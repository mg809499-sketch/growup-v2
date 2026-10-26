from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Protocol, cast
from uuid import UUID

import asyncpg  # type: ignore[import-untyped]

from app.core.db import Database
from app.core.errors import AppError
from app.domains.catalog.models import (
    VARIANT_PATCH_FIELDS,
    Category,
    CategoryInput,
    ProductDetail,
    ProductInput,
    ProductMedia,
    ProductMediaVariant,
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

    async def attach_media(
        self,
        tenant_id: UUID,
        product_id: UUID,
        media_asset_id: UUID,
        *,
        position: int | None,
        is_primary: bool | None,
    ) -> ProductDetail | None: ...

    async def detach_media(
        self,
        tenant_id: UUID,
        product_id: UUID,
        media_asset_id: UUID,
    ) -> bool: ...

    async def update_variant(
        self,
        tenant_id: UUID,
        product_id: UUID,
        variant_id: UUID,
        changes: Mapping[str, object],
    ) -> ProductDetail | None: ...

    async def delete_variant(
        self,
        tenant_id: UUID,
        product_id: UUID,
        variant_id: UUID,
    ) -> bool: ...


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
                       p.min_price_cents, p.max_price_cents, p.created_at,
                       img.r2_key as primary_image_key
                from app.products p
                left join app.categories c
                  on c.tenant_id = p.tenant_id and c.id = p.category_id
                left join lateral (
                    select ma.r2_key
                    from app.product_media pm
                    join app.media_assets ma
                      on ma.tenant_id = pm.tenant_id
                     and ma.id = pm.media_asset_id
                    where pm.tenant_id = p.tenant_id
                      and pm.product_id = p.id
                      and ma.status = 'ready'
                      and ma.alt is not null
                      and btrim(ma.alt) <> ''
                    order by pm.is_primary desc, pm.position, pm.created_at
                    limit 1
                ) img on true
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

    async def attach_media(
        self,
        tenant_id: UUID,
        product_id: UUID,
        media_asset_id: UUID,
        *,
        position: int | None,
        is_primary: bool | None,
    ) -> ProductDetail | None:
        try:
            async with self._database.tenant_transaction(tenant_id) as connection:
                product_row = await connection.fetchrow(
                    """
                    select id
                    from app.products
                    where tenant_id = $1 and id = $2
                    for update
                    """,
                    tenant_id,
                    product_id,
                )
                if product_row is None:
                    return None

                asset_row = await connection.fetchrow(
                    """
                    select status, alt
                    from app.media_assets
                    where tenant_id = $1 and id = $2
                    """,
                    tenant_id,
                    media_asset_id,
                )
                if asset_row is None:
                    raise AppError(
                        "MEDIA_NOT_FOUND",
                        "La imagen no existe en este tenant",
                        404,
                    )
                if asset_row["status"] != "ready":
                    raise AppError(
                        "MEDIA_NOT_READY",
                        "La imagen todavía no está procesada",
                        409,
                    )
                alt = asset_row["alt"]
                if not isinstance(alt, str) or not alt.strip():
                    raise AppError(
                        "MEDIA_ALT_REQUIRED",
                        "La imagen necesita alt text antes de asociarse",
                        422,
                    )

                existing = await connection.fetchrow(
                    """
                    select position, is_primary
                    from app.product_media
                    where tenant_id = $1
                      and product_id = $2
                      and media_asset_id = $3
                    """,
                    tenant_id,
                    product_id,
                    media_asset_id,
                )

                if position is None:
                    if existing is not None:
                        position = existing["position"]
                    else:
                        position = await connection.fetchval(
                            """
                            select coalesce(max(position) + 1, 0)::int
                            from app.product_media
                            where tenant_id = $1 and product_id = $2
                            """,
                            tenant_id,
                            product_id,
                        )

                effective_primary = (
                    is_primary
                    if is_primary is not None
                    else (existing["is_primary"] if existing is not None else False)
                )

                if effective_primary:
                    await connection.execute(
                        """
                        update app.product_media
                        set is_primary = false
                        where tenant_id = $1
                          and product_id = $2
                          and is_primary
                          and media_asset_id <> $3
                        """,
                        tenant_id,
                        product_id,
                        media_asset_id,
                    )

                await connection.execute(
                    """
                    insert into app.product_media
                        (tenant_id, product_id, media_asset_id, position, is_primary)
                    values ($1, $2, $3, $4, $5)
                    on conflict (tenant_id, product_id, media_asset_id)
                    do update set
                        position = excluded.position,
                        is_primary = excluded.is_primary
                    """,
                    tenant_id,
                    product_id,
                    media_asset_id,
                    position,
                    effective_primary,
                )

                return await self._fetch_detail(
                    connection,
                    tenant_id,
                    product_id,
                    public_only=False,
                )
        except asyncpg.UniqueViolationError as exc:
            raise AppError(
                "MEDIA_PRIMARY_CONFLICT",
                "No se pudo fijar la imagen principal; reintenta",
                409,
            ) from exc

    async def detach_media(
        self,
        tenant_id: UUID,
        product_id: UUID,
        media_asset_id: UUID,
    ) -> bool:
        async with self._database.tenant_transaction(tenant_id) as connection:
            deleted = await connection.fetchval(
                """
                delete from app.product_media
                where tenant_id = $1
                  and product_id = $2
                  and media_asset_id = $3
                returning 1
                """,
                tenant_id,
                product_id,
                media_asset_id,
            )
        return deleted is not None

    async def update_variant(
        self,
        tenant_id: UUID,
        product_id: UUID,
        variant_id: UUID,
        changes: Mapping[str, object],
    ) -> ProductDetail | None:
        unknown = {key for key in changes if key not in VARIANT_PATCH_FIELDS}
        if unknown:
            raise AppError(
                "INVALID_VARIANT_FIELD",
                "Campo de variante inválido",
                422,
            )

        async with self._database.tenant_transaction(tenant_id) as connection:
            product_row = await connection.fetchrow(
                """
                select id, status
                from app.products
                where tenant_id = $1 and id = $2
                for update
                """,
                tenant_id,
                product_id,
            )
            if product_row is None:
                return None

            variant_row = await connection.fetchrow(
                """
                select id, price_cents, compare_at_price_cents, is_active
                from app.product_variants
                where tenant_id = $1 and product_id = $2 and id = $3
                """,
                tenant_id,
                product_id,
                variant_id,
            )
            if variant_row is None:
                return None

            price = cast(int, changes.get("price_cents", variant_row["price_cents"]))
            compare_at = cast(
                int | None,
                changes.get(
                    "compare_at_price_cents",
                    variant_row["compare_at_price_cents"],
                ),
            )
            if compare_at is not None and compare_at < price:
                raise AppError(
                    "INVALID_COMPARE_AT_PRICE",
                    "El precio anterior no puede ser menor que el precio actual",
                    422,
                )

            if changes.get("is_active") is False and product_row["status"] == "active":
                other_active = await connection.fetchval(
                    """
                    select count(*)
                    from app.product_variants
                    where tenant_id = $1
                      and product_id = $2
                      and id <> $3
                      and is_active
                    """,
                    tenant_id,
                    product_id,
                    variant_id,
                )
                if not other_active:
                    raise AppError(
                        "PRODUCT_WITHOUT_ACTIVE_VARIANTS",
                        "El producto activo necesita al menos una variante activa",
                        422,
                    )

            updates: list[str] = []
            values: list[object] = []
            parameter = 4
            for field in VARIANT_PATCH_FIELDS:
                if field not in changes:
                    continue
                if field == "option_values":
                    updates.append(f"option_values = ${parameter}::jsonb")
                    values.append(json.dumps(changes[field]))
                else:
                    updates.append(f"{field} = ${parameter}")
                    values.append(changes[field])
                parameter += 1

            if updates:
                await connection.execute(
                    f"update app.product_variants set {', '.join(updates)} "
                    "where tenant_id = $1 and product_id = $2 and id = $3",
                    tenant_id,
                    product_id,
                    variant_id,
                    *values,
                )

            return await self._fetch_detail(
                connection,
                tenant_id,
                product_id,
                public_only=False,
            )

    async def delete_variant(
        self,
        tenant_id: UUID,
        product_id: UUID,
        variant_id: UUID,
    ) -> bool:
        async with self._database.tenant_transaction(tenant_id) as connection:
            product_row = await connection.fetchrow(
                """
                select id, status
                from app.products
                where tenant_id = $1 and id = $2
                for update
                """,
                tenant_id,
                product_id,
            )
            if product_row is None:
                return False

            variant_row = await connection.fetchrow(
                """
                select id, is_active
                from app.product_variants
                where tenant_id = $1 and product_id = $2 and id = $3
                """,
                tenant_id,
                product_id,
                variant_id,
            )
            if variant_row is None:
                return False

            variant_count = await connection.fetchval(
                """
                select count(*)
                from app.product_variants
                where tenant_id = $1 and product_id = $2
                """,
                tenant_id,
                product_id,
            )
            if variant_count <= 1:
                raise AppError(
                    "PRODUCT_WITHOUT_VARIANTS",
                    "El producto debe conservar al menos una variante",
                    422,
                )

            if variant_row["is_active"] and product_row["status"] == "active":
                active_count = await connection.fetchval(
                    """
                    select count(*)
                    from app.product_variants
                    where tenant_id = $1 and product_id = $2 and is_active
                    """,
                    tenant_id,
                    product_id,
                )
                if active_count <= 1:
                    raise AppError(
                        "PRODUCT_WITHOUT_ACTIVE_VARIANTS",
                        "El producto activo necesita al menos una variante activa",
                        422,
                    )

            active_reservations = await connection.fetchval(
                """
                select count(*)
                from app.inventory_reservations
                where tenant_id = $1
                  and variant_id = $2
                  and status = 'active'
                  and expires_at > now()
                """,
                tenant_id,
                variant_id,
            )
            if active_reservations:
                raise AppError(
                    "VARIANT_HAS_ACTIVE_RESERVATIONS",
                    "La variante tiene reservas activas; espera a que expiren",
                    409,
                )

            await connection.execute(
                "delete from app.product_variants where tenant_id = $1 and id = $2",
                tenant_id,
                variant_id,
            )
            return True

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
                   min_price_cents, max_price_cents, created_at,
                   img.r2_key as primary_image_key
            from app.products
            left join lateral (
                select ma.r2_key
                from app.product_media pm
                join app.media_assets ma
                  on ma.tenant_id = pm.tenant_id
                 and ma.id = pm.media_asset_id
                where pm.tenant_id = app.products.tenant_id
                  and pm.product_id = app.products.id
                  and ma.status = 'ready'
                  and ma.alt is not null
                  and btrim(ma.alt) <> ''
                order by pm.is_primary desc, pm.position, pm.created_at
                limit 1
            ) img on true
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

        media_rows = await connection.fetch(
            """
            select pm.media_asset_id, pm.position, pm.is_primary,
                   ma.r2_key, ma.alt, ma.blurhash, ma.width, ma.height, ma.status
            from app.product_media pm
            join app.media_assets ma
              on ma.tenant_id = pm.tenant_id and ma.id = pm.media_asset_id
            where pm.tenant_id = $1
              and pm.product_id = $2
              and (
                  $3::boolean is false
                  or (
                      ma.status = 'ready'
                      and ma.alt is not null
                      and btrim(ma.alt) <> ''
                  )
              )
            order by pm.is_primary desc, pm.position, pm.created_at, pm.media_asset_id
            """,
            tenant_id,
            product_id,
            public_only,
        )

        media_ids = [row["media_asset_id"] for row in media_rows]
        media_variant_rows: list[Any] = []
        if media_ids:
            media_variant_rows = await connection.fetch(
                """
                select media_asset_id, format, width, height, r2_key
                from app.media_variants
                where tenant_id = $1
                  and media_asset_id = any($2::uuid[])
                order by media_asset_id, width, format
                """,
                tenant_id,
                media_ids,
            )

        variants_by_media: dict[UUID, list[ProductMediaVariant]] = {}
        for variant_row in media_variant_rows:
            variants_by_media.setdefault(variant_row["media_asset_id"], []).append(
                _media_variant(variant_row)
            )

        media = tuple(
            _media(row, tuple(variants_by_media.get(row["media_asset_id"], ())))
            for row in media_rows
        )

        return ProductDetail(
            summary=_summary(row),
            description=row["description"],
            brand=row["brand"],
            tags=tuple(row["tags"] or ()),
            variants=tuple(_variant(variant) for variant in variant_rows),
            media=media,
            images=tuple(item.r2_key for item in media),
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
        primary_image_key=row.get("primary_image_key"),
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


def _media(row: Any, variants: tuple[ProductMediaVariant, ...]) -> ProductMedia:
    return ProductMedia(
        media_asset_id=row["media_asset_id"],
        r2_key=row["r2_key"],
        alt=row["alt"],
        blurhash=row["blurhash"],
        width=row["width"],
        height=row["height"],
        position=row["position"],
        is_primary=row["is_primary"],
        status=row["status"],
        variants=variants,
    )


def _media_variant(row: Any) -> ProductMediaVariant:
    return ProductMediaVariant(
        format=row["format"],
        width=row["width"],
        height=row["height"],
        r2_key=row["r2_key"],
    )


def _as_dict(value: object) -> dict[str, str]:
    if isinstance(value, dict):
        return {str(key): str(item) for key, item in value.items()}
    if isinstance(value, str):
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return {str(key): str(item) for key, item in parsed.items()}
    return {}
