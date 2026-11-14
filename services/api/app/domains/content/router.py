from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app import runtime
from app.api.deps import get_storefront_tenant, get_tenant_context, require_tenant_id
from app.core.errors import AppError
from app.domains.content.schemas import (
    PageCreateRequest,
    PageDetail,
    PageDraftRequest,
    PageListResponse,
    PageSummary,
    PageUpdateRequest,
    PublishRequest,
    StorefrontPageResponse,
    ThemeResponse,
    ThemeUpsertRequest,
    page_detail,
    page_summary,
    version_response,
)
from app.domains.content.service import PageService
from app.domains.identity.models import Permission, RequestContext
from app.domains.identity.permissions import require_permission
from app.domains.tenants.models import Tenant

admin_router = APIRouter(prefix="/v1/admin", tags=["admin-content"])
storefront_router = APIRouter(prefix="/v1/storefront", tags=["storefront-content"])


def get_page_service() -> PageService:
    if runtime.page_service is None:
        raise AppError(
            "SERVICE_UNAVAILABLE",
            "El servicio de contenido no está configurado",
            503,
        )
    return runtime.page_service


@admin_router.get("/pages", response_model=PageListResponse)
async def list_pages(
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[PageService, Depends(get_page_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PageListResponse:
    require_permission(context, Permission.CONTENT_READ)
    tenant_id = require_tenant_id(context)
    pages, total = await service.list_pages(tenant_id, limit=limit, offset=offset)
    return PageListResponse(
        items=[page_summary(page) for page in pages],
        total=total,
        limit=limit,
        offset=offset,
    )


@admin_router.post("/pages", response_model=PageSummary, status_code=201)
async def create_page(
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[PageService, Depends(get_page_service)],
    body: PageCreateRequest,
) -> PageSummary:
    require_permission(context, Permission.CONTENT_WRITE)
    tenant_id = require_tenant_id(context)
    page = await service.create_page(tenant_id, slug=body.slug, title=body.title)
    return page_summary(page)


@admin_router.get("/pages/{page_id}", response_model=PageDetail)
async def get_page(
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[PageService, Depends(get_page_service)],
    page_id: UUID,
) -> PageDetail:
    require_permission(context, Permission.CONTENT_READ)
    tenant_id = require_tenant_id(context)
    page = await service.get_page(tenant_id, page_id)
    latest = await service.latest_version(tenant_id, page_id)
    return page_detail(page, latest.version if latest else None)


@admin_router.get("/pages/{page_id}/draft")
async def get_draft(
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[PageService, Depends(get_page_service)],
    page_id: UUID,
) -> dict[str, object]:
    """Última versión del layout (base de edición), o null si no hay borradores."""
    require_permission(context, Permission.CONTENT_READ)
    tenant_id = require_tenant_id(context)
    await service.get_page(tenant_id, page_id)
    latest = await service.latest_version(tenant_id, page_id)
    if latest is None:
        return {"version": None, "layout": None, "id": None}
    return version_response(latest)


@admin_router.patch("/pages/{page_id}", response_model=PageSummary)
async def update_page(
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[PageService, Depends(get_page_service)],
    page_id: UUID,
    body: PageUpdateRequest,
) -> PageSummary:
    require_permission(context, Permission.CONTENT_WRITE)
    tenant_id = require_tenant_id(context)
    page = await service.update_page(tenant_id, page_id, title=body.title, slug=body.slug)
    return page_summary(page)


@admin_router.post("/pages/{page_id}/draft", status_code=201)
async def create_draft(
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[PageService, Depends(get_page_service)],
    page_id: UUID,
    body: PageDraftRequest,
) -> dict[str, object]:
    require_permission(context, Permission.CONTENT_WRITE)
    tenant_id = require_tenant_id(context)
    version = await service.create_draft(
        tenant_id,
        page_id,
        layout=body.layout,
        actor_id=context.actor.user_id,
        expected_version=body.expected_version,
    )
    return version_response(version)


@admin_router.post("/pages/{page_id}/preview-token")
async def preview_token(
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[PageService, Depends(get_page_service)],
    page_id: UUID,
    version_id: UUID,
) -> dict[str, str]:
    require_permission(context, Permission.CONTENT_READ)
    tenant_id = require_tenant_id(context)
    await service.get_version(tenant_id, page_id, version_id)
    return {"token": service.sign_preview_token(tenant_id, page_id, version_id)}


@admin_router.post("/pages/{page_id}/publish")
async def publish_page(
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[PageService, Depends(get_page_service)],
    page_id: UUID,
    body: PublishRequest,
) -> dict[str, str]:
    require_permission(context, Permission.CONTENT_PUBLISH)
    tenant_id = require_tenant_id(context)
    await service.publish(
        tenant_id,
        page_id,
        version_id=body.version_id,
        expected_version=body.expected_version,
        actor_id=context.actor.user_id,
    )
    return {"status": "published"}


@admin_router.post("/pages/{page_id}/unpublish", status_code=204)
async def unpublish_page(
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[PageService, Depends(get_page_service)],
    page_id: UUID,
) -> Response:
    require_permission(context, Permission.CONTENT_PUBLISH)
    tenant_id = require_tenant_id(context)
    await service.unpublish(tenant_id, page_id, actor_id=context.actor.user_id)
    return Response(status_code=204)


@storefront_router.get("/pages/preview", response_model=StorefrontPageResponse)
async def preview_page(
    service: Annotated[PageService, Depends(get_page_service)],
    token: str,
) -> StorefrontPageResponse:
    """Previsualización acotada por token HMAC firmado (sin sesión)."""
    tenant_id, page_id, version_id = PageService.verify_preview_token(token)
    version = await service.get_version(tenant_id, page_id, version_id)
    page = await service._repository.get_page(tenant_id, page_id)
    return StorefrontPageResponse(
        slug=page.slug if page else "preview",
        title=page.title if page else "Vista previa",
        version=version.version,
        layout=version.layout,
    )


@admin_router.get("/theme", response_model=ThemeResponse)
async def get_theme(
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[PageService, Depends(get_page_service)],
) -> ThemeResponse:
    require_permission(context, Permission.CONTENT_READ)
    tenant_id = require_tenant_id(context)
    return ThemeResponse(tokens=await service.get_theme(tenant_id))


@admin_router.put("/theme", response_model=ThemeResponse)
async def put_theme(
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[PageService, Depends(get_page_service)],
    body: ThemeUpsertRequest,
) -> ThemeResponse:
    require_permission(context, Permission.CONTENT_WRITE)
    tenant_id = require_tenant_id(context)
    tokens = await service.upsert_theme(tenant_id, tokens=body.tokens)
    return ThemeResponse(tokens=tokens)


@storefront_router.get("/pages/{slug}", response_model=StorefrontPageResponse)
async def get_page_public(
    tenant: Annotated[Tenant, Depends(get_storefront_tenant)],
    service: Annotated[PageService, Depends(get_page_service)],
    slug: str,
) -> StorefrontPageResponse:
    if len(slug) > 128:
        raise AppError("PAGE_NOT_FOUND", "Página no publicada", 404)
    version = await service.get_published_page(tenant.id, slug)
    page = await service._repository.get_page(tenant.id, version.page_id)
    return StorefrontPageResponse(
        slug=slug,
        title=page.title if page else slug,
        version=version.version,
        layout=version.layout,
    )
