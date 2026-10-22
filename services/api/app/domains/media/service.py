from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import replace
from uuid import UUID, uuid4

from app.core.errors import AppError
from app.domains.media.imaging import (
    MAX_IMAGE_BYTES,
    ensure_allowed_mime,
    extension_for_mime,
    process_image,
)
from app.domains.media.models import MediaAsset, MediaStatus, MediaVariant, UploadTicket
from app.domains.media.repository import MediaRepository
from app.domains.media.storage import MediaStorage

EnqueueMedia = Callable[[UUID, UUID], Awaitable[None]]

_VALID_STATUSES = {status.value for status in MediaStatus}


class MediaService:
    """Orquesta subida directa a R2 y procesamiento en worker.

    `tenant_id` proviene siempre del contexto autenticado, nunca del body.
    """

    def __init__(
        self,
        repository: MediaRepository,
        storage: MediaStorage,
        *,
        enqueue: EnqueueMedia | None = None,
        upload_ttl_seconds: int = 900,
        max_image_bytes: int = MAX_IMAGE_BYTES,
    ) -> None:
        self._repository = repository
        self._storage = storage
        self._enqueue = enqueue
        self._upload_ttl_seconds = upload_ttl_seconds
        self._max_image_bytes = max_image_bytes

    async def create_upload(
        self,
        tenant_id: UUID,
        *,
        filename: str,
        content_type: str,
        size_bytes: int,
    ) -> UploadTicket:
        mime = ensure_allowed_mime(content_type)
        if size_bytes <= 0:
            raise AppError("MEDIA_EMPTY", "El archivo está vacío", 400)
        if size_bytes > self._max_image_bytes:
            raise AppError("MEDIA_TOO_LARGE", "La imagen supera 10 MB", 413)

        clean_name = _clean_filename(filename)
        asset_id = uuid4()
        extension = extension_for_mime(mime)
        r2_key = f"tenant/{tenant_id}/originals/{asset_id}.{extension}"

        await self._repository.create_asset(
            tenant_id,
            asset_id=asset_id,
            r2_key=r2_key,
            mime=mime,
            size_bytes=size_bytes,
            original_filename=clean_name,
        )

        try:
            upload_url = self._storage.presigned_put(
                r2_key,
                content_type=mime,
                expires_in=self._upload_ttl_seconds,
            )
        except Exception:
            await self._repository.mark_failed(tenant_id, asset_id)
            raise

        return UploadTicket(
            asset_id=asset_id,
            upload_url=upload_url,
            r2_key=r2_key,
            expires_in=self._upload_ttl_seconds,
        )

    async def complete_upload(
        self,
        tenant_id: UUID,
        asset_id: UUID,
        *,
        alt: str,
    ) -> MediaAsset:
        clean_alt = _clean_alt(alt)

        asset = await self._repository.get_asset(tenant_id, asset_id)
        if asset is None:
            raise AppError("MEDIA_NOT_FOUND", "El media asset no existe", 404)
        if asset.status is MediaStatus.READY:
            return asset
        if asset.status is MediaStatus.FAILED:
            raise AppError(
                "MEDIA_PROCESSING_FAILED",
                "El procesamiento falló; sube la imagen de nuevo",
                409,
            )
        if self._enqueue is None:
            raise AppError(
                "MEDIA_QUEUE_UNAVAILABLE",
                "La cola de procesamiento no está configurada",
                503,
            )

        await self._repository.set_alt(tenant_id, asset_id, clean_alt)
        try:
            await self._enqueue(tenant_id, asset_id)
        except AppError:
            raise
        except Exception as exc:
            raise AppError(
                "MEDIA_QUEUE_UNAVAILABLE",
                "No se pudo encolar el procesamiento",
                503,
            ) from exc

        return replace(asset, alt=clean_alt)

    async def list_assets(
        self,
        tenant_id: UUID,
        *,
        status: str | None,
        limit: int,
    ) -> tuple[MediaAsset, ...]:
        if limit < 1 or limit > 100:
            raise AppError("INVALID_LIMIT", "El límite debe estar entre 1 y 100", 422)
        if status is not None and status not in _VALID_STATUSES:
            raise AppError("INVALID_STATUS", "Estado de media inválido", 422)
        return await self._repository.list_assets(
            tenant_id,
            status=status,
            limit=limit,
        )

    async def get_asset(self, tenant_id: UUID, asset_id: UUID) -> MediaAsset:
        asset = await self._repository.get_asset(tenant_id, asset_id)
        if asset is None:
            raise AppError("MEDIA_NOT_FOUND", "El media asset no existe", 404)
        return asset

    async def get_asset_detail(
        self,
        tenant_id: UUID,
        asset_id: UUID,
    ) -> tuple[MediaAsset, tuple[MediaVariant, ...]]:
        asset = await self.get_asset(tenant_id, asset_id)
        variants = await self._repository.list_variants(tenant_id, asset_id)
        return asset, variants

    async def update_alt(
        self,
        tenant_id: UUID,
        asset_id: UUID,
        *,
        alt: str,
    ) -> MediaAsset:
        clean_alt = _clean_alt(alt)
        asset = await self.get_asset(tenant_id, asset_id)
        await self._repository.set_alt(tenant_id, asset_id, clean_alt)
        return replace(asset, alt=clean_alt)

    async def delete_asset(self, tenant_id: UUID, asset_id: UUID) -> None:
        asset = await self.get_asset(tenant_id, asset_id)
        variants = await self._repository.list_variants(tenant_id, asset_id)
        keys = [asset.r2_key, *(variant.r2_key for variant in variants)]

        failed = False
        for key in keys:
            try:
                await self._storage.delete(key)
            except Exception:
                failed = True

        if failed:
            raise AppError(
                "MEDIA_DELETE_FAILED",
                "No se pudieron borrar todos los archivos",
                502,
            )

        await self._repository.delete_asset(tenant_id, asset_id)

    async def process_asset(self, tenant_id: UUID, asset_id: UUID) -> None:
        asset = await self._repository.get_asset(tenant_id, asset_id)
        if asset is None:
            raise AppError("MEDIA_NOT_FOUND", "El media asset no existe", 404)

        try:
            data = await self._storage.download(
                asset.r2_key,
                max_bytes=self._max_image_bytes,
            )
            processed = await asyncio.to_thread(process_image, data, asset.mime)
        except AppError as exc:
            if exc.code.startswith("MEDIA_"):
                await self._repository.mark_failed(tenant_id, asset_id)
            raise

        # Sobrescribe el original con la versión sin EXIF.
        await self._storage.upload(
            asset.r2_key,
            processed.data,
            content_type=processed.mime,
        )

        variants: list[MediaVariant] = []
        for variant in processed.variants:
            key = (
                f"tenant/{tenant_id}/variants/{asset_id}/"
                f"{variant.width}-{variant.checksum}.{variant.format}"
            )
            await self._storage.upload(
                key,
                variant.data,
                content_type=f"image/{variant.format}",
            )
            variants.append(
                MediaVariant(
                    format=variant.format,
                    width=variant.width,
                    height=variant.height,
                    r2_key=key,
                    size_bytes=len(variant.data),
                )
            )

        await self._repository.replace_variants(tenant_id, asset_id, variants)
        await self._repository.mark_ready(
            tenant_id,
            asset_id,
            r2_key=asset.r2_key,
            mime=processed.mime,
            size_bytes=len(processed.data),
            width=processed.width,
            height=processed.height,
            blurhash=processed.blurhash,
        )


def _clean_alt(alt: str) -> str:
    clean = alt.strip()
    if not clean:
        raise AppError("MEDIA_ALT_REQUIRED", "El alt text es obligatorio", 422)
    if len(clean) > 300:
        raise AppError("MEDIA_ALT_TOO_LONG", "El alt text supera 300 caracteres", 422)
    return clean


def _clean_filename(filename: str) -> str:
    name = filename.replace("\\", "/").rsplit("/", 1)[-1].strip()
    if not name:
        return "archivo"
    return name[:255]
