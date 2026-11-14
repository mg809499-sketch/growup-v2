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


@dataclass(frozen=True, slots=True)
class AISuggestion:
    id: UUID
    tenant_id: UUID
    type: str
    status: str
    payload: dict[str, object]
    proposed_at: datetime

    @property
    def variant_id(self) -> UUID | None:
        raw = self.payload.get("variant_id") if isinstance(self.payload, dict) else None
        try:
            return UUID(str(raw)) if raw else None
        except (ValueError, TypeError):
            return None

    @property
    def sku(self) -> str | None:
        value = self.payload.get("sku") if isinstance(self.payload, dict) else None
        return str(value) if value else None

    @property
    def stock(self) -> int | None:
        val = self.payload.get("stock") if isinstance(self.payload, dict) else None
        return int(val) if isinstance(val, int) else None

    @property
    def message(self) -> str:
        return f"Reordenar {self.sku or 'variante'}: stock {self.stock} por debajo del mínimo."
