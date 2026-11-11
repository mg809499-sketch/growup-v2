from __future__ import annotations

from typing import Any
from uuid import UUID

from app.core.config import settings
from app.core.crypto import decrypt_secret
from app.core.errors import AppError
from app.domains.commerce.models import Cart, Order, OrderItem, OrderStatus
from app.domains.commerce.repository import (
    PostgresCommerceRepository,
    wompi_event_checksum,
    wompi_integrity_signature,
)

DEFAULT_SHIPPING_ZONES = [
    {"code": "bogota", "name": "Bogotá D.C.", "price_cents": 800_000},
    {"code": "resto", "name": "Resto del país", "price_cents": 1_500_000},
]
TAX_RATE_BPS = 1900  # IVA 19% incluido en precios

_TRANSITIONS = {
    "paid": {"preparing", "cancelled"},
    "preparing": {"shipped", "cancelled"},
    "shipped": {"delivered"},
    "delivered": set(),
    "pending": {"failed", "expired", "cancelled"},
    "failed": set(),
    "expired": set(),
    "cancelled": set(),
    "refund_pending": {"refunded", "delivered"},
    "refunded": set(),
}


class CommerceService:
    def __init__(self, repository: PostgresCommerceRepository) -> None:
        self._repository = repository

    # ---------- Carrito ----------
    async def get_or_create_cart(self, tenant_id: UUID, cart_id: UUID | None) -> Cart:
        if cart_id is not None:
            cart = await self._repository.get_cart(tenant_id, cart_id)
            if cart is not None:
                return cart
        new_id = await self._repository.create_cart(tenant_id)
        cart = await self._repository.get_cart(tenant_id, new_id)
        assert cart is not None
        return cart

    async def get_cart(self, tenant_id: UUID, cart_id: UUID) -> Cart:
        cart = await self._repository.get_cart(tenant_id, cart_id)
        if cart is None:
            raise AppError("CART_NOT_FOUND", "El carrito no existe o expiró", 404)
        return cart

    async def add_item(
        self, tenant_id: UUID, cart_id: UUID, *, variant_id: UUID, quantity: int
    ) -> Cart:
        await self._repository.add_item(
            tenant_id, cart_id=cart_id, variant_id=variant_id, quantity=quantity
        )
        return await self.get_cart(tenant_id, cart_id)

    async def set_item_quantity(
        self, tenant_id: UUID, cart_id: UUID, *, variant_id: UUID, quantity: int
    ) -> Cart:
        await self._repository.set_item_quantity(
            tenant_id, cart_id=cart_id, variant_id=variant_id, quantity=quantity
        )
        return await self.get_cart(tenant_id, cart_id)

    # ---------- Checkout ----------
    def shipping_zones(self, settings_zones: list[Any]) -> list[dict[str, Any]]:
        if settings_zones:
            return settings_zones
        return list(DEFAULT_SHIPPING_ZONES)

    def zone_price(self, zone_code: str, settings_zones: list[Any]) -> int:
        for zone in self.shipping_zones(settings_zones):
            if str(zone.get("code")) == zone_code:
                price = int(zone.get("price_cents", 0))
                if price < 0:
                    raise AppError("SHIPPING_ZONE_INVALID", "Tarifa de envío inválida", 400)
                return price
        raise AppError("SHIPPING_ZONE_INVALID", "Zona de envío desconocida", 422)

    async def checkout(
        self,
        tenant_id: UUID,
        *,
        cart_id: UUID,
        email: str,
        shipping_zone: str,
        settings_zones: list[Any],
        shipping: dict[str, Any],
        redirect_base_url: str,
    ) -> dict[str, Any]:
        account = await self._repository.get_payment_account(tenant_id)
        if account is None:
            raise AppError(
                "PAYMENT_ACCOUNT_NOT_CONFIGURED",
                "Este comercio aún no conectó su cuenta de pagos",
                409,
            )

        shipping_cents = self.zone_price(shipping_zone, settings_zones)
        order = await self._repository.create_order_from_cart(
            tenant_id,
            cart_id=cart_id,
            email=email,
            shipping_zone=shipping_zone,
            shipping_cents=shipping_cents,
            tax_rate_bps=TAX_RATE_BPS,
            shipping=shipping,
        )

        integrity_key = decrypt_secret(account.integrity_key_encrypted)
        reference = f"ord_{order.id}"
        signature = wompi_integrity_signature(
            reference=reference,
            amount_in_cents=order.total_cents,
            currency="COP",
            integrity_key=integrity_key,
        )
        query = (
            f"public-key={account.public_key}"
            f"&currency=COP&amount-in-cents={order.total_cents}"
            f"&reference={reference}"
            f"&signature:integrity={signature}"
            f"&redirect-url={redirect_base_url}/checkout/retorno"
            f"&expiration-time=30m"
        )
        return {
            "order_id": str(order.id),
            "reference": reference,
            "total_cents": order.total_cents,
            "amount_in_cents": order.total_cents,
            "currency": "COP",
            "wompi_url": f"{settings.wompi_base_url}?{query}",
        }

    async def upsert_payment_account(
        self,
        tenant_id: UUID,
        *,
        public_key: str,
        events_secret: str,
        integrity_key: str,
        mode: str,
    ) -> None:
        await self._repository.upsert_payment_account(
            tenant_id,
            public_key=public_key,
            events_secret=events_secret,
            integrity_key=integrity_key,
            mode=mode,
        )

    # ---------- Órdenes (admin) ----------
    async def list_orders(
        self, tenant_id: UUID, *, limit: int, offset: int
    ) -> tuple[list[Order], int]:
        return await self._repository.list_orders(tenant_id, limit=limit, offset=offset)

    async def get_order(
        self, tenant_id: UUID, order_id: UUID
    ) -> tuple[Order, list[OrderItem]]:
        order = await self._repository.get_order(tenant_id, order_id)
        if order is None:
            raise AppError("ORDER_NOT_FOUND", "La orden no existe", 404)
        items = await self._repository.get_order_items(tenant_id, order_id)
        return order, items

    async def transition_order(
        self, tenant_id: UUID, order_id: UUID, *, target: OrderStatus
    ) -> Order:
        order = await self._repository.get_order(tenant_id, order_id)
        if order is None:
            raise AppError("ORDER_NOT_FOUND", "La orden no existe", 404)
        allowed = _TRANSITIONS.get(order.status.value, set())
        if target.value not in allowed:
            raise AppError(
                "ORDER_TRANSITION_INVALID",
                f"No se puede pasar de {order.status.value} a {target.value}",
                409,
            )
        # Transición genérica vía update; la base fuerza el rango de estados válidos.
        await self._repository.set_order_status(tenant_id, order_id, target.value)
        updated = await self._repository.get_order(tenant_id, order_id)
        assert updated is not None
        return updated

    # ---------- Webhook Wompi ----------
    async def process_wompi_event(self, event: dict[str, Any]) -> dict[str, str]:
        transaction_id = str(event.get("id") or event.get("transaction", {}).get("id") or "")
        if not transaction_id:
            raise AppError("WOMPI_EVENT_INVALID", "Evento sin identificador", 400)

        data = event.get("data", {})
        transaction = data.get("transaction", data if isinstance(data, dict) else {})
        reference = str(transaction.get("reference", ""))
        status = str(transaction.get("status", "")).lower()
        method = transaction.get("payment_method_type")

        correlation = await self._repository.get_payment_by_reference(reference)
        if correlation is None:
            # Evento de otra referencia o aún no registrada: se contesta 200 y se ignora.
            recorded = await self._repository.record_webhook_event(
                provider="wompi",
                event_id=transaction_id,
                tenant_id=None,
                payload=event,
            )
            return {"status": "ignored" if not recorded else "ignored"}

        tenant_id, order_id, _ = correlation

        account = await self._repository.get_payment_account(tenant_id)
        if account is None:
            raise AppError("PAYMENT_ACCOUNT_NOT_CONFIGURED", "Cuenta de pago no configurada", 409)

        events_secret = decrypt_secret(account.events_secret_encrypted)
        expected = wompi_event_checksum(event, events_secret)
        provided = str(
            event.get("signature", {}).get("checksum", "")
            or event.get("signature", {}).get("checksum-sha256", "")
        ).lower()
        if not expected or provided != expected:
            raise AppError("WOMPI_SIGNATURE_INVALID", "Firma del webhook inválida", 401)

        recorded = await self._repository.record_webhook_event(
            provider="wompi",
            event_id=transaction_id,
            tenant_id=tenant_id,
            payload=event,
        )
        if not recorded:
            return {"status": "duplicate"}

        result = (
            "approved" if status == "approved"
            else "voided" if status in ("voided", "void")
            else "declined" if status in ("declined",)
            else "error"
        )
        await self._repository.mark_payment_result(
            tenant_id,
            reference=reference,
            order_id=order_id,
            result=result,
            method=str(method) if method else None,
        )
        return {"status": "processed"}
