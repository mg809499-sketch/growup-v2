from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_admin_context, get_platform_tenant_service
from app.core.config import settings
from app.domains.identity.models import Permission, RequestContext
from app.domains.identity.permissions import require_permission
from app.domains.tenants.platform_service import PlatformTenantService
from app.domains.tenants.schemas import TenantCreatedResponse, TenantCreateRequest

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
