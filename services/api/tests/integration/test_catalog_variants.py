from __future__ import annotations

import os
from uuid import UUID, uuid4

import pytest

from app.core.db import Database
from app.core.errors import AppError
from app.domains.catalog.models import ProductInput, VariantInput
from app.domains.catalog.repository import PostgresCatalogRepository

TEST_DSN = os.getenv("GROWUP_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DSN,
    reason="GROWUP_TEST_DATABASE_URL no configurada",
)


async def test_add_variant_creates_inventory_and_rejects_duplicate_sku() -> None:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=5)
    await database.connect()
    tenants: list[UUID] = []
    suffix = uuid4().hex[:8]

    try:
        async with database.pool.acquire() as connection:
            tenant_id = await connection.fetchval(
                "select app.create_tenant($1, $2, $3)",
                f"it-add-variant-{suffix}",
                f"it-add-variant-{suffix}.growup.com",
                "Add Variant Test",
            )
        tenants.append(tenant_id)
        catalog = PostgresCatalogRepository(database)
        product = await catalog.create_product(
            tenant_id,
            ProductInput(
                slug=f"camisa-add-{suffix}",
                name="Camisa",
                description=None,
                category_id=None,
                status="active",
                brand=None,
                tags=(),
                variants=(
                    VariantInput(
                        sku=f"BASE-{suffix}",
                        name="M",
                        price_cents=5000000,
                        stock=2,
                    ),
                ),
            ),
        )

        detail = await catalog.add_variant(
            tenant_id,
            product.summary.id,
            VariantInput(
                sku=f"NEW-{suffix}",
                name="L",
                price_cents=6000000,
                compare_at_price_cents=7000000,
                stock=4,
                option_values={"Talla": "L"},
            ),
        )
        assert detail is not None
        assert len(detail.variants) == 2
        added = next(item for item in detail.variants if item.sku == f"NEW-{suffix}")
        assert added.price_cents == 6000000
        assert added.stock_available == 4

        async with database.pool.acquire() as connection:
            level = await connection.fetchrow(
                "select available from app.inventory_levels "
                "where tenant_id = $1 and variant_id = $2",
                tenant_id,
                added.id,
            )
            movement = await connection.fetchrow(
                "select reason, reference_type from app.inventory_movements "
                "where tenant_id = $1 and variant_id = $2 "
                "order by created_at desc limit 1",
                tenant_id,
                added.id,
            )
        assert level is not None
        assert level["available"] == 4
        assert movement is not None
        assert movement["reason"] == "restock"
        assert movement["reference_type"] == "variant_creation"

        with pytest.raises(AppError) as duplicate:
            await catalog.add_variant(
                tenant_id,
                product.summary.id,
                VariantInput(
                    sku=f"NEW-{suffix}",
                    name="L",
                    price_cents=6000000,
                    stock=1,
                ),
            )
        assert duplicate.value.code == "SKU_TAKEN"

        assert (
            await catalog.add_variant(
                tenant_id,
                uuid4(),
                VariantInput(
                    sku=f"ORPHAN-{suffix}",
                    name="Única",
                    price_cents=1000000,
                    stock=1,
                ),
            )
            is None
        )
    finally:
        if tenants:
            async with database.pool.acquire() as connection:
                await connection.execute(
                    "delete from app.tenants where id = any($1::uuid[])",
                    tenants,
                )
        await database.close()


async def test_variant_update_and_delete_rules() -> None:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=5)
    await database.connect()
    tenants: list[UUID] = []
    suffix = uuid4().hex[:8]

    try:
        async with database.pool.acquire() as connection:
            tenant_id = await connection.fetchval(
                "select app.create_tenant($1, $2, $3)",
                f"it-variants-{suffix}",
                f"it-variants-{suffix}.growup.com",
                "Variants Test",
            )
        tenants.append(tenant_id)
        catalog = PostgresCatalogRepository(database)
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
                        sku=f"M-{suffix}",
                        name="M",
                        price_cents=5000000,
                        stock=5,
                    ),
                    VariantInput(
                        sku=f"L-{suffix}",
                        name="L",
                        price_cents=6000000,
                        stock=3,
                    ),
                ),
            ),
        )
        variant_m = next(item for item in product.variants if item.sku == f"M-{suffix}")
        variant_l = next(item for item in product.variants if item.sku == f"L-{suffix}")

        updated = await catalog.update_variant(
            tenant_id,
            product.summary.id,
            variant_m.id,
            {"price_cents": 5500000},
        )
        assert updated is not None
        assert updated.summary.min_price_cents == 5500000
        assert updated.summary.max_price_cents == 6000000
        updated_m = next(item for item in updated.variants if item.id == variant_m.id)
        assert updated_m.price_cents == 5500000

        with pytest.raises(AppError) as invalid_compare:
            await catalog.update_variant(
                tenant_id,
                product.summary.id,
                variant_m.id,
                {"compare_at_price_cents": 1000},
            )
        assert invalid_compare.value.code == "INVALID_COMPARE_AT_PRICE"

        with_compare = await catalog.update_variant(
            tenant_id,
            product.summary.id,
            variant_m.id,
            {"compare_at_price_cents": 6000000},
        )
        assert with_compare is not None
        assert next(
            item for item in with_compare.variants if item.id == variant_m.id
        ).compare_at_price_cents == 6000000

        cleared = await catalog.update_variant(
            tenant_id,
            product.summary.id,
            variant_m.id,
            {"compare_at_price_cents": None},
        )
        assert cleared is not None
        assert next(
            item for item in cleared.variants if item.id == variant_m.id
        ).compare_at_price_cents is None

        deactivated = await catalog.update_variant(
            tenant_id,
            product.summary.id,
            variant_m.id,
            {"is_active": False},
        )
        assert deactivated is not None
        assert next(
            item for item in deactivated.variants if item.id == variant_m.id
        ).is_active is False

        with pytest.raises(AppError) as last_active:
            await catalog.update_variant(
                tenant_id,
                product.summary.id,
                variant_l.id,
                {"is_active": False},
            )
        assert last_active.value.code == "PRODUCT_WITHOUT_ACTIVE_VARIANTS"

        async with database.pool.acquire() as connection:
            location_id = await connection.fetchval(
                "select id from app.locations where tenant_id = $1 and is_default limit 1",
                tenant_id,
            )
            await connection.execute(
                """
                insert into app.inventory_reservations
                    (tenant_id, variant_id, location_id, quantity, expires_at)
                values ($1, $2, $3, 1, now() + interval '15 minutes')
                """,
                tenant_id,
                variant_m.id,
                location_id,
            )
        with pytest.raises(AppError) as reserved:
            await catalog.delete_variant(
                tenant_id,
                product.summary.id,
                variant_m.id,
            )
        assert reserved.value.code == "VARIANT_HAS_ACTIVE_RESERVATIONS"

        async with database.pool.acquire() as connection:
            await connection.execute(
                "update app.inventory_reservations set status = 'expired' "
                "where tenant_id = $1 and variant_id = $2",
                tenant_id,
                variant_m.id,
            )
        assert (
            await catalog.delete_variant(
                tenant_id,
                product.summary.id,
                variant_m.id,
            )
            is True
        )

        async with database.pool.acquire() as connection:
            inventory_count = await connection.fetchval(
                "select count(*)::int from app.inventory_levels "
                "where tenant_id = $1 and variant_id = $2",
                tenant_id,
                variant_m.id,
            )
        assert inventory_count == 0

        with pytest.raises(AppError) as last_variant:
            await catalog.delete_variant(
                tenant_id,
                product.summary.id,
                variant_l.id,
            )
        assert last_variant.value.code == "PRODUCT_WITHOUT_VARIANTS"

        assert (
            await catalog.delete_variant(
                tenant_id,
                product.summary.id,
                uuid4(),
            )
            is False
        )
    finally:
        if tenants:
            async with database.pool.acquire() as connection:
                await connection.execute(
                    "delete from app.tenants where id = any($1::uuid[])",
                    tenants,
                )
        await database.close()
