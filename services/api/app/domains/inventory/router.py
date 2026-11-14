from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app import runtime
from app.api.deps import get_tenant_context, require_tenant_id
from app.core.errors import AppError
from app.domains.identity.models import Permission, RequestContext
from app.domains.identity.permissions import require_permission
from app.domains.inventory.schemas import (
    AISuggestionListResponse,
    AISuggestionResolveRequest,
    AISuggestionResponse,
    InventoryLevelListResponse,
    InventoryLevelResponse,
)
from app.domains.inventory.service import InventoryService

router = APIRouter(prefix="/v1/admin/inventory", tags=["admin-inventory"])


def get_inventory_service() -> InventoryService:
    if runtime.inventory_service is None:
        raise AppError(
            "SERVICE_UNAVAILABLE",
            "El inventario no está configurado",
            503,
        )
    return runtime.inventory_service


@router.get("/levels", response_model=InventoryLevelListResponse)
async def list_levels(
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[InventoryService, Depends(get_inventory_service)],
    variant_id: Annotated[UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> InventoryLevelListResponse:
    require_permission(context, Permission.CATALOG_READ)
    tenant_id = require_tenant_id(context)
    levels = await service.list_levels(
        tenant_id,
        variant_id=variant_id,
        limit=limit,
        offset=offset,
    )
    return InventoryLevelListResponse(
        items=[
            InventoryLevelResponse(
                variant_id=level.variant_id,
                location_id=level.location_id,
                location_name=level.location_name,
                sku=level.sku,
                available=level.available,
                reserved=level.reserved,
                sellable=level.sellable,
            )
            for level in levels
        ],
        limit=limit,
        offset=offset,
    )


@router.get("/suggestions", response_model=AISuggestionListResponse)
async def list_suggestions(
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[InventoryService, Depends(get_inventory_service)],
    status: Annotated[str | None, Query()] = "pending",
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AISuggestionListResponse:
    require_permission(context, Permission.CATALOG_WRITE)
    tenant_id = require_tenant_id(context)
    normalized_status = status if status and status != "all" else None
    items, total = await service.list_suggestions(
        tenant_id,
        status=normalized_status,
        limit=limit,
        offset=offset,
    )
    return AISuggestionListResponse(
        items=[
            AISuggestionResponse(
                id=item.id,
                type=item.type,
                status=item.status,
                payload=item.payload,
                proposed_at=item.proposed_at,
            )
            for item in items
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/suggestions/{suggestion_id}/resolve", response_model=AISuggestionResponse)
async def resolve_suggestion(
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[InventoryService, Depends(get_inventory_service)],
    suggestion_id: UUID,
    body: AISuggestionResolveRequest,
) -> AISuggestionResponse:
    require_permission(context, Permission.CATALOG_WRITE)
    tenant_id = require_tenant_id(context)
    item = await service.resolve_suggestion(
        tenant_id, suggestion_id, action=body.action
    )
    return AISuggestionResponse(
        id=item.id,
        type=item.type,
        status=item.status,
        payload=item.payload,
        proposed_at=item.proposed_at,
    )
