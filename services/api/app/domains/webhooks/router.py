from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.api.deps import get_admin_context, get_webhook_service, require_tenant_id
from app.domains.identity.models import Permission, RequestContext
from app.domains.identity.permissions import require_permission
from app.domains.webhooks.schemas import (
    WebhookEndpointCreateRequest,
    WebhookEndpointCreateResponse,
    WebhookEndpointOut,
)
from app.domains.webhooks.service import WebhookService

router = APIRouter(prefix="/v1/admin/webhooks", tags=["admin-webhooks"])


@router.get("", response_model=list[WebhookEndpointOut])
async def list_webhooks(
    context: Annotated[RequestContext, Depends(get_admin_context)],
    service: Annotated[WebhookService, Depends(get_webhook_service)],
) -> list[WebhookEndpointOut]:
    require_permission(context, Permission.WEBHOOKS_MANAGE)
    tenant_id = require_tenant_id(context)
    return await service.list_endpoints(tenant_id)


@router.post("", response_model=WebhookEndpointCreateResponse, status_code=201)
async def create_webhook(
    context: Annotated[RequestContext, Depends(get_admin_context)],
    service: Annotated[WebhookService, Depends(get_webhook_service)],
    body: WebhookEndpointCreateRequest,
) -> WebhookEndpointCreateResponse:
    require_permission(context, Permission.WEBHOOKS_MANAGE)
    tenant_id = require_tenant_id(context)
    return await service.create_endpoint(tenant_id, body)


@router.delete("/{endpoint_id}", status_code=204)
async def delete_webhook(
    context: Annotated[RequestContext, Depends(get_admin_context)],
    service: Annotated[WebhookService, Depends(get_webhook_service)],
    endpoint_id: UUID,
) -> Response:
    require_permission(context, Permission.WEBHOOKS_MANAGE)
    tenant_id = require_tenant_id(context)
    await service.delete_endpoint(tenant_id, endpoint_id)
    return Response(status_code=204)
