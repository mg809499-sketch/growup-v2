from __future__ import annotations

from collections.abc import Sequence
from io import BytesIO
from uuid import UUID, uuid4

import pytest
from PIL import Image

from app.core.errors import AppError
from app.domains.media.models import MediaAsset, MediaStatus, MediaVariant
from app.domains.media.service import MediaService


class FakeMediaRepository:
    def __init__(self) -> None:
        self.assets: dict[UUID, MediaAsset] = {}
        self.variants: dict[UUID, list[MediaVariant]] = {}
        self.failed: list[UUID] = []
        self.created: list[dict[str, object]] = []

    async def create_asset(
        self,
        tenant_id: UUID,
        *,
        asset_id: UUID | None = None,
        r2_key: str,
        mime: str,
        size_bytes: int,
        original_filename: str | None,
    ) -> UUID:
        asset_id = asset_id or uuid4()
        self.assets[asset_id] = MediaAsset(
            id=asset_id,
            tenant_id=tenant_id,
            r2_key=r2_key,
            mime=mime,
            size_bytes=size_bytes,
            original_filename=original_filename,
            width=None,
            height=None,
            alt=None,
            blurhash=None,
            status=MediaStatus.UPLOADING,
        )
        self.created.append(
            {
                "tenant_id": tenant_id,
                "r2_key": r2_key,
                "mime": mime,
                "size_bytes": size_bytes,
                "original_filename": original_filename,
            }
        )
        return asset_id

    async def get_asset(self, tenant_id: UUID, asset_id: UUID) -> MediaAsset | None:
        asset = self.assets.get(asset_id)
        return asset if asset is not None and asset.tenant_id == tenant_id else None

    async def set_alt(self, tenant_id: UUID, asset_id: UUID, alt: str) -> None:
        self.assets[asset_id] = _replace(self.assets[asset_id], alt=alt)

    async def mark_ready(
        self,
        tenant_id: UUID,
        asset_id: UUID,
        *,
        r2_key: str,
        mime: str,
        size_bytes: int,
        width: int,
        height: int,
        blurhash: str,
    ) -> None:
        self.assets[asset_id] = _replace(
            self.assets[asset_id],
            r2_key=r2_key,
            mime=mime,
            size_bytes=size_bytes,
            width=width,
            height=height,
            blurhash=blurhash,
            status=MediaStatus.READY,
        )

    async def replace_variants(
        self,
        tenant_id: UUID,
        asset_id: UUID,
        variants: Sequence[MediaVariant],
    ) -> None:
        self.variants[asset_id] = list(variants)

    async def mark_failed(self, tenant_id: UUID, asset_id: UUID) -> None:
        self.failed.append(asset_id)
        self.assets[asset_id] = _replace(
            self.assets[asset_id],
            status=MediaStatus.FAILED,
        )


class FakeStorage:
    def __init__(self, objects: dict[str, bytes] | None = None) -> None:
        self.objects = objects or {}
        self.presigned: list[dict[str, object]] = []
        self.uploaded: list[dict[str, object]] = []
        self.fail_presign = False

    def presigned_put(
        self,
        key: str,
        *,
        content_type: str,
        expires_in: int = 900,
    ) -> str:
        if self.fail_presign:
            raise RuntimeError("r2 down")
        self.presigned.append(
            {
                "key": key,
                "content_type": content_type,
                "expires_in": expires_in,
            }
        )
        return f"https://r2.example/{key}?sig=1"

    async def download(self, key: str, *, max_bytes: int) -> bytes:
        data = self.objects[key]
        if len(data) > max_bytes:
            raise AppError("MEDIA_TOO_LARGE", "too large", 413)
        return data

    async def upload(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str,
        cache_control: str = "public, max-age=31536000, immutable",
    ) -> None:
        self.objects[key] = data
        self.uploaded.append(
            {
                "key": key,
                "content_type": content_type,
                "cache_control": cache_control,
                "size": len(data),
            }
        )

    def public_url(self, key: str) -> str:
        return f"https://cdn.example/{key}"


def _replace(asset: MediaAsset, **changes: object) -> MediaAsset:
    values = {
        "id": asset.id,
        "tenant_id": asset.tenant_id,
        "r2_key": asset.r2_key,
        "mime": asset.mime,
        "size_bytes": asset.size_bytes,
        "original_filename": asset.original_filename,
        "width": asset.width,
        "height": asset.height,
        "alt": asset.alt,
        "blurhash": asset.blurhash,
        "status": asset.status,
    }
    values.update(changes)
    return MediaAsset(**values)  # type: ignore[arg-type]


def _jpeg(size: tuple[int, int] = (800, 600)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", size, "red").save(buffer, format="JPEG")
    return buffer.getvalue()


async def test_create_upload_sanitizes_filename_and_prefixes_key() -> None:
    repository = FakeMediaRepository()
    storage = FakeStorage()
    service = MediaService(repository, storage, upload_ttl_seconds=600)
    tenant_id = uuid4()

    ticket = await service.create_upload(
        tenant_id,
        filename="../../fotos/camisa.jpg",
        content_type="image/jpeg",
        size_bytes=1024,
    )

    assert ticket.r2_key == f"tenant/{tenant_id}/originals/{ticket.asset_id}.jpg"
    assert ticket.expires_in == 600
    assert ticket.upload_url.startswith("https://r2.example/")
    assert repository.created[0]["original_filename"] == "camisa.jpg"
    assert storage.presigned[0]["content_type"] == "image/jpeg"


async def test_create_upload_rejects_bad_type_and_size() -> None:
    repository = FakeMediaRepository()
    storage = FakeStorage()
    service = MediaService(repository, storage, max_image_bytes=100)
    tenant_id = uuid4()

    with pytest.raises(AppError) as unsupported:
        await service.create_upload(
            tenant_id,
            filename="x.pdf",
            content_type="application/pdf",
            size_bytes=10,
        )
    assert unsupported.value.code == "MEDIA_UNSUPPORTED_TYPE"

    with pytest.raises(AppError) as empty:
        await service.create_upload(
            tenant_id,
            filename="x.jpg",
            content_type="image/jpeg",
            size_bytes=0,
        )
    assert empty.value.code == "MEDIA_EMPTY"

    with pytest.raises(AppError) as oversized:
        await service.create_upload(
            tenant_id,
            filename="x.jpg",
            content_type="image/jpeg",
            size_bytes=101,
        )
    assert oversized.value.code == "MEDIA_TOO_LARGE"


async def test_create_upload_marks_failed_if_presign_fails() -> None:
    repository = FakeMediaRepository()
    storage = FakeStorage()
    storage.fail_presign = True
    service = MediaService(repository, storage)

    with pytest.raises(RuntimeError):
        await service.create_upload(
            uuid4(),
            filename="x.jpg",
            content_type="image/jpeg",
            size_bytes=10,
        )

    assert len(repository.failed) == 1


async def test_complete_upload_sets_alt_and_enqueues() -> None:
    repository = FakeMediaRepository()
    storage = FakeStorage()
    tenant_id = uuid4()
    asset_id = await repository.create_asset(
        tenant_id,
        r2_key="tenant/t/originals/a.jpg",
        mime="image/jpeg",
        size_bytes=10,
        original_filename="a.jpg",
    )
    enqueued: list[tuple[UUID, UUID]] = []

    async def enqueue(tenant: UUID, asset: UUID) -> None:
        enqueued.append((tenant, asset))

    service = MediaService(repository, storage, enqueue=enqueue)

    asset = await service.complete_upload(tenant_id, asset_id, alt="  Camisa roja  ")

    assert asset.alt == "Camisa roja"
    assert enqueued == [(tenant_id, asset_id)]


async def test_complete_upload_is_idempotent_when_ready() -> None:
    repository = FakeMediaRepository()
    storage = FakeStorage()
    tenant_id = uuid4()
    asset_id = await repository.create_asset(
        tenant_id,
        r2_key="tenant/t/originals/a.jpg",
        mime="image/jpeg",
        size_bytes=10,
        original_filename="a.jpg",
    )
    repository.assets[asset_id] = _replace(
        repository.assets[asset_id],
        status=MediaStatus.READY,
        alt="Lista",
    )
    calls: list[tuple[UUID, UUID]] = []

    async def enqueue(tenant: UUID, asset: UUID) -> None:
        calls.append((tenant, asset))

    service = MediaService(repository, storage, enqueue=enqueue)

    asset = await service.complete_upload(tenant_id, asset_id, alt="Otra")

    assert asset.alt == "Lista"
    assert calls == []


async def test_complete_upload_rejects_failed_and_missing_queue() -> None:
    repository = FakeMediaRepository()
    storage = FakeStorage()
    tenant_id = uuid4()
    asset_id = await repository.create_asset(
        tenant_id,
        r2_key="tenant/t/originals/a.jpg",
        mime="image/jpeg",
        size_bytes=10,
        original_filename="a.jpg",
    )
    service = MediaService(repository, storage)

    with pytest.raises(AppError) as queue_missing:
        await service.complete_upload(tenant_id, asset_id, alt="Alt")
    assert queue_missing.value.code == "MEDIA_QUEUE_UNAVAILABLE"

    repository.assets[asset_id] = _replace(
        repository.assets[asset_id],
        status=MediaStatus.FAILED,
    )
    with pytest.raises(AppError) as failed:
        await service.complete_upload(tenant_id, asset_id, alt="Alt")
    assert failed.value.code == "MEDIA_PROCESSING_FAILED"


async def test_process_asset_sanitizes_original_and_saves_variants() -> None:
    repository = FakeMediaRepository()
    tenant_id = uuid4()
    asset_id = await repository.create_asset(
        tenant_id,
        r2_key="tenant/t/originals/a.jpg",
        mime="image/jpeg",
        size_bytes=10,
        original_filename="a.jpg",
    )
    storage = FakeStorage({repository.assets[asset_id].r2_key: _jpeg()})
    service = MediaService(repository, storage)

    await service.process_asset(tenant_id, asset_id)

    asset = await repository.get_asset(tenant_id, asset_id)
    assert asset is not None
    assert asset.status is MediaStatus.READY
    assert (asset.width, asset.height) == (800, 600)
    assert asset.blurhash
    assert len(repository.variants[asset_id]) == 4
    assert {variant.width for variant in repository.variants[asset_id]} == {320, 640}
    assert {variant.format for variant in repository.variants[asset_id]} == {"avif", "webp"}

    variant_keys = {variant.r2_key for variant in repository.variants[asset_id]}
    assert all(key.startswith(f"tenant/{tenant_id}/variants/{asset_id}/") for key in variant_keys)
    assert all(key in storage.objects for key in variant_keys)
    assert storage.uploaded[0]["content_type"] == "image/jpeg"


async def test_process_asset_marks_failed_on_invalid_image() -> None:
    repository = FakeMediaRepository()
    tenant_id = uuid4()
    asset_id = await repository.create_asset(
        tenant_id,
        r2_key="tenant/t/originals/a.jpg",
        mime="image/jpeg",
        size_bytes=10,
        original_filename="a.jpg",
    )
    storage = FakeStorage({repository.assets[asset_id].r2_key: b"not an image"})
    service = MediaService(repository, storage)

    with pytest.raises(AppError) as exc_info:
        await service.process_asset(tenant_id, asset_id)

    assert exc_info.value.code == "MEDIA_INVALID"
    assert repository.failed == [asset_id]


async def test_process_asset_missing_asset_is_404() -> None:
    service = MediaService(FakeMediaRepository(), FakeStorage())

    with pytest.raises(AppError) as exc_info:
        await service.process_asset(uuid4(), uuid4())

    assert exc_info.value.code == "MEDIA_NOT_FOUND"
