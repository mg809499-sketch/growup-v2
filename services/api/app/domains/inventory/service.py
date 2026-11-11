from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.core.errors import AppError
from app.domains.inventory.models import InventoryLevel, Reservation
from app.domains.inventory.repository import InventoryRepository


class InventoryService:
    """Política de reservas: TTL, cantidades y transiciones.

    El `tenant_id` siempre proviene del contexto autenticado (host + JWT) o de
    un worker; nunca del body de una petición.
    """

    def __init__(
        self,
        repository: InventoryRepository,
        *,
        default_ttl_seconds: int = 900,
    ) -> None:
        self._repository = repository
        self._default_ttl_seconds = default_ttl_seconds

    async def reserve(
        self,
        tenant_id: UUID,
        variant_id: UUID,
        quantity: int,
        *,
        cart_id: UUID | None = None,
        order_id: UUID | None = None,
        location_id: UUID | None = None,
        ttl_seconds: int | None = None,
    ) -> Reservation:
        if quantity <= 0:
            raise AppError("QUANTITY_INVALID", "La cantidad debe ser positiva", 400)

        ttl = self._default_ttl_seconds if ttl_seconds is None else ttl_seconds
        if ttl <= 0:
            raise AppError(
                "RESERVATION_TTL_INVALID",
                "El TTL de la reserva debe ser positivo",
                400,
            )

        expires_at = datetime.now(UTC) + timedelta(seconds=ttl)
        return await self._repository.reserve(
            tenant_id,
            variant_id=variant_id,
            quantity=quantity,
            expires_at=expires_at,
            cart_id=cart_id,
            order_id=order_id,
            location_id=location_id,
        )

    async def get(self, tenant_id: UUID, reservation_id: UUID) -> Reservation | None:
        return await self._repository.get(tenant_id, reservation_id)

    async def release(self, tenant_id: UUID, reservation_id: UUID) -> Reservation:
        return await self._repository.release(tenant_id, reservation_id)

    async def confirm(
        self,
        tenant_id: UUID,
        reservation_id: UUID,
        *,
        order_id: UUID,
    ) -> Reservation:
        return await self._repository.confirm(
            tenant_id,
            reservation_id,
            order_id=order_id,
        )

    async def expire(self, tenant_id: UUID) -> int:
        return await self._repository.expire(tenant_id)

    async def list_levels(
        self,
        tenant_id: UUID,
        *,
        variant_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[InventoryLevel]:
        return await self._repository.list_levels(
            tenant_id,
            variant_id=variant_id,
            limit=limit,
            offset=offset,
        )
