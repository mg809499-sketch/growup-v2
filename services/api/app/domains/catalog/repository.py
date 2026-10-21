from __future__ import annotations

import json
from typing import Any, Protocol, cast
from uuid import UUID

import asyncpg  # type: ignore[import-untyped]

from app.core.db import Database
from app.core.errors import AppError
from app.domains.catalog.models import (
    Category,
    CategoryInput,
    ProductDetail,
    ProductInput,
    ProductPage,
    ProductPatch,
    ProductStatus,
    ProductSummary,
    ProductVariant,
)
from app.domains.catalog.pagination import decode_cursor, encode_cursor


class CatalogRepository(Protocol):
    async def list_categories(self, tenant_id: UUID) -> tuple[Category, ...]: ...

    async def create_category(self, tenant_id: UUID, data: CategoryInput) -> Category: ...

    async def list_products(
        self,
        tenant_id: UUID,
        *,
        status: str | None,
        category: str | None,
        query: str | None,
        limit: int,
        cursor: str | None,
    ) -> ProductPage: ...

    async def get_product_by_slug(
        self,
        tenant_id: UUID,
        slug: str,
        *,
        public_only: bool,
    ) -> ProductDetail | None: ...

    async def get_product_by_id(
        self,
        tenant_id: UUID,
        product_id: UUID,
    ) -> ProductDetail | None: ...

    async def create_product(self, tenant_id: UUID, data: ProductInput) -> ProductDetail: ...

    async def update_product(
        self,
        tenant_id: UUID,
        product_id: UUID,
        patch: ProductPatch,
    ) -> ProductDetail | None: ...


class PostgresCatalogRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    async def list_categories(self, tenant_id: UUID) -> tuple[Category, ...]:
        async with self._database.tenant_transaction(tenant_id) as connection:
            rows = await connection.fetch(
                """
                select id, slug, name, description, position
                from app.categories
                where tenant_id = $1
                order by position, name
                """,
                tenant_id,
            )
        return tuple(_category(row) for row in rows)

    async def create_category(self, tenant_id: UUID, data: CategoryInput) -> Category:
        try:
            async with self._database.tenant_transaction(tenant_id) as connection:
                row = await connection.fetchrow(
                    """
                    insert into app.categories
                        (tenant_id, slug, name, description, position)
                    values ($1, $2, $3, $4, $5)
                    returning id, slug, name, description, position
                    """,
                    tenant_id,
                    data.slug,
                    data.name,
                    data.description,
                    data.position,
                )
        except asyncpg.UniqueViolationError as exc:
            raise AppError("SLUG_TAKEN", "La categoría ya existe", 409) from exc

        if row is None:
            raise AppError("CATEGORY_CREATE_FAILED", "No se pudo crear la categoría", 500)
        return _category(row)

    async def list_products(
        self,
        tenant_id: UUID,
        *,
        status: str | None,
        category: str | None,
        query: str | None,
        limit: int,
        cursor: str | None,
    ) -> ProductPage:
        cursor_created_at = None
        cursor_id = None
        if cursor:
            cursor_created_at, cursor_id = decode_cursor(cursor)

        async with self._database.tenant_transaction(tenant_id) as connection:
            rows = await connection.fetch(
                """
                select p.id, p.slug, p.name, p.status, p.category_id,
                       p.min_price_cents, p.max_price_cents, p.created_at
                from app.products p
                left join app.categories c
                  on c.tenant_id = p.tenant_id and c.id = p.category_id
                where p.tenant_id = $1
                  and ($2::text is null or p.status = $2)
                  and ($3::text is null or c.slug = $3)
                  and ($4::text is null or p.search_vector @@ websearch_to_tsquery('spanish', $4))
                  and (
                      $5::timestamptz is null
                      or (p.created_at, p.id) < ($5::timestamptz, $6::uuid)
                  )
                order by p.created_at desc, p.id desc
                limit $7::int
                """,
                tenant_id,
                status,
                category,
                query,
                cursor_created_at,
                cursor_id,
                limit + 1,
            )

        has_more = len(rows) > limit
        page_rows = rows[:limit]
        next_cursor = None
        if has_more and page_rows:
            last = page_rows[-1]
            next_cursor = encode_cursor(last["created_at"], last["id"])

        return ProductPage(
            items=tuple(_summary(row) for row in page_rows),
            next_cursor=next_cursor,
        )

    async def get_product_by_slug(
        self,
        tenant_id: UUID,
        slug: str,
        *,
        public_only: bool,
    ) -> ProductDetail | None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            row = await connection.fetchrow(
                """
                select id
                from app.products
                where tenant_id = $1
                  and slug = $2
                  and ($3::boolean is false or status = 'active')
                """,
                tenant_id,
                slug,
                public_only,
            )
            if row is None:
                return None
            return await self._fetch_detail(
                connection,
                tenant_id,
                row["id"],
                public_only=public_only,
            )

    async def get_product_by_id(
        self,
        tenant_id: UUID,
        product_id: UUID,
    ) -> ProductDetail | None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            return await self._fetch_detail(
                connection,
                tenant_id,
                product_id,
                public_only=False,
            )

    async def create_product(self, tenant_id: UUID, data: ProductInput) -> ProductDetail:
        try:
            async with self._database.tenant_transaction(tenant_id) as connection:
                product_row = await connection.fetchrow(
                    """
                    insert into app.products
                        (tenant_id, category_id, slug, name, description,
                         status, brand, tags, published_at)
                    values (
                        $1, $2, $3, $4, $5, $6, $7, $8,
                        case when $6 = 'active' then now() else null end
                    )
                    returning id
                    """,
                    tenant_id,
                    data.category_id,
                    data.slug,
                    data.name,
                    data.description,
                    data.status,
                    data.brand,
                    list(data.tags),
                )
                if product_row is None:
                    raise AppError("PRODUCT_CREATE_FAILED", "No se pudo crear el producto", 500)

                product_id = product_row["id"]
                location_id = await self._default_location(connection, tenant_id)

                for position, variant in enumerate(data.variants):
                    variant_id = await connection.fetchval(
                        """
                        insert into app.product_variants
                            (tenant_id, product_id, sku, name, price_cents,
                             compare_at_price_cents, cost_cents, weight_grams,
                             option_values, position, is_active)
                        values (
                            $1, $2, $3, $4, $5, $6, $7, $8,
                            $9::jsonb, $10, $11
                        )
                        returning id
                        """,
                        tenant_id,
                        product_id,
                        variant.sku,
                        variant.name,
                        variant.price_cents,
                        variant.compare_at_price_cents,
                        variant.cost_cents,
                        variant.weight_grams,
                        json.dumps(variant.option_values),
                        position,
                        variant.is_active,
                    )
                    await connection.execute(
                        """
                        insert into app.inventory_levels
                            (tenant_id, variant_id, location_id, available)
                        values ($1, $2, $3, $4)
                        """,
                        tenant_id,
                        variant_id,
                        location_id,
                        variant.stock,
                    )
                    if variant.stock > 0:
                        await connection.execute(
                            """
                            insert into app.inventory_movements
                                (tenant_id, variant_id, delta, reason,
                                 reference_type, reference_id)
                            values ($1, $2, $3, 'restock', 'product_creation', $4)
                            """,
                            tenant_id,
                            variant_id,
                            variant.stock,
                            product_id,
                        )

                detail = await self._fetch_detail(
                    connection,
                    tenant_id,
                    product_id,
                    public_only=False,
                )
                if detail is None:
                    raise AppError("PRODUCT_CREATE_FAILED", "No se pudo leer el producto", 500)
                return detail
        except asyncpg.UniqueViolationError as exc:
            constraint = getattr(exc, "constraint_name", "") or ""
            if "sku" in constraint:
                raise AppError("SKU_TAKEN", "El SKU ya existe", 409) from exc
            raise AppError("SLUG_TAKEN", "El slug del producto ya existe", 409) from exc
        except asyncpg.ForeignKeyViolationError as exc:
            raise AppError(
                "CATEGORY_NOT_FOUND",
                "La categoría no existe en este tenant",
                400,
            ) from exc

    async def update_product(
        self,
        tenant_id: UUID,
        product_id: UUID,
        patch: ProductPatch,
    ) -> ProductDetail | None:
        try:
            async with self._database.tenant_transaction(tenant_id) as connection:
                if patch.status == ProductStatus.ACTIVE.value:
                    active_count = await connection.fetchval(
                        """
                        select count(*)
                        from app.product_variants
                        where tenant_id = $1 and product_id = $2 and is_active
                        """,
                        tenant_id,
                        product_id,
                    )
                    if not active_count:
                        raise AppError(
                            "PRODUCT_WITHOUT_ACTIVE_VARIANTS",
                            "El producto no tiene variantes activas",
                            422,
                        )

                updates: list[str] = []
                values: list[object] = []
                parameter = 3

                if patch.name is not None:
                    updates.append(f"name = ${parameter}")
                    values.append(patch.name)
                    parameter += 1
                if patch.description is not None:
                    updates.append(f"description = ${parameter}")
                    values.append(patch.description)
                    parameter += 1
                if patch.category_id is not None:
                    updates.append(f"category_id = ${parameter}")
                    values.append(patch.category_id)
                    parameter += 1
                if patch.brand is not None:
                    updates.append(f"brand = ${parameter}")
                    values.append(patch.brand)
                    parameter += 1
                if patch.tags is not None:
                    updates.append(f"tags = ${parameter}")
                    values.append(list(patch.tags))
                    parameter += 1
                if patch.status is not None:
                    updates.append(f"status = ${parameter}")
                    values.append(patch.status)
                    parameter += 1
                    if patch.status == ProductStatus.ACTIVE.value:
                        updates.append("published_at = coalesce(published_at, now())")

                if not updates:
                    return await self._fetch_detail(
                        connection,
                        tenant_id,
                        product_id,
                        public_only=False,
                    )

                query = (
                    f"update app.products set {', '.join(updates)} "
                    "where tenant_id = $1 and id = $2 returning id"
                )
                row = await connection.fetchrow(query, tenant_id, product_id, *values)
                if row is None:
                    return None
                return await self._fetch_detail(
                    connection,
                    tenant_id,
                    product_id,
                    public_only=False,
                )
        except asyncpg.ForeignKeyViolationError as exc:
            raise AppError(
                "CATEGORY_NOT_FOUND",
                "La categoría no existe en este tenant",
                400,
            ) from exc

    async def _default_location(self, connection: asyncpg.Connection, tenant_id: UUID) -> UUID:
        location_id = await connection.fetchval(
            "select id from app.locations where tenant_id = $1 and is_default limit 1",
            tenant_id,
        )
        if location_id is None:
            location_id = await connection.fetchval(
                """
                insert into app.locations (tenant_id, name, is_default)
                values ($1, 'Principal', true)
                returning id
                """,
                tenant_id,
            )
        return cast(UUID, location_id)

    async def _fetch_detail(
        self,
        connection: asyncpg.Connection,
        tenant_id: UUID,
        product_id: UUID,
        *,
        public_only: bool,
    ) -> ProductDetail | None:
        row = await connection.fetchrow(
            """
            select id, slug, name, description, status, category_id, brand, tags,
                   min_price_cents, max_price_cents, created_at
            from app.products
            where tenant_id = $1
              and id = $2
              and ($3::boolean is false or status = 'active')
            """,
            tenant_id,
            product_id,
            public_only,
        )
        if row is None:
            return None

        variant_rows = await connection.fetch(
            """
            select v.id, v.sku, v.name, v.price_cents, v.compare_at_price_cents,
                   v.option_values, v.is_active,
                   greatest(coalesce(sum(l.available - l.reserved), 0), 0)::int
                       as stock_available
            from app.product_variants v
            left join app.inventory_levels l
              on l.tenant_id = v.tenant_id and l.variant_id = v.id
            where v.tenant_id = $1
              and v.product_id = $2
              and ($3::boolean is false or v.is_active)
            group by v.id
            order by v.position, v.name
            """,
            tenant_id,
            product_id,
            public_only,
        )

        return ProductDetail(
            summary=_summary(row),
            description=row["description"],
            brand=row["brand"],
            tags=tuple(row["tags"] or ()),
            variants=tuple(_variant(variant) for variant in variant_rows),
        )


def _category(row: Any) -> Category:
    return Category(
        id=row["id"],
        slug=row["slug"],
        name=row["name"],
        description=row["description"],
        position=row["position"],
    )


def _summary(row: Any) -> ProductSummary:
    return ProductSummary(
        id=row["id"],
        slug=row["slug"],
        name=row["name"],
        status=ProductStatus(row["status"]),
        category_id=row["category_id"],
        min_price_cents=row["min_price_cents"],
        max_price_cents=row["max_price_cents"],
        created_at=row["created_at"],
    )


def _variant(row: Any) -> ProductVariant:
    return ProductVariant(
        id=row["id"],
        sku=row["sku"],
        name=row["name"],
        price_cents=row["price_cents"],
        compare_at_price_cents=row["compare_at_price_cents"],
        option_values=_as_dict(row["option_values"]),
        is_active=row["is_active"],
        stock_available=row["stock_available"],
    )


def _as_dict(value: object) -> dict[str, str]:
    if isinstance(value, dict):
        return {str(key): str(item) for key, item in value.items()}
    if isinstance(value, str):
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return {str(key): str(item) for key, item in parsed.items()}
    return {}
