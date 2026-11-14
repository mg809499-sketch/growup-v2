from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.errors import AppError
from app.domains.commerce.models import Cart, Order, OrderStatus

_EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class CartItemResponse(BaseModel):
    variant_id: UUID
    product_name: str
    variant_sku: str | None
    variant_title: str | None
    unit_price_cents: int
    quantity: int
    line_total_cents: int


class CartResponse(BaseModel):
    cart_id: UUID
    items: list[CartItemResponse]
    subtotal_cents: int
    currency: Literal["COP"] = "COP"


class CartAddRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variant_id: UUID
    quantity: int = Field(ge=1, le=50)


class CartUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variant_id: UUID
    quantity: int = Field(ge=0, le=50)


class ShippingAddressInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=120)
    phone: str | None = Field(default=None, max_length=30)
    line1: str = Field(min_length=3, max_length=200)
    line2: str | None = Field(default=None, max_length=200)
    city: str = Field(min_length=2, max_length=80)
    state: str = Field(min_length=2, max_length=80)
    postal_code: str | None = Field(default=None, max_length=20)


class CheckoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320, pattern=_EMAIL)
    shipping_zone: str = Field(min_length=1, max_length=60, pattern=r"^[a-z0-9_-]+$")
    shipping: ShippingAddressInput
    redirect_base_url: str | None = Field(
        default=None, pattern=r"^https?://[^\s<>\"']+$"
    )


class CheckoutResponse(BaseModel):
    order_id: UUID
    reference: str
    total_cents: int
    amount_in_cents: int
    currency: Literal["COP"] = "COP"
    wompi_url: str


class OrderSummary(BaseModel):
    id: UUID
    email: str
    status: OrderStatus
    subtotal_cents: int
    tax_cents: int
    shipping_cents: int
    total_cents: int
    tax_rate_bps: int
    shipping_zone: str | None
    created_at: str
    updated_at: str


class OrderItemResponse(BaseModel):
    product_name: str
    variant_sku: str | None
    variant_title: str | None
    unit_price_cents: int
    quantity: int


class OrderDetail(OrderSummary):
    items: list[OrderItemResponse]


class OrderListResponse(BaseModel):
    items: list[OrderSummary]
    total: int
    limit: int
    offset: int


class OrderTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: OrderStatus


# ---------- Webhook Wompi (esquema público de Wompi, tipado y fail-closed) ----------
class WompiTransaction(BaseModel):
    """Transacción embebida en data.transaction. Wompi añade campos libremente."""

    model_config = ConfigDict(extra="allow")

    id: str | None = Field(default=None, max_length=120)
    reference: str = Field(default="", max_length=120)
    status: str = Field(default="", max_length=40)
    payment_method_type: str | None = Field(default=None, max_length=60)


class WompiEventData(BaseModel):
    model_config = ConfigDict(extra="allow")

    transaction: WompiTransaction = Field(default_factory=WompiTransaction)


class WompiSignature(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    properties: list[str] = Field(default_factory=list, max_length=20)
    timestamp: int | str | None = None
    checksum: str | None = Field(default=None, max_length=128)
    checksum_sha256: str | None = Field(default=None, alias="checksum-sha256", max_length=128)


class WompiEvent(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | None = Field(default=None, max_length=120)
    data: WompiEventData = Field(default_factory=WompiEventData)
    signature: WompiSignature = Field(default_factory=WompiSignature)


def parse_wompi_event(event: dict[str, Any]) -> WompiEvent:
    """Parsea el evento con esquema cerrado; 400 ante cualquier desviación de tipos."""
    if not isinstance(event, dict):
        raise AppError("WOMPI_EVENT_INVALID", "Cuerpo JSON inválido", 400)
    try:
        return WompiEvent.model_validate(event)
    except ValidationError as exc:
        issues = [".".join(str(part) for part in err.get("loc", ())) for err in exc.errors()[:5]]
        raise AppError(
            "WOMPI_EVENT_INVALID",
            "Evento Wompi inválido",
            400,
            {"issues": issues},
        ) from exc


def cart_response(cart: Cart) -> CartResponse:
    items = [
        CartItemResponse(
            variant_id=item.variant_id,
            product_name=item.product_name,
            variant_sku=item.variant_sku,
            variant_title=item.variant_title,
            unit_price_cents=item.unit_price_cents,
            quantity=item.quantity,
            line_total_cents=item.unit_price_cents * item.quantity,
        )
        for item in cart.items
    ]
    return CartResponse(cart_id=cart.id, items=items, subtotal_cents=cart.subtotal_cents)


def order_summary(order: Order) -> OrderSummary:
    return OrderSummary(
        id=order.id,
        email=order.email,
        status=order.status,
        subtotal_cents=order.subtotal_cents,
        tax_cents=order.tax_cents,
        shipping_cents=order.shipping_cents,
        total_cents=order.total_cents,
        tax_rate_bps=order.tax_rate_bps,
        shipping_zone=order.shipping_zone,
        created_at=order.created_at.isoformat(),
        updated_at=order.updated_at.isoformat(),
    )


def order_item_response(item: Any) -> OrderItemResponse:
    return OrderItemResponse(
        product_name=item.product_name,
        variant_sku=item.variant_sku,
        variant_title=item.variant_title,
        unit_price_cents=item.unit_price_cents,
        quantity=item.quantity,
    )
