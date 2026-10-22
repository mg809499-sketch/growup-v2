from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import get_catalog_service, get_storefront_tenant, get_tenant_context
from app.core.errors import AppError
from app.domains.catalog.models import (
    CategoryInput,
    ProductInput,
    ProductPage,
    ProductPatch,
    VariantInput,
)
from app.domains.catalog.schemas import (
    CategoryCreate,
    CategoryResponse,
    MediaAttachRequest,
    ProductCreate,
    ProductDetailResponse,
    ProductListResponse,
    ProductSummaryResponse,
    ProductUpdate,
    VariantUpdate,
)
from app.domains.catalog.service import CatalogService
from app.domains.identity.models import Permission, RequestContext
from app.domains.identity.permissions import require_permission
from app.domains.tenants.models import Tenant

admin_router = APIRouter(prefix="/v1/admin", tags=["admin-catalog"])
storefront_router = APIRouter(prefix="/v1/storefront", tags=["storefront-catalog"])


def _tenant_id(context: RequestContext) -> UUID:
    if context.tenant_id is None:
        raise AppError("FORBIDDEN", "Se requiere un tenant", 403)
    return context.tenant_id


def _to_product_input(payload: ProductCreate) -> ProductInput:
    return ProductInput(
        slug=payload.slug,
        name=payload.name,
        description=payload.description,
        category_id=payload.category_id,
        status=payload.status,
        brand=payload.brand,
        tags=tuple(payload.tags),
        variants=tuple(
            VariantInput(
                sku=variant.sku,
                name=variant.name,
                price_cents=variant.price_cents,
                compare_at_price_cents=variant.compare_at_price_cents,
                cost_cents=variant.cost_cents,
                weight_grams=variant.weight_grams,
                stock=variant.stock,
                option_values=variant.option_values,
                is_active=variant.is_active,
            )
            for variant in payload.variants
        ),
    )


def _to_product_patch(payload: ProductUpdate) -> ProductPatch:
    return ProductPatch(
        name=payload.name,
        description=payload.description,
        category_id=payload.category_id,
        status=payload.status,
        brand=payload.brand,
        tags=tuple(payload.tags) if payload.tags is not None else None,
    )


def _to_list_response(page: ProductPage) -> ProductListResponse:
    return ProductListResponse(
        items=[ProductSummaryResponse.from_domain(item) for item in page.items],
        next_cursor=page.next_cursor,
    )


@admin_router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> list[CategoryResponse]:
    require_permission(context, Permission.CATALOG_READ)
    categories = await service.list_categories(_tenant_id(context))
    return [CategoryResponse.from_domain(category) for category in categories]


@admin_router.post("/categories", response_model=CategoryResponse, status_code=201)
async def create_category(
    payload: CategoryCreate,
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> CategoryResponse:
    require_permission(context, Permission.CATALOG_WRITE)
    category = await service.create_category(
        _tenant_id(context),
        CategoryInput(
            slug=payload.slug,
            name=payload.name,
            description=payload.description,
            position=payload.position,
        ),
    )
    return CategoryResponse.from_domain(category)


@admin_router.get("/products", response_model=ProductListResponse)
async def list_products_admin(
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[CatalogService, Depends(get_catalog_service)],
    status: Annotated[Literal["draft", "active", "archived"] | None, Query()] = None,
    category: Annotated[str | None, Query(max_length=63)] = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: Annotated[str | None, Query()] = None,
) -> ProductListResponse:
    require_permission(context, Permission.CATALOG_READ)
    page = await service.list_products(
        _tenant_id(context),
        status=status,
        category=category,
        query=q,
        limit=limit,
        cursor=cursor,
    )
    return _to_list_response(page)


@admin_router.post("/products", response_model=ProductDetailResponse, status_code=201)
async def create_product(
    payload: ProductCreate,
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> ProductDetailResponse:
    require_permission(context, Permission.CATALOG_WRITE)
    detail = await service.create_product(_tenant_id(context), _to_product_input(payload))
    return ProductDetailResponse.from_domain(detail)


@admin_router.get("/products/{product_id}", response_model=ProductDetailResponse)
async def get_product_admin(
    product_id: UUID,
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> ProductDetailResponse:
    require_permission(context, Permission.CATALOG_READ)
    detail = await service.get_product_by_id(_tenant_id(context), product_id)
    if detail is None:
        raise AppError("PRODUCT_NOT_FOUND", "Producto no encontrado", 404)
    return ProductDetailResponse.from_domain(detail)


@admin_router.patch("/products/{product_id}", response_model=ProductDetailResponse)
async def update_product(
    product_id: UUID,
    payload: ProductUpdate,
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> ProductDetailResponse:
    require_permission(context, Permission.CATALOG_WRITE)
    detail = await service.update_product(
        _tenant_id(context),
        product_id,
        _to_product_patch(payload),
    )
    if detail is None:
        raise AppError("PRODUCT_NOT_FOUND", "Producto no encontrado", 404)
    return ProductDetailResponse.from_domain(detail)


@admin_router.post(
    "/products/{product_id}/media",
    response_model=ProductDetailResponse,
    status_code=201,
)
async def attach_product_media(
    product_id: UUID,
    payload: MediaAttachRequest,
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> ProductDetailResponse:
    require_permission(context, Permission.CATALOG_WRITE)
    detail = await service.attach_media(
        _tenant_id(context),
        product_id,
        payload.media_asset_id,
        position=payload.position,
        is_primary=payload.is_primary,
    )
    if detail is None:
        raise AppError("PRODUCT_NOT_FOUND", "Producto no encontrado", 404)
    return ProductDetailResponse.from_domain(detail)


@admin_router.delete(
    "/products/{product_id}/media/{media_asset_id}",
    status_code=204,
)
async def detach_product_media(
    product_id: UUID,
    media_asset_id: UUID,
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> Response:
    require_permission(context, Permission.CATALOG_WRITE)
    removed = await service.detach_media(
        _tenant_id(context),
        product_id,
        media_asset_id,
    )
    if not removed:
        raise AppError(
            "PRODUCT_MEDIA_NOT_FOUND",
            "La imagen no está asociada al producto",
            404,
        )
    return Response(status_code=204)


@admin_router.patch(
    "/products/{product_id}/variants/{variant_id}",
    response_model=ProductDetailResponse,
)
async def update_product_variant(
    product_id: UUID,
    variant_id: UUID,
    payload: VariantUpdate,
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> ProductDetailResponse:
    require_permission(context, Permission.CATALOG_WRITE)
    detail = await service.update_variant(
        _tenant_id(context),
        product_id,
        variant_id,
        changes=payload.model_dump(exclude_unset=True),
    )
    if detail is None:
        raise AppError(
            "VARIANT_NOT_FOUND",
            "Producto o variante no encontrados",
            404,
        )
    return ProductDetailResponse.from_domain(detail)


@admin_router.delete(
    "/products/{product_id}/variants/{variant_id}",
    status_code=204,
)
async def delete_product_variant(
    product_id: UUID,
    variant_id: UUID,
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> Response:
    require_permission(context, Permission.CATALOG_WRITE)
    removed = await service.delete_variant(
        _tenant_id(context),
        product_id,
        variant_id,
    )
    if not removed:
        raise AppError(
            "VARIANT_NOT_FOUND",
            "Producto o variante no encontrados",
            404,
        )
    return Response(status_code=204)


@storefront_router.get("/products", response_model=ProductListResponse)
async def list_products_storefront(
    tenant: Annotated[Tenant, Depends(get_storefront_tenant)],
    service: Annotated[CatalogService, Depends(get_catalog_service)],
    category: Annotated[str | None, Query(max_length=63)] = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: Annotated[str | None, Query()] = None,
) -> ProductListResponse:
    page = await service.list_products(
        tenant.id,
        status="active",
        category=category,
        query=q,
        limit=limit,
        cursor=cursor,
    )
    return _to_list_response(page)


@storefront_router.get("/products/{slug}", response_model=ProductDetailResponse)
async def get_product_storefront(
    slug: str,
    tenant: Annotated[Tenant, Depends(get_storefront_tenant)],
    service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> ProductDetailResponse:
    detail = await service.get_product(tenant.id, slug, public_only=True)
    if detail is None:
        raise AppError("PRODUCT_NOT_FOUND", "Producto no encontrado", 404)
    return ProductDetailResponse.from_domain(detail)
