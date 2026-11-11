from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ReservationStatus(StrEnum):
    ACTIVE = "active"
    CONFIRMED = "confirmed"
    RELEASED = "released"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class Reservation:
    id: UUID
    tenant_id: UUID
    variant_id: UUID
    location_id: UUID
    quantity: int
    status: ReservationStatus
    expires_at: datetime
    cart_id: UUID | None
    order_id: UUID | None


@dataclass(frozen=True, slots=True)
class InventoryLevel:
    variant_id: UUID
    location_id: UUID
    location_name: str
    sku: str | None
    available: int
    reserved: int
    sellable: int
