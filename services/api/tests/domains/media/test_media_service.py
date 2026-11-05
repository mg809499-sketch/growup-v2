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

    async def list_assets(
        self,
        tenant_id: UUID,
        *,
        status: str | None,
        limit: int,
        offset: int,
    ) -> tuple[tuple[MediaAsset, ...], int]:
        assets = [
            asset
            for asset in self.assets.values()
            if asset.tenant_id == tenant_id
            and (status is None or asset.status.value == status)
        ]
        return tuple(assets[offset : offset + limit]), len(assets)

    async def list_variants(
        self,
        tenant_id: UUID,
        asset_id: UUID,
    ) -> tuple[MediaVariant, ...]:
        return tuple(self.variants.get(asset_id, ()))

    async def delete_asset(self, tenant_id: UUID, asset_id: UUID) -> bool:
        asset = self.assets.get(asset_id)
        if asset is None or asset.tenant_id != tenant_id:
            return False
        del self.assets[asset_id]
        self.variants.pop(asset_id, None)
        return True

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
        self.deleted: list[str] = []
        self.fail_presign = False
        self.fail_delete = False

    def presigned_put(
        self,
        key: str,
        *,
        content_type: str,
        content_length: int,
        expires_in: int = 900,
    ) -> str:
        if self.fail_presign:
            raise RuntimeError("r2 down")
        self.presigned.append(
            {
                "key": key,
                "content_type": content_type,
                "content_length": content_length,
                "expires_in": expires_in,
            }
        )
        return f"https://r2.example/{key}?sig=1"

    async def head_size(self, key: str) -> int:
        if key not in self.objects:
            raise AppError("MEDIA_UPLOAD_MISSING", "missing", 404)
        return len(self.objects[key])

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

    async def delete(self, key: str) -> None:
        if self.fail_delete:
            raise RuntimeError("r2 down")
        self.deleted.append(key)
        self.objects.pop(key, None)


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
    assert storage.presigned[0]["content_length"] == 1024


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
    storage.objects["tenant/t/originals/a.jpg"] = b"x" * 10
    enqueued: list[tuple[UUID, UUID]] = []

    async def enqueue(tenant: UUID, asset: UUID) -> None:
        enqueued.append((tenant, asset))

    service = MediaService(repository, storage, enqueue=enqueue)

    asset = await service.complete_upload(tenant_id, asset_id, alt="  Camisa roja  ")

    assert asset.alt == "Camisa roja"
    assert enqueued == [(tenant_id, asset_id)]


async def test_complete_upload_rejects_mismatched_object_size() -> None:
    repository = FakeMediaRepository()
    storage = FakeStorage({"tenant/t/originals/a.jpg": b"x" * 11})
    tenant_id = uuid4()
    asset_id = await repository.create_asset(
        tenant_id,
        r2_key="tenant/t/originals/a.jpg",
        mime="image/jpeg",
        size_bytes=10,
        original_filename="a.jpg",
    )

    async def enqueue(_tenant: UUID, _asset: UUID) -> None:
        return None

    service = MediaService(repository, storage, enqueue=enqueue)
    with pytest.raises(AppError) as exc_info:
        await service.complete_upload(tenant_id, asset_id, alt="Alt")

    assert exc_info.value.code == "MEDIA_SIZE_MISMATCH"
    assert repository.assets[asset_id].status is MediaStatus.FAILED


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


async def test_list_assets_validates_limit_and_status() -> None:
    service = MediaService(FakeMediaRepository(), FakeStorage())

    with pytest.raises(AppError) as limit_error:
        await service.list_assets(uuid4(), status=None, limit=0, offset=0)
    assert limit_error.value.code == "INVALID_LIMIT"

    with pytest.raises(AppError) as status_error:
        await service.list_assets(uuid4(), status="bogus", limit=10, offset=0)
    assert status_error.value.code == "INVALID_STATUS"

    with pytest.raises(AppError) as offset_error:
        await service.list_assets(uuid4(), status=None, limit=10, offset=-1)
    assert offset_error.value.code == "INVALID_OFFSET"


async def test_update_alt_sets_alt() -> None:
    repository = FakeMediaRepository()
    tenant_id = uuid4()
    asset_id = await repository.create_asset(
        tenant_id,
        r2_key="tenant/t/originals/a.jpg",
        mime="image/jpeg",
        size_bytes=10,
        original_filename="a.jpg",
    )
    service = MediaService(repository, FakeStorage())

    updated = await service.update_alt(tenant_id, asset_id, alt="  Camisa roja  ")

    assert updated.alt == "Camisa roja"
    stored = await repository.get_asset(tenant_id, asset_id)
    assert stored is not None
    assert stored.alt == "Camisa roja"


async def test_update_alt_requires_alt_text() -> None:
    repository = FakeMediaRepository()
    tenant_id = uuid4()
    asset_id = await repository.create_asset(
        tenant_id,
        r2_key="tenant/t/originals/a.jpg",
        mime="image/jpeg",
        size_bytes=10,
        original_filename="a.jpg",
    )
    service = MediaService(repository, FakeStorage())

    with pytest.raises(AppError) as exc_info:
        await service.update_alt(tenant_id, asset_id, alt="   ")

    assert exc_info.value.code == "MEDIA_ALT_REQUIRED"


async def test_delete_asset_removes_objects_and_row() -> None:
    repository = FakeMediaRepository()
    tenant_id = uuid4()
    asset_id = await repository.create_asset(
        tenant_id,
        r2_key="tenant/t/originals/a.jpg",
        mime="image/jpeg",
        size_bytes=10,
        original_filename="a.jpg",
    )
    repository.variants[asset_id] = [
        MediaVariant(
            format="webp",
            width=320,
            height=240,
            r2_key="tenant/t/variants/a/320.webp",
            size_bytes=100,
        )
    ]
    storage = FakeStorage()
    service = MediaService(repository, storage)

    await service.delete_asset(tenant_id, asset_id)

    assert storage.deleted == [
        "tenant/t/originals/a.jpg",
        "tenant/t/variants/a/320.webp",
    ]
    assert asset_id not in repository.assets


async def test_delete_asset_missing_is_404() -> None:
    service = MediaService(FakeMediaRepository(), FakeStorage())

    with pytest.raises(AppError) as exc_info:
        await service.delete_asset(uuid4(), uuid4())

    assert exc_info.value.code == "MEDIA_NOT_FOUND"


async def test_delete_asset_keeps_row_when_storage_fails() -> None:
    repository = FakeMediaRepository()
    tenant_id = uuid4()
    asset_id = await repository.create_asset(
        tenant_id,
        r2_key="tenant/t/originals/a.jpg",
        mime="image/jpeg",
        size_bytes=10,
        original_filename="a.jpg",
    )
    storage = FakeStorage()
    storage.fail_delete = True
    service = MediaService(repository, storage)

    with pytest.raises(AppError) as exc_info:
        await service.delete_asset(tenant_id, asset_id)

    assert exc_info.value.code == "MEDIA_DELETE_FAILED"
    assert asset_id in repository.assets
