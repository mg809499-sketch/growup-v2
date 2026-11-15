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


class PaymentStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUND_PENDING = "refund_pending"
    REFUNDED = "refunded"


class FulfillmentStatus(StrEnum):
    UNFULFILLED = "unfulfilled"
    PREPARING = "preparing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"


class OrderLifecycleStatus(StrEnum):
    OPEN = "open"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


_ALLOWED_PAYMENT_TRANSITIONS: dict[PaymentStatus, frozenset[PaymentStatus]] = {
    PaymentStatus.PENDING: frozenset({PaymentStatus.PAID, PaymentStatus.FAILED}),
    PaymentStatus.PAID: frozenset({PaymentStatus.REFUND_PENDING, PaymentStatus.REFUNDED}),
    PaymentStatus.FAILED: frozenset(),
    PaymentStatus.REFUND_PENDING: frozenset({PaymentStatus.REFUNDED}),
    PaymentStatus.REFUNDED: frozenset(),
}

_ALLOWED_FULFILLMENT_TRANSITIONS: dict[FulfillmentStatus, frozenset[FulfillmentStatus]] = {
    FulfillmentStatus.UNFULFILLED: frozenset(
        {FulfillmentStatus.PREPARING, FulfillmentStatus.SHIPPED}
    ),
    FulfillmentStatus.PREPARING: frozenset({FulfillmentStatus.SHIPPED}),
    FulfillmentStatus.SHIPPED: frozenset({FulfillmentStatus.DELIVERED}),
    FulfillmentStatus.DELIVERED: frozenset(),
}

_ALLOWED_LIFECYCLE_TRANSITIONS: dict[OrderLifecycleStatus, frozenset[OrderLifecycleStatus]] = {
    OrderLifecycleStatus.OPEN: frozenset(
        {
            OrderLifecycleStatus.COMPLETED,
            OrderLifecycleStatus.CANCELLED,
            OrderLifecycleStatus.EXPIRED,
        }
    ),
    OrderLifecycleStatus.COMPLETED: frozenset(),
    OrderLifecycleStatus.CANCELLED: frozenset(),
    OrderLifecycleStatus.EXPIRED: frozenset(),
}


def transition_payment_status(current: PaymentStatus, target: PaymentStatus) -> PaymentStatus:
    if current == target:
        return current
    if target not in _ALLOWED_PAYMENT_TRANSITIONS[current]:
        raise ValueError(f"Transición de pago inválida: {current} -> {target}")
    return target


def transition_fulfillment_status(
    current: FulfillmentStatus,
    target: FulfillmentStatus,
    *,
    payment_status: PaymentStatus,
) -> FulfillmentStatus:
    if current == target:
        return current
    if payment_status != PaymentStatus.PAID:
        raise ValueError("No se puede avanzar el despacho si el pago no está en estado 'paid'")
    if target not in _ALLOWED_FULFILLMENT_TRANSITIONS[current]:
        raise ValueError(f"Transición de despacho inválida: {current} -> {target}")
    return target


def transition_lifecycle_status(
    current: OrderLifecycleStatus,
    target: OrderLifecycleStatus,
) -> OrderLifecycleStatus:
    if current == target:
        return current
    if target not in _ALLOWED_LIFECYCLE_TRANSITIONS[current]:
        raise ValueError(f"Transición de ciclo de vida inválida: {current} -> {target}")
    return target


def derive_orthogonal_statuses(
    status: OrderStatus,
) -> tuple[PaymentStatus, FulfillmentStatus, OrderLifecycleStatus]:
    match status:
        case OrderStatus.PENDING:
            return (
                PaymentStatus.PENDING,
                FulfillmentStatus.UNFULFILLED,
                OrderLifecycleStatus.OPEN,
            )
        case OrderStatus.PAID:
            return (
                PaymentStatus.PAID,
                FulfillmentStatus.UNFULFILLED,
                OrderLifecycleStatus.OPEN,
            )
        case OrderStatus.PREPARING:
            return (
                PaymentStatus.PAID,
                FulfillmentStatus.PREPARING,
                OrderLifecycleStatus.OPEN,
            )
        case OrderStatus.SHIPPED:
            return (
                PaymentStatus.PAID,
                FulfillmentStatus.SHIPPED,
                OrderLifecycleStatus.OPEN,
            )
        case OrderStatus.DELIVERED:
            return (
                PaymentStatus.PAID,
                FulfillmentStatus.DELIVERED,
                OrderLifecycleStatus.COMPLETED,
            )
        case OrderStatus.REFUND_PENDING:
            return (
                PaymentStatus.REFUND_PENDING,
                FulfillmentStatus.UNFULFILLED,
                OrderLifecycleStatus.OPEN,
            )
        case OrderStatus.REFUNDED:
            return (
                PaymentStatus.REFUNDED,
                FulfillmentStatus.UNFULFILLED,
                OrderLifecycleStatus.COMPLETED,
            )
        case OrderStatus.FAILED:
            return (
                PaymentStatus.FAILED,
                FulfillmentStatus.UNFULFILLED,
                OrderLifecycleStatus.CANCELLED,
            )
        case OrderStatus.EXPIRED:
            return (
                PaymentStatus.FAILED,
                FulfillmentStatus.UNFULFILLED,
                OrderLifecycleStatus.EXPIRED,
            )
        case OrderStatus.CANCELLED:
            return (
                PaymentStatus.FAILED,
                FulfillmentStatus.UNFULFILLED,
                OrderLifecycleStatus.CANCELLED,
            )


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

    @property
    def payment_status(self) -> PaymentStatus:
        return derive_orthogonal_statuses(self.status)[0]

    @property
    def fulfillment_status(self) -> FulfillmentStatus:
        return derive_orthogonal_statuses(self.status)[1]

    @property
    def lifecycle_status(self) -> OrderLifecycleStatus:
        return derive_orthogonal_statuses(self.status)[2]


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
