from __future__ import annotations

import os
from io import BytesIO
from uuid import UUID, uuid4

import pytest
from PIL import Image

from app.core.db import Database
from app.domains.media.models import MediaStatus, MediaVariant
from app.domains.media.repository import PostgresMediaRepository
from app.domains.media.service import MediaService

TEST_DSN = os.getenv("GROWUP_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DSN,
    reason="GROWUP_TEST_DATABASE_URL no configurada",
)


class FakeStorage:
    def __init__(self, objects: dict[str, bytes] | None = None) -> None:
        self.objects = objects or {}
        self.uploaded: list[dict[str, object]] = []

    def presigned_put(
        self,
        key: str,
        *,
        content_type: str,
        expires_in: int = 900,
    ) -> str:
        return f"https://r2.example/{key}?sig=1"

    async def download(self, key: str, *, max_bytes: int) -> bytes:
        return self.objects[key]

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
                "size": len(data),
            }
        )

    def public_url(self, key: str) -> str:
        return f"https://cdn.example/{key}"

    async def delete(self, key: str) -> None:
        self.objects.pop(key, None)


def _jpeg(size: tuple[int, int] = (800, 600)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", size, "red").save(buffer, format="JPEG")
    return buffer.getvalue()


async def _tenant(database: Database, suffix: str) -> UUID:
    async with database.pool.acquire() as connection:
        return await connection.fetchval(
            "select app.create_tenant($1, $2, $3)",
            f"it-media-{suffix}",
            f"it-media-{suffix}.growup.com",
            "Media Test",
        )


async def test_media_admin_lifecycle_list_update_and_delete() -> None:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=5)
    await database.connect()
    tenants: list[UUID] = []
    suffix = uuid4().hex[:8]

    try:
        tenant_id = await _tenant(database, suffix)
        tenants.append(tenant_id)
        repository = PostgresMediaRepository(database)
        asset_id = await repository.create_asset(
            tenant_id,
            r2_key=f"tenant/{tenant_id}/originals/{uuid4()}.jpg",
            mime="image/jpeg",
            size_bytes=100,
            original_filename="camisa.jpg",
        )
        asset = await repository.get_asset(tenant_id, asset_id)
        assert asset is not None
        variant_key = f"tenant/{tenant_id}/variants/{asset_id}/320.webp"
        await repository.set_alt(tenant_id, asset_id, "Camisa")
        await repository.replace_variants(
            tenant_id,
            asset_id,
            (
                MediaVariant(
                    format="webp",
                    width=320,
                    height=240,
                    r2_key=variant_key,
                    size_bytes=100,
                ),
            ),
        )
        await repository.mark_ready(
            tenant_id,
            asset_id,
            r2_key=asset.r2_key,
            mime="image/jpeg",
            size_bytes=90,
            width=800,
            height=600,
            blurhash="LDT9R{]9fQ]9",
        )
        storage = FakeStorage({asset.r2_key: b"original", variant_key: b"variant"})
        service = MediaService(repository, storage)

        assets = await service.list_assets(tenant_id, status="ready", limit=10)
        assert [item.id for item in assets] == [asset_id]

        updated = await service.update_alt(tenant_id, asset_id, alt="Camisa roja")
        assert updated.alt == "Camisa roja"

        detail_asset, variants = await service.get_asset_detail(tenant_id, asset_id)
        assert detail_asset.id == asset_id
        assert [variant.format for variant in variants] == ["webp"]

        await service.delete_asset(tenant_id, asset_id)

        assert await repository.get_asset(tenant_id, asset_id) is None
        assert storage.objects == {}
    finally:
        if tenants:
            async with database.pool.acquire() as connection:
                await connection.execute(
                    "delete from app.tenants where id = any($1::uuid[])",
                    tenants,
                )
        await database.close()


async def test_media_repository_lifecycle_and_rls() -> None:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=5)
    await database.connect()
    tenants: list[UUID] = []
    suffix = uuid4().hex[:8]

    try:
        tenant_id = await _tenant(database, suffix)
        other_tenant_id = await _tenant(database, f"{suffix}-b")
        tenants.extend([tenant_id, other_tenant_id])
        repository = PostgresMediaRepository(database)
        asset_id = await repository.create_asset(
            tenant_id,
            r2_key=f"tenant/{tenant_id}/originals/{uuid4()}.jpg",
            mime="image/jpeg",
            size_bytes=1234,
            original_filename="camisa.jpg",
        )

        asset = await repository.get_asset(tenant_id, asset_id)
        assert asset is not None
        assert asset.status is MediaStatus.UPLOADING
        assert asset.original_filename == "camisa.jpg"
        assert await repository.get_asset(other_tenant_id, asset_id) is None

        await repository.set_alt(tenant_id, asset_id, "Camisa roja")
        updated = await repository.get_asset(tenant_id, asset_id)
        assert updated is not None
        assert updated.alt == "Camisa roja"

        variants = (
            MediaVariant(
                format="webp",
                width=320,
                height=240,
                r2_key=f"tenant/{tenant_id}/variants/{asset_id}/320.webp",
                size_bytes=100,
            ),
            MediaVariant(
                format="avif",
                width=640,
                height=480,
                r2_key=f"tenant/{tenant_id}/variants/{asset_id}/640.avif",
                size_bytes=200,
            ),
        )
        await repository.replace_variants(tenant_id, asset_id, variants)
        await repository.mark_ready(
            tenant_id,
            asset_id,
            r2_key=f"tenant/{tenant_id}/originals/{asset_id}.jpg",
            mime="image/jpeg",
            size_bytes=1000,
            width=800,
            height=600,
            blurhash="LDT9R{]9fQ]9",
        )

        ready = await repository.get_asset(tenant_id, asset_id)
        assert ready is not None
        assert ready.status is MediaStatus.READY
        assert (ready.width, ready.height) == (800, 600)
        assert ready.blurhash == "LDT9R{]9fQ]9"

        async with database.pool.acquire() as connection:
            count = await connection.fetchval(
                "select count(*)::int from app.media_variants "
                "where tenant_id = $1 and media_asset_id = $2",
                tenant_id,
                asset_id,
            )
        assert count == 2
    finally:
        if tenants:
            async with database.pool.acquire() as connection:
                await connection.execute(
                    "delete from app.tenants where id = any($1::uuid[])",
                    tenants,
                )
        await database.close()


async def test_create_upload_uses_asset_id_in_key() -> None:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=5)
    await database.connect()
    tenants: list[UUID] = []
    suffix = uuid4().hex[:8]

    try:
        tenant_id = await _tenant(database, suffix)
        tenants.append(tenant_id)
        repository = PostgresMediaRepository(database)
        service = MediaService(repository, FakeStorage())

        ticket = await service.create_upload(
            tenant_id,
            filename="camisa.jpg",
            content_type="image/jpeg",
            size_bytes=100,
        )

        asset = await repository.get_asset(tenant_id, ticket.asset_id)
        assert asset is not None
        assert asset.r2_key == ticket.r2_key
        assert ticket.r2_key == f"tenant/{tenant_id}/originals/{ticket.asset_id}.jpg"
        assert asset.original_filename == "camisa.jpg"
    finally:
        if tenants:
            async with database.pool.acquire() as connection:
                await connection.execute(
                    "delete from app.tenants where id = any($1::uuid[])",
                    tenants,
                )
        await database.close()


async def test_media_service_processes_image_into_ready_asset() -> None:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=5)
    await database.connect()
    tenants: list[UUID] = []
    suffix = uuid4().hex[:8]

    try:
        tenant_id = await _tenant(database, suffix)
        tenants.append(tenant_id)
        repository = PostgresMediaRepository(database)
        asset_id = await repository.create_asset(
            tenant_id,
            r2_key=f"tenant/{tenant_id}/originals/{uuid4()}.jpg",
            mime="image/jpeg",
            size_bytes=100,
            original_filename="camisa.jpg",
        )
        asset = await repository.get_asset(tenant_id, asset_id)
        assert asset is not None
        storage = FakeStorage({asset.r2_key: _jpeg()})
        service = MediaService(repository, storage)

        await service.process_asset(tenant_id, asset_id)

        processed = await repository.get_asset(tenant_id, asset_id)
        assert processed is not None
        assert processed.status is MediaStatus.READY
        assert (processed.width, processed.height) == (800, 600)
        assert processed.blurhash

        async with database.pool.acquire() as connection:
            rows = await connection.fetch(
                "select format, width, r2_key from app.media_variants "
                "where tenant_id = $1 and media_asset_id = $2 "
                "order by format, width",
                tenant_id,
                asset_id,
            )
        assert len(rows) == 4
        assert {row["format"] for row in rows} == {"avif", "webp"}
        assert {row["width"] for row in rows} == {320, 640}
        assert all(row["r2_key"] in storage.objects for row in rows)
    finally:
        if tenants:
            async with database.pool.acquire() as connection:
                await connection.execute(
                    "delete from app.tenants where id = any($1::uuid[])",
                    tenants,
                )
        await database.close()
