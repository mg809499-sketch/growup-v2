from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.core.errors import AppError
from app.domains.inventory.models import Reservation, ReservationStatus
from app.domains.inventory.service import InventoryService


class FakeInventoryRepository:
    def __init__(self) -> None:
        self.reservations: list[Reservation] = []
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def reserve(
        self,
        tenant_id: UUID,
        *,
        variant_id: UUID,
        quantity: int,
        expires_at: datetime,
        cart_id: UUID | None = None,
        order_id: UUID | None = None,
        location_id: UUID | None = None,
    ) -> Reservation:
        self.calls.append(
            (
                "reserve",
                {
                    "tenant_id": tenant_id,
                    "variant_id": variant_id,
                    "quantity": quantity,
                    "expires_at": expires_at,
                    "cart_id": cart_id,
                    "order_id": order_id,
                    "location_id": location_id,
                },
            )
        )
        reservation = Reservation(
            id=uuid4(),
            tenant_id=tenant_id,
            variant_id=variant_id,
            location_id=location_id or uuid4(),
            quantity=quantity,
            status=ReservationStatus.ACTIVE,
            expires_at=expires_at,
            cart_id=cart_id,
            order_id=order_id,
        )
        self.reservations.append(reservation)
        return reservation

    async def get(self, tenant_id: UUID, reservation_id: UUID) -> Reservation | None:
        self.calls.append(("get", {"tenant_id": tenant_id, "id": reservation_id}))
        return next((r for r in self.reservations if r.id == reservation_id), None)

    async def release(self, tenant_id: UUID, reservation_id: UUID) -> Reservation:
        self.calls.append(("release", {"tenant_id": tenant_id, "id": reservation_id}))
        return self.reservations[0]

    async def confirm(
        self,
        tenant_id: UUID,
        reservation_id: UUID,
        *,
        order_id: UUID,
    ) -> Reservation:
        self.calls.append(
            ("confirm", {"tenant_id": tenant_id, "id": reservation_id, "order_id": order_id})
        )
        return self.reservations[0]

    async def expire(self, tenant_id: UUID) -> int:
        self.calls.append(("expire", {"tenant_id": tenant_id}))
        return 2


async def test_reserve_sets_expiry_from_ttl() -> None:
    repository = FakeInventoryRepository()
    service = InventoryService(repository, default_ttl_seconds=120)
    tenant_id = uuid4()
    variant_id = uuid4()
    cart_id = uuid4()

    before = datetime.now(UTC) + timedelta(seconds=120)
    reservation = await service.reserve(
        tenant_id,
        variant_id,
        2,
        cart_id=cart_id,
    )
    after = datetime.now(UTC) + timedelta(seconds=120)

    assert reservation.status is ReservationStatus.ACTIVE
    assert reservation.quantity == 2
    assert reservation.cart_id == cart_id
    assert before <= reservation.expires_at <= after

    name, call = repository.calls[0]
    assert name == "reserve"
    assert call["tenant_id"] == tenant_id
    assert call["variant_id"] == variant_id
    assert call["quantity"] == 2


async def test_reserve_accepts_explicit_ttl() -> None:
    repository = FakeInventoryRepository()
    service = InventoryService(repository, default_ttl_seconds=120)
    tenant_id = uuid4()

    before = datetime.now(UTC) + timedelta(seconds=30)
    reservation = await service.reserve(
        tenant_id,
        uuid4(),
        1,
        ttl_seconds=30,
    )
    after = datetime.now(UTC) + timedelta(seconds=30)

    assert before <= reservation.expires_at <= after


@pytest.mark.parametrize("quantity", [0, -1])
async def test_reserve_rejects_non_positive_quantity(quantity: int) -> None:
    repository = FakeInventoryRepository()
    service = InventoryService(repository)

    with pytest.raises(AppError) as exc_info:
        await service.reserve(uuid4(), uuid4(), quantity)

    assert exc_info.value.code == "QUANTITY_INVALID"
    assert repository.calls == []


@pytest.mark.parametrize("ttl", [0, -5])
async def test_reserve_rejects_non_positive_ttl(ttl: int) -> None:
    repository = FakeInventoryRepository()
    service = InventoryService(repository)

    with pytest.raises(AppError) as exc_info:
        await service.reserve(uuid4(), uuid4(), 1, ttl_seconds=ttl)

    assert exc_info.value.code == "RESERVATION_TTL_INVALID"
    assert repository.calls == []


async def test_release_and_confirm_delegate() -> None:
    repository = FakeInventoryRepository()
    service = InventoryService(repository)
    tenant_id = uuid4()
    reservation = await service.reserve(tenant_id, uuid4(), 1)

    await service.release(tenant_id, reservation.id)
    order_id = uuid4()
    await service.confirm(tenant_id, reservation.id, order_id=order_id)
    assert await service.get(tenant_id, reservation.id) is not None
    assert await service.expire(tenant_id) == 2

    assert [call[0] for call in repository.calls] == [
        "reserve",
        "release",
        "confirm",
        "get",
        "expire",
    ]
    assert repository.calls[2][1]["order_id"] == order_id
