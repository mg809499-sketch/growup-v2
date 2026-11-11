from __future__ import annotations

from dataclasses import asdict
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field

from app import runtime
from app.api.deps import get_tenant_context
from app.core.errors import AppError
from app.domains.commerce.schemas import (
    OrderDetail,
    OrderItemResponse,
    OrderListResponse,
    OrderTransitionRequest,
    order_summary,
)
from app.domains.commerce.service import CommerceService
from app.domains.identity.models import Permission, RequestContext
from app.domains.identity.permissions import require_permission

router = APIRouter(prefix="/v1/admin", tags=["admin-orders"])


class PaymentAccountRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    public_key: str = Field(
        min_length=8, max_length=128, pattern=r"^(pub_test_|pub_prod_)[A-Za-z0-9]+$"
    )
    events_secret: str = Field(min_length=8, max_length=256)
    integrity_key: str = Field(min_length=8, max_length=256)
    mode: str = Field(pattern=r"^(sandbox|production)$")


def get_commerce_service() -> CommerceService:
    if runtime.commerce_service is None:
        raise AppError(
            "SERVICE_UNAVAILABLE",
            "El servicio de comercio no está configurado",
            503,
        )
    return runtime.commerce_service


@router.get("/orders", response_model=OrderListResponse)
async def list_orders(
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[CommerceService, Depends(get_commerce_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> OrderListResponse:
    require_permission(context, Permission.ORDERS_READ)
    tenant_id = context.tenant_id
    assert tenant_id is not None
    orders, total = await service.list_orders(tenant_id, limit=limit, offset=offset)
    return OrderListResponse(
        items=[order_summary(order) for order in orders],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/orders/{order_id}", response_model=OrderDetail)
async def get_order(
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[CommerceService, Depends(get_commerce_service)],
    order_id: UUID,
) -> OrderDetail:
    require_permission(context, Permission.ORDERS_READ)
    tenant_id = context.tenant_id
    assert tenant_id is not None
    order, items = await service.get_order(tenant_id, order_id)
    summary = order_summary(order)
    return OrderDetail(
        **summary.model_dump(),
        items=[OrderItemResponse(**asdict(item)) for item in items],
    )


@router.post("/orders/{order_id}/status", response_model=OrderDetail)
async def transition_order(
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[CommerceService, Depends(get_commerce_service)],
    order_id: UUID,
    body: OrderTransitionRequest,
) -> OrderDetail:
    require_permission(context, Permission.ORDERS_FULFILL)
    tenant_id = context.tenant_id
    assert tenant_id is not None
    order = await service.transition_order(tenant_id, order_id, target=body.status)
    _, items = await service.get_order(tenant_id, order_id)
    summary = order_summary(order)
    return OrderDetail(
        **summary.model_dump(),
        items=[OrderItemResponse(**asdict(item)) for item in items],
    )


@router.put("/payment-account", status_code=204)
async def upsert_payment_account(
    context: Annotated[RequestContext, Depends(get_tenant_context)],
    service: Annotated[CommerceService, Depends(get_commerce_service)],
    body: PaymentAccountRequest,
) -> None:
    """Conecta la cuenta Wompi del comercio (merchant of record = tenant)."""
    require_permission(context, Permission.BILLING_WRITE)
    tenant_id = context.tenant_id
    assert tenant_id is not None
    await service.upsert_payment_account(
        tenant_id,
        public_key=body.public_key,
        events_secret=body.events_secret,
        integrity_key=body.integrity_key,
        mode=body.mode,
    )
