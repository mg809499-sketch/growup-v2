from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from app.core.errors import AppError
from app.domains.catalog.models import (
    VARIANT_PATCH_FIELDS,
    Category,
    CategoryInput,
    ProductDetail,
    ProductInput,
    ProductPage,
    ProductPatch,
    ProductStatus,
)
from app.domains.catalog.repository import CatalogRepository

_VALID_STATUSES = {status.value for status in ProductStatus}
_CREATABLE_STATUSES = {ProductStatus.DRAFT.value, ProductStatus.ACTIVE.value}


class CatalogService:
    def __init__(self, repository: CatalogRepository) -> None:
        self._repository = repository

    async def list_categories(self, tenant_id: UUID) -> tuple[Category, ...]:
        return await self._repository.list_categories(tenant_id)

    async def create_category(self, tenant_id: UUID, data: CategoryInput) -> Category:
        return await self._repository.create_category(tenant_id, data)

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
        if limit < 1 or limit > 50:
            raise AppError("INVALID_LIMIT", "El límite debe estar entre 1 y 50", 422)
        if status is not None and status not in _VALID_STATUSES:
            raise AppError("INVALID_STATUS", "Estado de producto inválido", 422)

        normalized_query = query.strip() if query else None
        if normalized_query is not None and len(normalized_query) > 100:
            raise AppError("QUERY_TOO_LONG", "La búsqueda es demasiado larga", 422)

        normalized_category = category.strip() if category else None

        return await self._repository.list_products(
            tenant_id,
            status=status,
            category=normalized_category,
            query=normalized_query,
            limit=limit,
            cursor=cursor,
        )

    async def get_product(
        self,
        tenant_id: UUID,
        slug: str,
        *,
        public_only: bool,
    ) -> ProductDetail | None:
        return await self._repository.get_product_by_slug(
            tenant_id,
            slug,
            public_only=public_only,
        )

    async def get_product_by_id(
        self,
        tenant_id: UUID,
        product_id: UUID,
    ) -> ProductDetail | None:
        return await self._repository.get_product_by_id(tenant_id, product_id)

    async def create_product(self, tenant_id: UUID, data: ProductInput) -> ProductDetail:
        self._validate_product(data)
        return await self._repository.create_product(tenant_id, data)

    async def update_product(
        self,
        tenant_id: UUID,
        product_id: UUID,
        patch: ProductPatch,
    ) -> ProductDetail | None:
        if patch.status is not None and patch.status not in _VALID_STATUSES:
            raise AppError("INVALID_STATUS", "Estado de producto inválido", 422)

        return await self._repository.update_product(tenant_id, product_id, patch)

    async def attach_media(
        self,
        tenant_id: UUID,
        product_id: UUID,
        media_asset_id: UUID,
        *,
        position: int | None,
        is_primary: bool | None,
    ) -> ProductDetail | None:
        if position is not None and position < 0:
            raise AppError(
                "INVALID_POSITION",
                "La posición no puede ser negativa",
                422,
            )
        return await self._repository.attach_media(
            tenant_id,
            product_id,
            media_asset_id,
            position=position,
            is_primary=is_primary,
        )

    async def detach_media(
        self,
        tenant_id: UUID,
        product_id: UUID,
        media_asset_id: UUID,
    ) -> bool:
        return await self._repository.detach_media(
            tenant_id,
            product_id,
            media_asset_id,
        )

    async def update_variant(
        self,
        tenant_id: UUID,
        product_id: UUID,
        variant_id: UUID,
        *,
        changes: Mapping[str, object],
    ) -> ProductDetail | None:
        _validate_variant_changes(changes)
        return await self._repository.update_variant(
            tenant_id,
            product_id,
            variant_id,
            changes,
        )

    async def delete_variant(
        self,
        tenant_id: UUID,
        product_id: UUID,
        variant_id: UUID,
    ) -> bool:
        return await self._repository.delete_variant(
            tenant_id,
            product_id,
            variant_id,
        )

    def _validate_product(self, data: ProductInput) -> None:
        if data.status not in _CREATABLE_STATUSES:
            raise AppError(
                "INVALID_STATUS",
                "Un producto nuevo solo puede ser draft o active",
                422,
            )

        if not data.variants:
            raise AppError(
                "PRODUCT_WITHOUT_VARIANTS",
                "El producto debe tener al menos una variante",
                422,
            )

        skus = [variant.sku for variant in data.variants]
        if len(set(skus)) != len(skus):
            raise AppError("DUPLICATE_SKU", "Hay SKUs duplicados", 422)

        for variant in data.variants:
            if variant.price_cents <= 0:
                raise AppError("INVALID_PRICE", "El precio debe ser mayor que cero", 422)
            if (
                variant.compare_at_price_cents is not None
                and variant.compare_at_price_cents < variant.price_cents
            ):
                raise AppError(
                    "INVALID_COMPARE_AT_PRICE",
                    "El precio anterior no puede ser menor que el precio actual",
                    422,
                )

        if data.status == ProductStatus.ACTIVE.value and not any(
            variant.is_active for variant in data.variants
        ):
            raise AppError(
                "PRODUCT_WITHOUT_ACTIVE_VARIANTS",
                "Un producto activo necesita al menos una variante activa",
                422,
            )


def _validate_variant_changes(changes: Mapping[str, object]) -> None:
    unknown = {key for key in changes if key not in VARIANT_PATCH_FIELDS}
    if unknown:
        raise AppError("INVALID_VARIANT_FIELD", "Campo de variante inválido", 422)

    if "name" in changes:
        name = changes["name"]
        if not isinstance(name, str) or not name.strip():
            raise AppError("INVALID_NAME", "El nombre no puede estar vacío", 422)

    if "price_cents" in changes:
        price = changes["price_cents"]
        if isinstance(price, bool) or not isinstance(price, int) or price <= 0:
            raise AppError("INVALID_PRICE", "El precio debe ser mayor que cero", 422)

    for field in ("compare_at_price_cents", "cost_cents", "weight_grams"):
        if field not in changes:
            continue
        value = changes[field]
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            raise AppError(
                "INVALID_VARIANT_FIELD",
                f"El campo {field} debe ser un entero no negativo o null",
                422,
            )

    if "position" in changes:
        position = changes["position"]
        if isinstance(position, bool) or not isinstance(position, int) or position < 0:
            raise AppError("INVALID_POSITION", "La posición no puede ser negativa", 422)

    if "is_active" in changes and not isinstance(changes["is_active"], bool):
        raise AppError("INVALID_VARIANT_FIELD", "is_active debe ser booleano", 422)

    if "option_values" in changes and not isinstance(changes["option_values"], dict):
        raise AppError(
            "INVALID_VARIANT_FIELD",
            "option_values debe ser un objeto",
            422,
        )
