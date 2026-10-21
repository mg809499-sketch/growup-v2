from __future__ import annotations

import os
from uuid import UUID, uuid4

import pytest

from app.core.db import Database
from app.domains.catalog.models import (
    CategoryInput,
    ProductInput,
    ProductPatch,
    ProductStatus,
    VariantInput,
)
from app.domains.catalog.repository import PostgresCatalogRepository

TEST_DSN = os.getenv("GROWUP_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DSN,
    reason="GROWUP_TEST_DATABASE_URL no configurada",
)


async def test_catalog_repository_lifecycle() -> None:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=2)
    await database.connect()
    created_tenants: list[UUID] = []
    suffix = uuid4().hex[:8]
    tenant_slug = f"it-catalog-{suffix}"
    category_slug = f"ropa-{suffix}"
    product_slug = f"camiseta-{suffix}"

    try:
        async with database.pool.acquire() as connection:
            tenant_id = await connection.fetchval(
                "select app.create_tenant($1, $2, $3)",
                tenant_slug,
                f"{tenant_slug}.growup.com",
                "Catalog Test",
            )
            created_tenants.append(tenant_id)

        repository = PostgresCatalogRepository(database)

        category = await repository.create_category(
            tenant_id,
            CategoryInput(slug=category_slug, name="Ropa"),
        )
        assert category.slug == category_slug

        detail = await repository.create_product(
            tenant_id,
            ProductInput(
                slug=product_slug,
                name="Camiseta de prueba",
                description="Camiseta de algodón",
                category_id=category.id,
                status="active",
                brand="Growup",
                tags=("nuevo",),
                variants=(
                    VariantInput(
                        sku=f"CAM-M-{suffix}",
                        name="M",
                        price_cents=8900000,
                        stock=10,
                        option_values={"Talla": "M"},
                    ),
                    VariantInput(
                        sku=f"CAM-L-{suffix}",
                        name="L",
                        price_cents=9900000,
                        stock=5,
                        option_values={"Talla": "L"},
                    ),
                ),
            ),
        )

        assert detail.summary.slug == product_slug
        assert detail.summary.status == ProductStatus.ACTIVE
        assert detail.summary.min_price_cents == 8900000
        assert detail.summary.max_price_cents == 9900000
        assert len(detail.variants) == 2
        assert detail.variants[0].stock_available == 10
        assert detail.variants[0].option_values == {"Talla": "M"}

        page = await repository.list_products(
            tenant_id,
            status="active",
            category=category_slug,
            query="camiseta",
            limit=10,
            cursor=None,
        )
        assert len(page.items) == 1
        assert page.items[0].slug == product_slug
        assert page.next_cursor is None

        fetched = await repository.get_product_by_slug(
            tenant_id,
            product_slug,
            public_only=True,
        )
        assert fetched is not None
        assert fetched.summary.id == detail.summary.id

        updated = await repository.update_product(
            tenant_id,
            detail.summary.id,
            ProductPatch(status="draft"),
        )
        assert updated is not None
        assert updated.summary.status == ProductStatus.DRAFT

        hidden = await repository.get_product_by_slug(
            tenant_id,
            product_slug,
            public_only=True,
        )
        assert hidden is None
    finally:
        if created_tenants:
            async with database.pool.acquire() as connection:
                await connection.execute(
                    "delete from app.tenants where id = any($1::uuid[])",
                    created_tenants,
                )
        await database.close()
