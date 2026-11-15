from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domains.commerce.models import (
    FulfillmentStatus,
    Order,
    OrderLifecycleStatus,
    OrderStatus,
    PaymentStatus,
    derive_orthogonal_statuses,
    transition_fulfillment_status,
    transition_lifecycle_status,
    transition_payment_status,
)


def test_payment_state_machine_valid_transitions() -> None:
    state = PaymentStatus.PENDING
    state = transition_payment_status(state, PaymentStatus.PAID)
    assert state == PaymentStatus.PAID
    state = transition_payment_status(state, PaymentStatus.REFUND_PENDING)
    assert state == PaymentStatus.REFUND_PENDING
    state = transition_payment_status(state, PaymentStatus.REFUNDED)
    assert state == PaymentStatus.REFUNDED


def test_payment_state_machine_rejects_invalid_transitions() -> None:
    with pytest.raises(ValueError, match="Transición de pago inválida"):
        transition_payment_status(PaymentStatus.FAILED, PaymentStatus.PAID)

    with pytest.raises(ValueError, match="Transición de pago inválida"):
        transition_payment_status(PaymentStatus.REFUNDED, PaymentStatus.PAID)


def test_fulfillment_requires_paid_status() -> None:
    with pytest.raises(ValueError, match="pago no está en estado 'paid'"):
        transition_fulfillment_status(
            FulfillmentStatus.UNFULFILLED,
            FulfillmentStatus.PREPARING,
            payment_status=PaymentStatus.PENDING,
        )


def test_fulfillment_valid_and_invalid_transitions() -> None:
    state = FulfillmentStatus.UNFULFILLED
    state = transition_fulfillment_status(
        state,
        FulfillmentStatus.PREPARING,
        payment_status=PaymentStatus.PAID,
    )
    state = transition_fulfillment_status(
        state,
        FulfillmentStatus.SHIPPED,
        payment_status=PaymentStatus.PAID,
    )
    state = transition_fulfillment_status(
        state,
        FulfillmentStatus.DELIVERED,
        payment_status=PaymentStatus.PAID,
    )
    assert state == FulfillmentStatus.DELIVERED

    with pytest.raises(ValueError, match="Transición de despacho inválida"):
        transition_fulfillment_status(
            FulfillmentStatus.DELIVERED,
            FulfillmentStatus.PREPARING,
            payment_status=PaymentStatus.PAID,
        )


def test_lifecycle_transitions() -> None:
    assert (
        transition_lifecycle_status(
            OrderLifecycleStatus.OPEN,
            OrderLifecycleStatus.COMPLETED,
        )
        == OrderLifecycleStatus.COMPLETED
    )
    with pytest.raises(ValueError, match="Transición de ciclo de vida inválida"):
        transition_lifecycle_status(
            OrderLifecycleStatus.CANCELLED,
            OrderLifecycleStatus.OPEN,
        )


def test_order_derives_orthogonal_axes() -> None:
    now = datetime.now(UTC)
    order = Order(
        id=uuid4(),
        tenant_id=uuid4(),
        email="comprador@growup.com",
        status=OrderStatus.SHIPPED,
        subtotal_cents=100_000,
        tax_cents=19_000,
        shipping_cents=8_000,
        total_cents=127_000,
        tax_rate_bps=1900,
        shipping_zone="bogota",
        created_at=now,
        updated_at=now,
    )
    assert order.payment_status == PaymentStatus.PAID
    assert order.fulfillment_status == FulfillmentStatus.SHIPPED
    assert order.lifecycle_status == OrderLifecycleStatus.OPEN

    for status in OrderStatus:
        payment, fulfillment, lifecycle = derive_orthogonal_statuses(status)
        assert isinstance(payment, PaymentStatus)
        assert isinstance(fulfillment, FulfillmentStatus)
        assert isinstance(lifecycle, OrderLifecycleStatus)
