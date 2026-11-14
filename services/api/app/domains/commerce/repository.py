from __future__ import annotations

import hashlib
import json
from typing import Any, cast
from uuid import UUID

import asyncpg  # type: ignore[import-untyped]

from app.core.db import Database
from app.core.errors import AppError
from app.domains.commerce.models import (
    Cart,
    CartItem,
    Order,
    OrderItem,
    OrderStatus,
    TenantPaymentAccount,
)

_CART_QTY_MAX = 50


class PostgresCommerceRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    # ---------- Carrito ----------
    async def upsert_customer(
        self,
        tenant_id: UUID,
        *,
        email: str,
        name: str | None,
        phone: str | None,
    ) -> UUID:
        async with self._database.tenant_transaction(tenant_id) as connection:
            row = await connection.fetchrow(
                """
                insert into app.customers (tenant_id, email, name, phone)
                values ($1, lower(btrim($2)), $3, $4)
                on conflict (tenant_id, lower(email)) do update
                    set name = coalesce(nullif(btrim(excluded.name), ''), customers.name),
                        phone = coalesce(nullif(btrim(excluded.phone), ''), customers.phone),
                        updated_at = now()
                returning id
                """,
                tenant_id,
                email,
                name,
                phone,
            )
        if row is None:
            raise AppError("CUSTOMER_UPSERT_FAILED", "No se pudo crear el comprador", 500)
        return cast(UUID, row["id"])

    async def assign_customer_to_cart(
        self,
        tenant_id: UUID,
        *,
        cart_id: UUID,
        customer_id: UUID,
    ) -> None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            result = await connection.execute(
                """
                update app.carts
                   set customer_id = $3, updated_at = now()
                 where tenant_id = $1 and id = $2 and status = 'open' and expires_at > now()
                """,
                tenant_id,
                cart_id,
                customer_id,
            )
        if result != "UPDATE 1":
            raise AppError("CART_NOT_FOUND", "El carrito no existe o expiró", 404)

    async def create_cart(self, tenant_id: UUID) -> UUID:
        async with self._database.tenant_transaction(tenant_id) as connection:
            cart_id = await connection.fetchval(
                "insert into app.carts (tenant_id) values ($1) returning id", tenant_id
            )
        if not isinstance(cart_id, UUID):
            raise AppError("CART_CREATE_FAILED", "No se pudo crear el carrito", 500)
        return cart_id

    async def get_cart(self, tenant_id: UUID, cart_id: UUID) -> Cart | None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            cart = await connection.fetchrow(
                """
                select id, tenant_id, status, expires_at
                from app.carts
                where tenant_id = $1 and id = $2 and status = 'open' and expires_at > now()
                """,
                tenant_id,
                cart_id,
            )
            if cart is None:
                return None
            items = await connection.fetch(
                """
                select ci.id, ci.variant_id, ci.quantity,
                       p.name as product_name, v.sku,
                       v.name as variant_title, v.price_cents
                from app.cart_items ci
                join app.product_variants v
                  on v.tenant_id = ci.tenant_id and v.id = ci.variant_id and v.is_active
                join app.products p
                  on p.tenant_id = v.tenant_id and p.id = v.product_id and p.status = 'active'
                where ci.tenant_id = $1 and ci.cart_id = $2
                order by ci.created_at
                """,
                tenant_id,
                cart_id,
            )
        cart_items = tuple(
            CartItem(
                id=row["id"],
                variant_id=row["variant_id"],
                product_name=row["product_name"],
                variant_sku=row["sku"],
                variant_title=row["variant_title"],
                unit_price_cents=row["price_cents"],
                quantity=row["quantity"],
            )
            for row in items
        )
        subtotal = sum(item.unit_price_cents * item.quantity for item in cart_items)
        return Cart(
            id=cart["id"],
            tenant_id=cart["tenant_id"],
            status=cart["status"],
            items=cart_items,
            subtotal_cents=subtotal,
            expires_at=cart["expires_at"],
        )

    async def add_item(
        self, tenant_id: UUID, *, cart_id: UUID, variant_id: UUID, quantity: int
    ) -> None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            variant = await connection.fetchrow(
                """
                select v.id
                from app.product_variants v
                join app.products p
                  on p.tenant_id = v.tenant_id and p.id = v.product_id and p.status = 'active'
                where v.tenant_id = $1 and v.id = $2 and v.is_active
                """,
                tenant_id,
                variant_id,
            )
            if variant is None:
                raise AppError("VARIANT_NOT_FOUND", "La variante no existe o no está activa", 404)
            existing = await connection.fetchrow(
                """
                select id, quantity from app.cart_items
                where tenant_id = $1 and cart_id = $2 and variant_id = $3
                """,
                tenant_id,
                cart_id,
                variant_id,
            )
            new_quantity = quantity + (existing["quantity"] if existing else 0)
            if new_quantity < 1 or new_quantity > _CART_QTY_MAX:
                raise AppError("QUANTITY_INVALID", "Cantidad fuera de rango", 422)
            await connection.execute(
                """
                insert into app.cart_items (tenant_id, cart_id, variant_id, quantity)
                values ($1, $2, $3, $4)
                on conflict (tenant_id, cart_id, variant_id)
                do update set quantity = $4, updated_at = now()
                """,
                tenant_id,
                cart_id,
                variant_id,
                new_quantity,
            )
            await connection.execute(
                "update app.carts set updated_at = now() where tenant_id = $1 and id = $2",
                tenant_id,
                cart_id,
            )

    async def set_item_quantity(
        self, tenant_id: UUID, *, cart_id: UUID, variant_id: UUID, quantity: int
    ) -> None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            if quantity <= 0:
                await connection.execute(
                    """
                    delete from app.cart_items
                    where tenant_id = $1 and cart_id = $2 and variant_id = $3
                    """,
                    tenant_id,
                    cart_id,
                    variant_id,
                )
                return
            if quantity > _CART_QTY_MAX:
                raise AppError("QUANTITY_INVALID", "Cantidad fuera de rango", 422)
            result = await connection.execute(
                """
                update app.cart_items set quantity = $4, updated_at = now()
                where tenant_id = $1 and cart_id = $2 and variant_id = $3 and quantity >= 0
                """,
                tenant_id,
                cart_id,
                variant_id,
                quantity,
            )
            if result == "UPDATE 0":
                raise AppError("CART_ITEM_NOT_FOUND", "El producto no está en el carrito", 404)

    async def clear_cart(self, tenant_id: UUID, cart_id: UUID) -> None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            await connection.execute(
                "delete from app.cart_items where tenant_id = $1 and cart_id = $2",
                tenant_id,
                cart_id,
            )

    # ---------- Checkout / órdenes ----------
    async def create_order_from_cart(
        self,
        tenant_id: UUID,
        *,
        cart_id: UUID,
        email: str,
        shipping_zone: str,
        shipping_cents: int,
        tax_rate_bps: int,
        shipping: dict[str, Any],
        customer_id: UUID | None = None,
    ) -> Order:
        async with self._database.tenant_transaction(tenant_id) as connection:
            async with connection.transaction():
                cart = await connection.fetchrow(
                    """
                    select id from app.carts
                    where tenant_id = $1 and id = $2 and status = 'open' and expires_at > now()
                    for update
                    """,
                    tenant_id,
                    cart_id,
                )
                if cart is None:
                    raise AppError("CART_NOT_FOUND", "El carrito no existe o expiró", 404)
                items = await connection.fetch(
                    """
                    select ci.variant_id, ci.quantity, p.name as product_name,
                           v.sku, v.name as variant_title, v.price_cents
                    from app.cart_items ci
                    join app.product_variants v
                      on v.tenant_id = ci.tenant_id and v.id = ci.variant_id and v.is_active
                    join app.products p
                      on p.tenant_id = v.tenant_id and p.id = v.product_id and p.status = 'active'
                    where ci.tenant_id = $1 and ci.cart_id = $2
                    for update of v
                    """,
                    tenant_id,
                    cart_id,
                )
                if not items:
                    raise AppError("CART_EMPTY", "El carrito está vacío", 400)

                subtotal = 0
                for row in items:
                    subtotal += int(row["price_cents"]) * int(row["quantity"])

                # IVA incluido en precios: el IVA del subtotal se deriva hacia atrás.
                tax_cents = subtotal - (subtotal * 10_000) // (10_000 + tax_rate_bps)
                total = subtotal + shipping_cents

                order_id = await connection.fetchval(
                    """
                    insert into app.orders (
                        tenant_id, cart_id, customer_id, email, status,
                        subtotal_cents, tax_cents, shipping_cents, total_cents, tax_rate_bps,
                        shipping_zone, shipping_name, shipping_line1, shipping_line2,
                        shipping_city, shipping_state, shipping_postal_code, shipping_country
                    ) values (
                        $1, $2, $3, $4, 'pending',
                        $5, $6, $7, $8, $9,
                        $10, $11, $12, $13, $14, $15, $16, $17
                    ) returning id
                    """,
                    tenant_id,
                    cart_id,
                    customer_id,
                    email.lower(),
                    subtotal,
                    tax_cents,
                    shipping_cents,
                    total,
                    tax_rate_bps,
                    shipping_zone,
                    shipping.get("name"),
                    shipping.get("line1"),
                    shipping.get("line2"),
                    shipping.get("city"),
                    shipping.get("state"),
                    shipping.get("postal_code"),
                    shipping.get("country", "CO"),
                )
                for row in items:
                    await connection.execute(
                        """
                        insert into app.order_items (
                            tenant_id, order_id, variant_id, product_name,
                            variant_sku, variant_title, quantity, unit_price_cents
                        ) values ($1, $2, $3, $4, $5, $6, $7, $8)
                        """,
                        tenant_id,
                        order_id,
                        row["variant_id"],
                        row["product_name"],
                        row["sku"],
                        row["variant_title"],
                        row["quantity"],
                        row["price_cents"],
                    )
                payment_reference = f"ord_{order_id}"
                await connection.execute(
                    """
                    insert into app.payments (
                        tenant_id, order_id, provider, provider_reference, status, amount_cents
                    ) values ($1, $2, 'wompi', $3, 'pending', $4)
                    """,
                    tenant_id,
                    order_id,
                    payment_reference,
                    total,
                )
                await connection.execute(
                    """
                    update app.carts set status = 'converted', updated_at = now()
                    where tenant_id = $1 and id = $2
                    """,
                    tenant_id,
                    cart_id,
                )
            row = await connection.fetchrow(
                """
                select id, tenant_id, email, status, subtotal_cents, tax_cents,
                       shipping_cents, total_cents, tax_rate_bps, shipping_zone,
                       created_at, updated_at
                from app.orders where tenant_id = $1 and id = $2
                """,
                tenant_id,
                order_id,
            )
        return _order(row)

    async def list_orders(
        self, tenant_id: UUID, *, limit: int, offset: int
    ) -> tuple[list[Order], int]:
        async with self._database.tenant_transaction(tenant_id) as connection:
            total = await connection.fetchval(
                "select count(*) from app.orders where tenant_id = $1", tenant_id
            )
            rows = await connection.fetch(
                """
                select id, tenant_id, email, status, subtotal_cents, tax_cents,
                       shipping_cents, total_cents, tax_rate_bps, shipping_zone,
                       created_at, updated_at
                from app.orders
                where tenant_id = $1
                order by created_at desc
                limit $2 offset $3
                """,
                tenant_id,
                limit,
                offset,
            )
        return [_order(row) for row in rows], int(total or 0)

    async def get_order(self, tenant_id: UUID, order_id: UUID) -> Order | None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            row = await connection.fetchrow(
                """
                select id, tenant_id, email, status, subtotal_cents, tax_cents,
                       shipping_cents, total_cents, tax_rate_bps, shipping_zone,
                       created_at, updated_at
                from app.orders where tenant_id = $1 and id = $2
                """,
                tenant_id,
                order_id,
            )
        return _order(row) if row is not None else None

    async def get_order_items(self, tenant_id: UUID, order_id: UUID) -> list[OrderItem]:
        async with self._database.tenant_transaction(tenant_id) as connection:
            rows = await connection.fetch(
                """
                select id, order_id, variant_id, product_name, variant_sku,
                       variant_title, quantity, unit_price_cents
                from app.order_items
                where tenant_id = $1 and order_id = $2
                order by created_at
                """,
                tenant_id,
                order_id,
            )
        return [
            OrderItem(
                id=row["id"],
                order_id=row["order_id"],
                variant_id=row["variant_id"],
                product_name=row["product_name"],
                variant_sku=row["variant_sku"],
                variant_title=row["variant_title"],
                unit_price_cents=row["unit_price_cents"],
                quantity=row["quantity"],
            )
            for row in rows
        ]

    async def set_order_status(self, tenant_id: UUID, order_id: UUID, status: str) -> None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            await connection.execute(
                """
                update app.orders set status = $3, updated_at = now()
                where tenant_id = $1 and id = $2
                """,
                tenant_id,
                order_id,
                status,
            )

    async def get_payment_account(self, tenant_id: UUID) -> TenantPaymentAccount | None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            row = await connection.fetchrow(
                """
                select tenant_id, provider, public_key,
                       events_secret_encrypted, integrity_key_encrypted, mode
                from app.tenant_payment_accounts where tenant_id = $1
                """,
                tenant_id,
            )
        if row is None:
            return None
        return TenantPaymentAccount(
            tenant_id=row["tenant_id"],
            provider=row["provider"],
            public_key=row["public_key"],
            events_secret_encrypted=row["events_secret_encrypted"],
            integrity_key_encrypted=row["integrity_key_encrypted"],
            mode=row["mode"],
        )

    async def upsert_payment_account(
        self,
        tenant_id: UUID,
        *,
        public_key: str,
        events_secret: str,
        integrity_key: str,
        mode: str,
    ) -> None:
        from app.core.crypto import encrypt_secret

        async with self._database.tenant_transaction(tenant_id) as connection:
            await connection.execute(
                """
                insert into app.tenant_payment_accounts
                    (tenant_id, provider, public_key, events_secret_encrypted,
                     integrity_key_encrypted, mode, updated_at)
                values ($1, 'wompi', $2, $3, $4, $5, now())
                on conflict (tenant_id) do update
                set public_key = excluded.public_key,
                    events_secret_encrypted = excluded.events_secret_encrypted,
                    integrity_key_encrypted = excluded.integrity_key_encrypted,
                    mode = excluded.mode,
                    updated_at = now()
                """,
                tenant_id,
                public_key,
                encrypt_secret(events_secret),
                encrypt_secret(integrity_key),
                mode,
            )

    # ---------- Webhooks ----------
    async def record_webhook_event(
        self, *, provider: str, event_id: str, tenant_id: UUID | None, payload: dict[str, Any]
    ) -> bool:
        if tenant_id is not None:
            manager = self._database.tenant_transaction(tenant_id)
        else:
            manager = self._database.public_transaction()
        try:
            async with manager as connection:
                await connection.execute(
                    """
                    insert into app.webhook_events (provider, event_id, tenant_id, payload)
                    values ($1, $2, $3, $4::jsonb)
                    """,
                    provider,
                    event_id,
                    tenant_id,
                    json.dumps(payload),
                )
                return True
        except asyncpg.UniqueViolationError:
            return False

    async def get_payment_by_reference(
        self, reference: str
    ) -> tuple[UUID, UUID, str] | None:
        """(tenant_id, order_id, reference) para uso interno del webhook."""
        async with self._database.public_transaction() as connection:
            row = await connection.fetchrow(
                "select tenant_id, order_id, provider_reference from app.payment_by_reference($1)",
                reference,
            )
        if row is None:
            return None
        return row["tenant_id"], row["order_id"], row["provider_reference"]

    async def mark_payment_result(
        self,
        tenant_id: UUID,
        *,
        reference: str,
        order_id: UUID,
        result: str,
        method: str | None,
    ) -> None:
        async with self._database.tenant_transaction(tenant_id) as connection:
            await connection.execute(
                """
                update app.payments
                set status = $3, method = coalesce($4, method), updated_at = now()
                where tenant_id = $1 and provider_reference = $2
                """,
                tenant_id,
                reference,
                {
                    "approved": "approved",
                    "declined": "declined",
                    "voided": "voided",
                    "error": "error",
                }[result],
                method,
            )
            order_status = (
                "paid" if result == "approved"
                else ("failed" if result in ("declined", "error") else "expired")
            )
            await connection.execute(
                """
                update app.orders set status = $3, updated_at = now()
                where tenant_id = $1 and id = $2
                """,
                tenant_id,
                order_id,
                order_status,
            )


def _order(row: Any) -> Order:
    return Order(
        id=row["id"],
        tenant_id=row["tenant_id"],
        email=row["email"],
        status=OrderStatus(row["status"]),
        subtotal_cents=row["subtotal_cents"],
        tax_cents=row["tax_cents"],
        shipping_cents=row["shipping_cents"],
        total_cents=row["total_cents"],
        tax_rate_bps=row["tax_rate_bps"],
        shipping_zone=row["shipping_zone"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def wompi_integrity_signature(
    *, reference: str, amount_in_cents: int, currency: str, integrity_key: str
) -> str:
    digest = hashlib.sha256(
        f"{reference}{amount_in_cents}{currency}{integrity_key}".encode()
    )
    return digest.hexdigest()


def wompi_event_checksum(event: dict[str, Any], events_secret: str) -> str:
    """Checksum de webhooks (esquema público de Wompi):

    concat(valores de signature.properties en orden, signature.timestamp,
    events_secret) → SHA256 hex.

    Fail-closed: ante cualquier entrada malformada devuelve "" (el emisor
    verifica firma; "" nunca coincide con un checksum real).
    """
    if not isinstance(event, dict):
        return ""
    signature = event.get("signature")
    if not isinstance(signature, dict):
        return ""
    properties = signature.get("properties")
    if not isinstance(properties, list):
        return ""
    timestamp = signature.get("timestamp")
    data = event.get("data")
    if timestamp is None or not isinstance(data, dict):
        return ""
    values: list[str] = []
    for prop in properties:
        value: Any = data
        for part in str(prop).split("."):
            if not isinstance(value, dict):
                value = None
                break
            value = value.get(part)
        values.append("" if value is None else str(value))
    payload = "".join(values) + str(timestamp) + events_secret
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
