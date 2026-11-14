from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse

from app.api.deps import get_admin_context, get_platform_tenant_service
from app.core.config import settings
from app.domains.identity.models import Permission, RequestContext
from app.domains.identity.permissions import require_permission
from app.domains.tenants.models import TenantStatus
from app.domains.tenants.platform_service import PlatformTenantService
from app.domains.tenants.schemas import (
    PauseTenantRequest,
    PlanOut,
    PlanUpdateRequest,
    PlatformAlertDismissRequest,
    PlatformAlertListResponse,
    PlatformOverviewResponse,
    PlatformTenantListResponse,
    PlatformTenantOverviewResponse,
    TenantCreatedResponse,
    TenantCreateRequest,
)

platform_router = APIRouter(prefix="/v1/platform", tags=["platform"])


@platform_router.post(
    "/tenants",
    response_model=TenantCreatedResponse,
    status_code=201,
)
async def create_tenant(
    payload: TenantCreateRequest,
    context: Annotated[RequestContext, Depends(get_admin_context)],
    service: Annotated[PlatformTenantService, Depends(get_platform_tenant_service)],
) -> TenantCreatedResponse:
    require_permission(context, Permission.PLATFORM_TENANTS)

    tenant = await service.create_tenant(
        actor_id=str(context.actor.user_id),
        actor_type=context.actor.role.value,
        slug=payload.slug,
        name=payload.name,
        owner_user_id=payload.owner_user_id,
        owner_email=payload.owner_email,
        legal_name=payload.legal_name,
        plan_id=payload.plan_id,
        trace_id=context.trace_id,
    )

    return TenantCreatedResponse(
        id=tenant.id,
        slug=tenant.slug,
        name=tenant.name,
        status=tenant.status,
        host=f"{tenant.slug}.{settings.root_domain}",
        owner_user_id=payload.owner_user_id,
    )


@platform_router.get("/tenants", response_model=PlatformTenantListResponse)
async def list_tenants(
    context: Annotated[RequestContext, Depends(get_admin_context)],
    service: Annotated[PlatformTenantService, Depends(get_platform_tenant_service)],
    status: Annotated[TenantStatus | None, Query()] = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PlatformTenantListResponse:
    require_permission(context, Permission.PLATFORM_TENANTS)
    page = await service.list_tenants(
        actor_id=context.actor.user_id,
        status=status.value if status is not None else None,
        query=q,
        limit=limit,
        offset=offset,
    )
    return PlatformTenantListResponse.from_domain(page)


@platform_router.get("/overview", response_model=PlatformOverviewResponse)
async def overview(
    context: Annotated[RequestContext, Depends(get_admin_context)],
    service: Annotated[PlatformTenantService, Depends(get_platform_tenant_service)],
) -> PlatformOverviewResponse:
    require_permission(context, Permission.PLATFORM_TENANTS)
    return await service.get_overview(actor_id=context.actor.user_id)


@platform_router.get(
    "/tenants/{tenant_id}/overview", response_model=PlatformTenantOverviewResponse
)
async def tenant_overview(
    context: Annotated[RequestContext, Depends(get_admin_context)],
    service: Annotated[PlatformTenantService, Depends(get_platform_tenant_service)],
    tenant_id: UUID,
) -> PlatformTenantOverviewResponse:
    require_permission(context, Permission.PLATFORM_TENANTS)
    return await service.get_tenant_overview(
        actor_id=context.actor.user_id, tenant_id=tenant_id
    )


@platform_router.get("/alerts", response_model=PlatformAlertListResponse)
async def list_alerts(
    context: Annotated[RequestContext, Depends(get_admin_context)],
    service: Annotated[PlatformTenantService, Depends(get_platform_tenant_service)],
) -> PlatformAlertListResponse:
    require_permission(context, Permission.PLATFORM_TENANTS)
    return await service.list_alerts(actor_id=context.actor.user_id)


@platform_router.post("/alerts/dismiss", status_code=204)
async def dismiss_alert(
    context: Annotated[RequestContext, Depends(get_admin_context)],
    service: Annotated[PlatformTenantService, Depends(get_platform_tenant_service)],
    payload: PlatformAlertDismissRequest,
) -> Response:
    require_permission(context, Permission.PLATFORM_TENANTS)
    await service.dismiss_alert(
        actor_id=context.actor.user_id,
        tenant_id=payload.tenant_id,
        alert_key=payload.alert_key,
    )
    return Response(status_code=204)


@platform_router.get("/plans", response_model=list[PlanOut])
async def list_plans(
    context: Annotated[RequestContext, Depends(get_admin_context)],
    service: Annotated[PlatformTenantService, Depends(get_platform_tenant_service)],
) -> list[PlanOut]:
    require_permission(context, Permission.PLATFORM_TENANTS)
    return await service.list_plans(actor_id=context.actor.user_id)


@platform_router.put("/plans/{plan_id}", response_model=PlanOut)
async def update_plan(
    context: Annotated[RequestContext, Depends(get_admin_context)],
    service: Annotated[PlatformTenantService, Depends(get_platform_tenant_service)],
    plan_id: UUID,
    payload: PlanUpdateRequest,
) -> PlanOut:
    require_permission(context, Permission.PLATFORM_TENANTS)
    return await service.update_plan(
        actor_id=context.actor.user_id, plan_id=plan_id, payload=payload
    )


@platform_router.patch("/tenants/{tenant_id}", status_code=204)
async def pause_tenant(
    context: Annotated[RequestContext, Depends(get_admin_context)],
    service: Annotated[PlatformTenantService, Depends(get_platform_tenant_service)],
    tenant_id: UUID,
    payload: PauseTenantRequest,
) -> Response:
    require_permission(context, Permission.PLATFORM_TENANTS)
    await service.pause_tenant(
        actor_id=context.actor.user_id, tenant_id=tenant_id, status=payload.status
    )
    return Response(status_code=204)


@platform_router.get("/tenants/export.csv", response_class=StreamingResponse)
async def export_tenants_csv(
    context: Annotated[RequestContext, Depends(get_admin_context)],
    service: Annotated[PlatformTenantService, Depends(get_platform_tenant_service)],
) -> StreamingResponse:
    require_permission(context, Permission.PLATFORM_TENANTS)
    csv_body = await service.tenants_csv(actor_id=context.actor.user_id)

    from collections.abc import AsyncIterator

    async def iterate() -> AsyncIterator[bytes]:
        yield csv_body.encode("utf-8")

    return StreamingResponse(
        iterate(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="tenants.csv"'},
    )
