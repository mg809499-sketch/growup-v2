from __future__ import annotations

import os
from uuid import UUID, uuid4

import pytest

from app.core.db import Database
from app.core.errors import AppError
from app.domains.commerce.models import OrderStatus
from app.domains.commerce.repository import PostgresCommerceRepository
from app.domains.commerce.service import CommerceService

TEST_DSN = os.getenv("GROWUP_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DSN,
    reason="GROWUP_TEST_DATABASE_URL no configurada",
)


async def _seed_catalog(database: Database, tenant_id: UUID) -> UUID:
    async with database.pool.acquire() as connection:
        product_id = await connection.fetchval(
            """
            insert into app.products (tenant_id, slug, name, status)
            values ($1, $2, $3, 'active') returning id
            """,
            tenant_id,
            f"it-prod-{uuid4().hex[:6]}",
            "Producto Integración",
        )
        variant_id = await connection.fetchval(
            """
            insert into app.product_variants (tenant_id, product_id, sku, name, price_cents)
            values ($1, $2, $3, 'Base', 99000) returning id
            """,
            tenant_id,
            product_id,
            f"SKU-{uuid4().hex[:6]}",
        )
    return variant_id  # type: ignore[return-value]


async def test_cart_to_checkout_and_webhook_flow() -> None:
    assert TEST_DSN is not None
    database = Database(TEST_DSN, min_size=1, max_size=4)
    await database.connect()
    created_tenant: list[UUID] = []
    suffix = uuid4().hex[:8]
    slug = f"it-commerce-{suffix}"

    try:
        from app.domains.tenants.repository import PostgresTenantRepository

        tenant_repository = PostgresTenantRepository(database)
        tenant_id = await tenant_repository.create_tenant(
            slug=slug,
            host=f"{slug}.growup.com",
            name="Commerce Test",
        )
        created_tenant.append(tenant_id)

        variant_id = await _seed_catalog(database, tenant_id)

        repository = PostgresCommerceRepository(database)
        service = CommerceService(repository)

        # Conectar cuenta Wompi sandbox del tenant
        await service.upsert_payment_account(
            tenant_id,
            public_key="pub_test_1234567890abcdef",
            events_secret="events_secret_de_integracion",
            integrity_key="integrity_key_de_integracion",
            mode="sandbox",
        )

        # Carrito guest → agregar item
        cart = await service.get_or_create_cart(tenant_id, None)
        cart = await service.add_item(tenant_id, cart.id, variant_id=variant_id, quantity=2)
        assert cart.subtotal_cents == 198_000

        # Checkout → orden pending con enlace Wompi firmado
        checkout = await service.checkout(
            tenant_id,
            cart_id=cart.id,
            email="comprador@example.com",
            shipping_zone="bogota",
            settings_zones=[],
            shipping={
                "name": "Comprador Prueba",
                "line1": "Calle 123",
                "city": "Bogotá",
                "state": "DC",
            },
            redirect_base_url="https://ropa.growup.test",
        )
        assert checkout["total_cents"] == 198_000 + 800_000
        assert checkout["reference"].startswith("ord_")
        assert "signature:integrity=" in checkout["wompi_url"]
        assert "amount-in-cents=998000" in checkout["wompi_url"]

        # Checkout upsertó al comprador y enlazó cart/order
        async with database.pool.acquire() as connection:
            customer = await connection.fetchrow(
                """select id, email, name, phone from app.customers
                    where tenant_id = $1 and lower(email) = lower($2)""",
                tenant_id,
                "comprador@example.com",
            )
            assert customer is not None, "customers no se materializó en el checkout"
            assert customer["name"] == "Comprador Prueba"
            assert customer["phone"] is None
            order_row = await connection.fetchrow(
                "select customer_id from app.orders where id = $1",
                UUID(checkout["order_id"]),
            )
            assert order_row["customer_id"] == customer["id"]
            cart_row = await connection.fetchrow(
                "select customer_id from app.carts where id = $1", cart.id
            )
            assert cart_row["customer_id"] == customer["id"]

        # Webhook: firma inválida → 401
        invalid_event_id = f"evt-inv-{uuid4().hex[:8]}"
        with pytest.raises(AppError) as excinfo:
            await service.process_wompi_event(
                {
                    "id": invalid_event_id,
                    "data": {"transaction": {"id": "tx-1", "reference": checkout["reference"],
                                             "status": "APPROVED", "payment_method_type": "CARD"}},
                    "signature": {"properties": ["transaction.id", "transaction.status"],
                                  "timestamp": 1700000000, "checksum": "deadbeef"},
                }
            )
        assert excinfo.value.code == "WOMPI_SIGNATURE_INVALID"

        # Webhook: firma válida → orden paid
        import hashlib

        event = {
            "id": f"evt-ok-{uuid4().hex[:8]}",
            "data": {
                "transaction": {
                    "id": "tx-1",
                    "reference": checkout["reference"],
                    "status": "APPROVED",
                    "payment_method_type": "CARD",
                }
            },
            "signature": {
                "properties": ["transaction.id", "transaction.status"],
                "timestamp": 1700000000,
            },
        }
        payload = "tx-1APPROVED1700000000events_secret_de_integracion"
        event["signature"]["checksum"] = hashlib.sha256(payload.encode()).hexdigest()

        result = await service.process_wompi_event(event)
        assert result["status"] == "processed"

        order_id = UUID(checkout["order_id"])
        order, items = await service.get_order(tenant_id, order_id)
        assert order.status == OrderStatus.PAID
        assert items[0].unit_price_cents == 99_000
        assert order.total_cents == 998_000

        # Webhook duplicado → idempotente
        duplicate = await service.process_wompi_event(event)
        assert duplicate["status"] == "duplicate"
    finally:
        if created_tenant:
            async with database.pool.acquire() as connection:
                await connection.execute(
                    "delete from app.tenants where id = any($1::uuid[])", created_tenant
                )
        await database.close()
