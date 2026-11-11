from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class OrderStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PREPARING = "preparing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    REFUND_PENDING = "refund_pending"
    REFUNDED = "refunded"


@dataclass(frozen=True, slots=True)
class CartItem:
    id: UUID
    variant_id: UUID
    product_name: str
    variant_sku: str | None
    variant_title: str | None
    unit_price_cents: int
    quantity: int


@dataclass(frozen=True, slots=True)
class Cart:
    id: UUID
    tenant_id: UUID
    status: str
    items: tuple[CartItem, ...]
    subtotal_cents: int
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class Order:
    id: UUID
    tenant_id: UUID
    email: str
    status: OrderStatus
    subtotal_cents: int
    tax_cents: int
    shipping_cents: int
    total_cents: int
    tax_rate_bps: int
    shipping_zone: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class OrderItem:
    id: UUID
    order_id: UUID
    variant_id: UUID | None
    product_name: str
    variant_sku: str | None
    variant_title: str | None
    unit_price_cents: int
    quantity: int


@dataclass(frozen=True, slots=True)
class TenantPaymentAccount:
    tenant_id: UUID
    provider: str
    public_key: str
    events_secret_encrypted: str
    integrity_key_encrypted: str
    mode: str
