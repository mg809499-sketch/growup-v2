from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.core.db import Database
from app.core.errors import AppError
from app.domains.catalog.models import ProductInput, VariantInput
from app.domains.catalog.repository import PostgresCatalogRepository
from app.domains.inventory.models import Reservation, ReservationStatus
from app.domains.inventory.repository import PostgresInventoryRepository
from app.domains.inventory.service import InventoryService

TEST_DSN = os.getenv("GROWUP_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DSN,
    reason="GROWUP_TEST_DATABASE_URL no configurada",
)


async def _create_variant(
    database: Database,
    suffix: str,
    *,
    stock: int,
) -> tuple[UUID, UUID]:
    async with database.pool.acquire() as connection:
        tenant_id = await connection.fetchval(
            "select app.create_tenant($1, $2, $3)",
            f"it-inv-{suffix}",
            f"it-inv-{suffix}.growup.com",
            "Inventory Test",
        )

    catalog = PostgresCatalogRepository(database)
    detail = await catalog.create_product(
        tenant_id,
        ProductInput(
            slug=f"producto-{suffix}",
            name="Producto de prueba",
            description=None,
            category_id=None,
            status="active",
            brand=None,
            tags=(),
            variants=(
                VariantInput(
                    sku=f"SKU-{suffix}",
                    name="M",
                    price_cents=1000,
                    stock=stock,
                ),
            ),
        ),
    )
    return tenant_id, detail.variants[0].id


async def _level(database: Database, tenant_id: UUID, variant_id: UUID) -> tuple[int, int]:
    async with database.pool.acquire() as connection:
        row = await connection.fetchrow(
            "select available, reserved from app.inventory_levels "
            "where tenant_id = $1 and variant_id = $2",
            tenant_id,
            variant_id,
        )
    assert row is not None
    return int(row["available"]), int(row["reserved"])


async def test_reserve_release_and_confirm_flow() -> None:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=5)
    await database.connect()
    tenants: list[UUID] = []
    suffix = uuid4().hex[:8]

    try:
        tenant_id, variant_id = await _create_variant(database, suffix, stock=10)
        tenants.append(tenant_id)
        repository = PostgresInventoryRepository(database)
        service = InventoryService(repository, default_ttl_seconds=60)

        reservation = await service.reserve(tenant_id, variant_id, 2)
        assert reservation.status is ReservationStatus.ACTIVE
        assert await _level(database, tenant_id, variant_id) == (10, 2)

        released = await service.release(tenant_id, reservation.id)
        assert released.status is ReservationStatus.RELEASED
        assert await _level(database, tenant_id, variant_id) == (10, 0)

        # Release es idempotente.
        again = await service.release(tenant_id, reservation.id)
        assert again.status is ReservationStatus.RELEASED
        assert await _level(database, tenant_id, variant_id) == (10, 0)

        pending = await service.reserve(tenant_id, variant_id, 3)
        order_id = uuid4()
        confirmed = await service.confirm(tenant_id, pending.id, order_id=order_id)
        assert confirmed.status is ReservationStatus.CONFIRMED
        assert confirmed.order_id == order_id
        assert await _level(database, tenant_id, variant_id) == (7, 0)

        # Confirm es idempotente para la misma orden.
        repeated = await service.confirm(tenant_id, pending.id, order_id=order_id)
        assert repeated.status is ReservationStatus.CONFIRMED
        assert await _level(database, tenant_id, variant_id) == (7, 0)

        with pytest.raises(AppError) as mismatch:
            await service.confirm(tenant_id, pending.id, order_id=uuid4())
        assert mismatch.value.code == "RESERVATION_ORDER_MISMATCH"

        async with database.pool.acquire() as connection:
            movement = await connection.fetchrow(
                "select delta, reason from app.inventory_movements "
                "where tenant_id = $1 and reference_id = $2",
                tenant_id,
                order_id,
            )
        assert movement is not None
        assert movement["delta"] == -3
        assert movement["reason"] == "sale"

        with pytest.raises(AppError) as not_active:
            await service.release(tenant_id, pending.id)
        assert not_active.value.code == "RESERVATION_NOT_ACTIVE"
    finally:
        if tenants:
            async with database.pool.acquire() as connection:
                await connection.execute(
                    "delete from app.tenants where id = any($1::uuid[])",
                    tenants,
                )
        await database.close()


async def test_reserve_rejects_missing_stock_and_variant() -> None:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=5)
    await database.connect()
    tenants: list[UUID] = []
    suffix = uuid4().hex[:8]

    try:
        tenant_id, variant_id = await _create_variant(database, suffix, stock=2)
        tenants.append(tenant_id)
        repository = PostgresInventoryRepository(database)

        with pytest.raises(AppError) as insufficient:
            await repository.reserve(
                tenant_id,
                variant_id=variant_id,
                quantity=3,
                expires_at=datetime.now(UTC) + timedelta(minutes=1),
            )
        assert insufficient.value.code == "INSUFFICIENT_STOCK"
        assert await _level(database, tenant_id, variant_id) == (2, 0)

        with pytest.raises(AppError) as missing:
            await repository.reserve(
                tenant_id,
                variant_id=uuid4(),
                quantity=1,
                expires_at=datetime.now(UTC) + timedelta(minutes=1),
            )
        assert missing.value.code == "VARIANT_NOT_FOUND"
    finally:
        if tenants:
            async with database.pool.acquire() as connection:
                await connection.execute(
                    "delete from app.tenants where id = any($1::uuid[])",
                    tenants,
                )
        await database.close()


async def test_concurrent_reservations_do_not_oversell() -> None:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=10)
    await database.connect()
    tenants: list[UUID] = []
    suffix = uuid4().hex[:8]

    try:
        tenant_id, variant_id = await _create_variant(database, suffix, stock=10)
        tenants.append(tenant_id)
        repository = PostgresInventoryRepository(database)
        expires_at = datetime.now(UTC) + timedelta(minutes=1)

        results = await asyncio.gather(
            *[
                repository.reserve(
                    tenant_id,
                    variant_id=variant_id,
                    quantity=1,
                    expires_at=expires_at,
                )
                for _ in range(40)
            ],
            return_exceptions=True,
        )

        successes = [item for item in results if isinstance(item, Reservation)]
        failures = [
            item
            for item in results
            if isinstance(item, AppError) and item.code == "INSUFFICIENT_STOCK"
        ]
        unexpected = [
            item
            for item in results
            if not isinstance(item, Reservation)
            and not (isinstance(item, AppError) and item.code == "INSUFFICIENT_STOCK")
        ]

        assert len(successes) == 10
        assert len(failures) == 30
        assert unexpected == []
        assert await _level(database, tenant_id, variant_id) == (10, 10)
    finally:
        if tenants:
            async with database.pool.acquire() as connection:
                await connection.execute(
                    "delete from app.tenants where id = any($1::uuid[])",
                    tenants,
                )
        await database.close()


async def test_expire_releases_only_expired_reservations() -> None:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=5)
    await database.connect()
    tenants: list[UUID] = []
    suffix = uuid4().hex[:8]

    try:
        tenant_id, variant_id = await _create_variant(database, suffix, stock=10)
        tenants.append(tenant_id)
        repository = PostgresInventoryRepository(database)

        expired = await repository.reserve(
            tenant_id,
            variant_id=variant_id,
            quantity=2,
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
        )
        active = await repository.reserve(
            tenant_id,
            variant_id=variant_id,
            quantity=1,
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
        )
        assert await _level(database, tenant_id, variant_id) == (10, 3)

        assert await repository.expire(tenant_id) == 1
        assert await _level(database, tenant_id, variant_id) == (10, 1)
        assert await repository.expire(tenant_id) == 0

        expired_after = await repository.get(tenant_id, expired.id)
        active_after = await repository.get(tenant_id, active.id)
        assert expired_after is not None
        assert active_after is not None
        assert expired_after.status is ReservationStatus.EXPIRED
        assert active_after.status is ReservationStatus.ACTIVE
    finally:
        if tenants:
            async with database.pool.acquire() as connection:
                await connection.execute(
                    "delete from app.tenants where id = any($1::uuid[])",
                    tenants,
                )
        await database.close()


async def test_confirm_rejects_expired_reservation() -> None:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=5)
    await database.connect()
    tenants: list[UUID] = []
    suffix = uuid4().hex[:8]

    try:
        tenant_id, variant_id = await _create_variant(database, suffix, stock=10)
        tenants.append(tenant_id)
        repository = PostgresInventoryRepository(database)
        reservation = await repository.reserve(
            tenant_id,
            variant_id=variant_id,
            quantity=2,
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
        )

        with pytest.raises(AppError) as exc_info:
            await repository.confirm(tenant_id, reservation.id, order_id=uuid4())
        assert exc_info.value.code == "RESERVATION_EXPIRED"
        assert await _level(database, tenant_id, variant_id) == (10, 2)

        assert await repository.expire(tenant_id) == 1
        assert await _level(database, tenant_id, variant_id) == (10, 0)
    finally:
        if tenants:
            async with database.pool.acquire() as connection:
                await connection.execute(
                    "delete from app.tenants where id = any($1::uuid[])",
                    tenants,
                )
        await database.close()
