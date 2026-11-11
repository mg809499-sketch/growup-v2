from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID

from app.core.db import Database
from app.core.errors import AppError
from app.domains.inventory.models import InventoryLevel, Reservation, ReservationStatus

_RESERVATION_COLUMNS = (
    "id, tenant_id, variant_id, location_id, cart_id, order_id, "
    "quantity, status, expires_at"
)


class InventoryRepository(Protocol):
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
    ) -> Reservation: ...

    async def get(self, tenant_id: UUID, reservation_id: UUID) -> Reservation | None: ...

    async def release(self, tenant_id: UUID, reservation_id: UUID) -> Reservation: ...

    async def confirm(
        self,
        tenant_id: UUID,
        reservation_id: UUID,
        *,
        order_id: UUID,
    ) -> Reservation: ...

    async def expire(self, tenant_id: UUID) -> int: ...

    async def list_levels(
        self,
        tenant_id: UUID,
        *,
        variant_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[InventoryLevel]: ...


class PostgresInventoryRepository:
    """Reservas atómicas; el stock se descuenta al confirmar la venta."""

    def __init__(self, database: Database) -> None:
        self._database = database

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
        async with self._database.tenant_transaction(tenant_id) as connection:
            if location_id is None:
                location_id = await connection.fetchval(
                    "select id from app.locations "
                    "where tenant_id = $1 and is_default limit 1",
                    tenant_id,
                )
                if location_id is None:
                    raise AppError(
                        "LOCATION_NOT_FOUND",
                        "El tenant no tiene ubicación default",
                        400,
                    )
            else:
                exists = await connection.fetchval(
                    "select 1 from app.locations where tenant_id = $1 and id = $2",
                    tenant_id,
                    location_id,
                )
                if not exists:
                    raise AppError("LOCATION_NOT_FOUND", "La ubicación no existe", 404)

            sellable = await connection.fetchval(
                """
                select 1
                from app.product_variants v
                join app.products p
                  on p.tenant_id = v.tenant_id and p.id = v.product_id
                where v.tenant_id = $1
                  and v.id = $2
                  and v.is_active
                  and p.status = 'active'
                """,
                tenant_id,
                variant_id,
            )
            if not sellable:
                raise AppError("VARIANT_NOT_FOUND", "La variante no está disponible", 404)

            level_id = await connection.fetchval(
                """
                update app.inventory_levels
                set reserved = reserved + $3,
                    updated_at = now()
                where tenant_id = $1
                  and variant_id = $2
                  and location_id = $4
                  and available - reserved >= $3
                returning id
                """,
                tenant_id,
                variant_id,
                quantity,
                location_id,
            )
            if level_id is None:
                raise AppError("INSUFFICIENT_STOCK", "Stock insuficiente", 409)

            row = await connection.fetchrow(
                f"""
                insert into app.inventory_reservations
                    (tenant_id, variant_id, location_id, cart_id, order_id,
                     quantity, expires_at)
                values ($1, $2, $3, $4, $5, $6, $7)
                returning {_RESERVATION_COLUMNS}
                """,
                tenant_id,
                variant_id,
                location_id,
                cart_id,
                order_id,
                quantity,
                expires_at,
            )
            if row is None:
                raise AppError("RESERVATION_CREATE_FAILED", "No se creó la reserva", 500)
            return _reservation(row)

    async def get(self, tenant_id: UUID, reservation_id: UUID) -> Reservation | None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            row = await connection.fetchrow(
                f"""
                select {_RESERVATION_COLUMNS}
                from app.inventory_reservations
                where tenant_id = $1 and id = $2
                """,
                tenant_id,
                reservation_id,
            )
        return _reservation(row) if row is not None else None

    async def list_levels(
        self,
        tenant_id: UUID,
        *,
        variant_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[InventoryLevel]:
        async with self._database.tenant_transaction(tenant_id) as connection:
            rows = await connection.fetch(
                """
                select il.variant_id, il.location_id, l.name as location_name,
                       v.sku, il.available, il.reserved,
                       (il.available - il.reserved) as sellable
                from app.inventory_levels il
                join app.locations l
                  on l.tenant_id = il.tenant_id and l.id = il.location_id
                left join app.product_variants v
                  on v.tenant_id = il.tenant_id and v.id = il.variant_id
                where il.tenant_id = $1
                  and ($2::uuid is null or il.variant_id = $2)
                order by il.variant_id, l.name
                limit $3 offset $4
                """,
                tenant_id,
                variant_id,
                limit,
                offset,
            )
        return [
            InventoryLevel(
                variant_id=row["variant_id"],
                location_id=row["location_id"],
                location_name=row["location_name"],
                sku=row["sku"],
                available=row["available"],
                reserved=row["reserved"],
                sellable=row["sellable"],
            )
            for row in rows
        ]

    async def release(self, tenant_id: UUID, reservation_id: UUID) -> Reservation:
        async with self._database.tenant_transaction(tenant_id) as connection:
            row = await self._lock(connection, tenant_id, reservation_id)
            status = ReservationStatus(row["status"])

            if status in (ReservationStatus.RELEASED, ReservationStatus.EXPIRED):
                return _reservation(row)
            if status is not ReservationStatus.ACTIVE:
                raise AppError(
                    "RESERVATION_NOT_ACTIVE",
                    "La reserva ya fue confirmada",
                    409,
                )

            updated_level = await connection.fetchval(
                """
                update app.inventory_levels
                set reserved = reserved - $3,
                    updated_at = now()
                where tenant_id = $1
                  and variant_id = $2
                  and location_id = $4
                  and reserved >= $3
                returning id
                """,
                tenant_id,
                row["variant_id"],
                row["quantity"],
                row["location_id"],
            )
            if updated_level is None:
                raise AppError(
                    "INVENTORY_INCONSISTENT",
                    "El stock reservado no cuadra",
                    500,
                )

            updated = await connection.fetchrow(
                f"""
                update app.inventory_reservations
                set status = 'released'
                where tenant_id = $1 and id = $2
                returning {_RESERVATION_COLUMNS}
                """,
                tenant_id,
                reservation_id,
            )
            if updated is None:
                raise AppError("RESERVATION_NOT_FOUND", "Reserva no encontrada", 404)
            return _reservation(updated)

    async def confirm(
        self,
        tenant_id: UUID,
        reservation_id: UUID,
        *,
        order_id: UUID,
    ) -> Reservation:
        async with self._database.tenant_transaction(tenant_id) as connection:
            row = await self._lock(connection, tenant_id, reservation_id)
            status = ReservationStatus(row["status"])

            if status is ReservationStatus.CONFIRMED:
                if row["order_id"] == order_id:
                    return _reservation(row)
                raise AppError(
                    "RESERVATION_ORDER_MISMATCH",
                    "La reserva pertenece a otra orden",
                    409,
                )
            if status is not ReservationStatus.ACTIVE:
                raise AppError(
                    "RESERVATION_NOT_ACTIVE",
                    "La reserva expiró o fue liberada",
                    409,
                )
            if row["expires_at"] <= datetime.now(UTC):
                raise AppError(
                    "RESERVATION_EXPIRED",
                    "La reserva expiró y no puede confirmarse",
                    409,
                )
            if row["order_id"] is not None and row["order_id"] != order_id:
                raise AppError(
                    "RESERVATION_ORDER_MISMATCH",
                    "La reserva pertenece a otra orden",
                    409,
                )

            updated_level = await connection.fetchval(
                """
                update app.inventory_levels
                set available = available - $3,
                    reserved = reserved - $3,
                    updated_at = now()
                where tenant_id = $1
                  and variant_id = $2
                  and location_id = $4
                  and available >= $3
                  and reserved >= $3
                returning id
                """,
                tenant_id,
                row["variant_id"],
                row["quantity"],
                row["location_id"],
            )
            if updated_level is None:
                raise AppError(
                    "INVENTORY_INCONSISTENT",
                    "El stock disponible no cuadra",
                    500,
                )

            updated = await connection.fetchrow(
                f"""
                update app.inventory_reservations
                set status = 'confirmed',
                    order_id = $3
                where tenant_id = $1 and id = $2
                returning {_RESERVATION_COLUMNS}
                """,
                tenant_id,
                reservation_id,
                order_id,
            )
            if updated is None:
                raise AppError("RESERVATION_NOT_FOUND", "Reserva no encontrada", 404)

            await connection.execute(
                """
                insert into app.inventory_movements
                    (tenant_id, variant_id, delta, reason, reference_type, reference_id)
                values ($1, $2, $3, 'sale', 'order', $4)
                """,
                tenant_id,
                row["variant_id"],
                -row["quantity"],
                order_id,
            )
            return _reservation(updated)

    async def expire(self, tenant_id: UUID) -> int:
        async with self._database.tenant_transaction(tenant_id) as connection:
            rows = await connection.fetch(
                """
                select id, variant_id, location_id, quantity
                from app.inventory_reservations
                where tenant_id = $1
                  and status = 'active'
                  and expires_at <= now()
                order by expires_at
                for update skip locked
                """,
                tenant_id,
            )

            for row in rows:
                updated_level = await connection.fetchval(
                    """
                    update app.inventory_levels
                    set reserved = reserved - $3,
                        updated_at = now()
                    where tenant_id = $1
                      and variant_id = $2
                      and location_id = $4
                      and reserved >= $3
                    returning id
                    """,
                    tenant_id,
                    row["variant_id"],
                    row["quantity"],
                    row["location_id"],
                )
                if updated_level is None:
                    raise AppError(
                        "INVENTORY_INCONSISTENT",
                        "El stock reservado no cuadra",
                        500,
                    )
                await connection.execute(
                    "update app.inventory_reservations "
                    "set status = 'expired' where tenant_id = $1 and id = $2",
                    tenant_id,
                    row["id"],
                )
            return len(rows)

    async def _lock(
        self,
        connection: Any,
        tenant_id: UUID,
        reservation_id: UUID,
    ) -> Any:
        row = await connection.fetchrow(
            f"""
            select {_RESERVATION_COLUMNS}
            from app.inventory_reservations
            where tenant_id = $1 and id = $2
            for update
            """,
            tenant_id,
            reservation_id,
        )
        if row is None:
            raise AppError("RESERVATION_NOT_FOUND", "Reserva no encontrada", 404)
        return row


def _reservation(row: Any) -> Reservation:
    return Reservation(
        id=row["id"],
        tenant_id=row["tenant_id"],
        variant_id=row["variant_id"],
        location_id=row["location_id"],
        quantity=row["quantity"],
        status=ReservationStatus(row["status"]),
        expires_at=row["expires_at"],
        cart_id=row["cart_id"],
        order_id=row["order_id"],
    )
