from __future__ import annotations

import os
from uuid import UUID, uuid4

import pytest

from app.core.db import Database
from app.core.errors import AppError
from app.domains.catalog.models import ProductInput, VariantInput
from app.domains.catalog.repository import PostgresCatalogRepository
from app.domains.media.models import MediaVariant
from app.domains.media.repository import PostgresMediaRepository

TEST_DSN = os.getenv("GROWUP_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DSN,
    reason="GROWUP_TEST_DATABASE_URL no configurada",
)


async def _tenant(database: Database, slug: str) -> UUID:
    async with database.pool.acquire() as connection:
        return await connection.fetchval(
            "select app.create_tenant($1, $2, $3)",
            slug,
            f"{slug}.growup.com",
            "Catalog Media Test",
        )


async def _ready_asset(
    repository: PostgresMediaRepository,
    tenant_id: UUID,
    *,
    asset_id: UUID,
    alt: str,
) -> None:
    await repository.create_asset(
        tenant_id,
        asset_id=asset_id,
        r2_key=f"tenant/{tenant_id}/originals/{asset_id}.jpg",
        mime="image/jpeg",
        size_bytes=1000,
        original_filename="camisa.jpg",
    )
    await repository.set_alt(tenant_id, asset_id, alt)
    await repository.replace_variants(
        tenant_id,
        asset_id,
        (
            MediaVariant(
                format="webp",
                width=320,
                height=240,
                r2_key=f"tenant/{tenant_id}/variants/{asset_id}/320.webp",
                size_bytes=100,
            ),
        ),
    )
    await repository.mark_ready(
        tenant_id,
        asset_id,
        r2_key=f"tenant/{tenant_id}/originals/{asset_id}.jpg",
        mime="image/jpeg",
        size_bytes=900,
        width=800,
        height=600,
        blurhash="LDT9R{]9fQ]9",
    )


async def test_attach_detach_media_and_public_filtering() -> None:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=5)
    await database.connect()
    tenants: list[UUID] = []
    suffix = uuid4().hex[:8]

    try:
        tenant_id = await _tenant(database, f"it-cat-media-{suffix}")
        other_tenant_id = await _tenant(database, f"it-cat-media-{suffix}-b")
        tenants.extend([tenant_id, other_tenant_id])

        catalog = PostgresCatalogRepository(database)
        media = PostgresMediaRepository(database)
        product = await catalog.create_product(
            tenant_id,
            ProductInput(
                slug=f"camisa-{suffix}",
                name="Camisa",
                description=None,
                category_id=None,
                status="active",
                brand=None,
                tags=(),
                variants=(
                    VariantInput(
                        sku=f"CAM-{suffix}",
                        name="M",
                        price_cents=5000000,
                        stock=3,
                    ),
                ),
            ),
        )

        front_id = uuid4()
        back_id = uuid4()
        await _ready_asset(media, tenant_id, asset_id=front_id, alt="Frente")
        await _ready_asset(media, tenant_id, asset_id=back_id, alt="Espalda")

        attached = await catalog.attach_media(
            tenant_id,
            product.summary.id,
            front_id,
            position=None,
            is_primary=True,
        )
        assert attached is not None
        assert len(attached.media) == 1
        assert attached.media[0].media_asset_id == front_id
        assert attached.media[0].is_primary is True
        assert attached.media[0].alt == "Frente"
        assert attached.media[0].variants[0].format == "webp"
        assert attached.images == (attached.media[0].r2_key,)

        reordered = await catalog.attach_media(
            tenant_id,
            product.summary.id,
            back_id,
            position=1,
            is_primary=True,
        )
        assert reordered is not None
        assert [item.media_asset_id for item in reordered.media] == [back_id, front_id]
        assert [item.is_primary for item in reordered.media] == [True, False]

        reattached = await catalog.attach_media(
            tenant_id,
            product.summary.id,
            front_id,
            position=None,
            is_primary=None,
        )
        assert reattached is not None
        by_id = {item.media_asset_id: item for item in reattached.media}
        assert by_id[front_id].is_primary is False
        assert by_id[back_id].is_primary is True
        assert by_id[front_id].position == 0

        public = await catalog.get_product_by_slug(
            tenant_id,
            f"camisa-{suffix}",
            public_only=True,
        )
        assert public is not None
        assert len(public.media) == 2

        assert (
            await catalog.attach_media(
                other_tenant_id,
                product.summary.id,
                front_id,
                position=None,
                is_primary=False,
            )
            is None
        )

        assert await catalog.detach_media(tenant_id, product.summary.id, back_id) is True
        remaining = await catalog.get_product_by_id(tenant_id, product.summary.id)
        assert remaining is not None
        assert [item.media_asset_id for item in remaining.media] == [front_id]

        assert await catalog.detach_media(tenant_id, product.summary.id, back_id) is False
    finally:
        if tenants:
            async with database.pool.acquire() as connection:
                await connection.execute(
                    "delete from app.tenants where id = any($1::uuid[])",
                    tenants,
                )
        await database.close()


async def test_attach_media_requires_ready_asset_and_alt() -> None:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=5)
    await database.connect()
    tenants: list[UUID] = []
    suffix = uuid4().hex[:8]

    try:
        tenant_id = await _tenant(database, f"it-cat-media-rules-{suffix}")
        tenants.append(tenant_id)

        catalog = PostgresCatalogRepository(database)
        media = PostgresMediaRepository(database)
        product = await catalog.create_product(
            tenant_id,
            ProductInput(
                slug=f"camisa-reglas-{suffix}",
                name="Camisa",
                description=None,
                category_id=None,
                status="active",
                brand=None,
                tags=(),
                variants=(
                    VariantInput(
                        sku=f"CAM-R-{suffix}",
                        name="M",
                        price_cents=5000000,
                        stock=1,
                    ),
                ),
            ),
        )

        uploading_id = uuid4()
        await media.create_asset(
            tenant_id,
            asset_id=uploading_id,
            r2_key=f"tenant/{tenant_id}/originals/{uploading_id}.jpg",
            mime="image/jpeg",
            size_bytes=100,
            original_filename="uploading.jpg",
        )
        with pytest.raises(AppError) as not_ready:
            await catalog.attach_media(
                tenant_id,
                product.summary.id,
                uploading_id,
                position=None,
                is_primary=False,
            )
        assert not_ready.value.code == "MEDIA_NOT_READY"

        no_alt_id = uuid4()
        await media.create_asset(
            tenant_id,
            asset_id=no_alt_id,
            r2_key=f"tenant/{tenant_id}/originals/{no_alt_id}.jpg",
            mime="image/jpeg",
            size_bytes=100,
            original_filename="sin-alt.jpg",
        )
        await media.mark_ready(
            tenant_id,
            no_alt_id,
            r2_key=f"tenant/{tenant_id}/originals/{no_alt_id}.jpg",
            mime="image/jpeg",
            size_bytes=90,
            width=800,
            height=600,
            blurhash="LDT9R{]9fQ]9",
        )
        with pytest.raises(AppError) as missing_alt:
            await catalog.attach_media(
                tenant_id,
                product.summary.id,
                no_alt_id,
                position=None,
                is_primary=False,
            )
        assert missing_alt.value.code == "MEDIA_ALT_REQUIRED"

        missing_id = uuid4()
        with pytest.raises(AppError) as missing_media:
            await catalog.attach_media(
                tenant_id,
                product.summary.id,
                missing_id,
                position=None,
                is_primary=False,
            )
        assert missing_media.value.code == "MEDIA_NOT_FOUND"
    finally:
        if tenants:
            async with database.pool.acquire() as connection:
                await connection.execute(
                    "delete from app.tenants where id = any($1::uuid[])",
                    tenants,
                )
        await database.close()
