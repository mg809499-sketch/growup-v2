from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app import runtime
from app.api.deps import get_tenant_context
from app.core.errors import AppError
from app.domains.identity.models import Permission, RequestContext
from app.domains.identity.permissions import require_permission
from app.domains.inventory.schemas import InventoryLevelListResponse, InventoryLevelResponse
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
    tenant_id = context.tenant_id
    assert tenant_id is not None  # get_tenant_context garantiza tenant cuando llega aquí
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
