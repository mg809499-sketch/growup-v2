from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Response

from app import runtime
from app.api.deps import get_storefront_tenant
from app.core.errors import AppError
from app.domains.commerce.models import Cart
from app.domains.commerce.schemas import (
    CartAddRequest,
    CartResponse,
    CartUpdateRequest,
    CheckoutRequest,
    CheckoutResponse,
    cart_response,
)
from app.domains.commerce.service import CommerceService
from app.domains.tenants.models import Tenant

router = APIRouter(prefix="/v1/storefront", tags=["storefront-commerce"])

_CART_HEADER = "x-cart-id"


def get_commerce_service() -> CommerceService:
    if runtime.commerce_service is None:
        raise AppError(
            "SERVICE_UNAVAILABLE",
            "El servicio de comercio no está configurado",
            503,
        )
    return runtime.commerce_service


def _parse_cart_id(raw: str | None) -> UUID | None:
    if not raw:
        return None
    try:
        return UUID(raw)
    except ValueError:
        return None


def _with_cart_header(response: Response, cart_id: UUID) -> Response:
    response.headers["X-Cart-ID"] = str(cart_id)
    response.headers["Cache-Control"] = "no-store"
    return response


@router.get("/cart", response_model=CartResponse)
async def get_cart(
    tenant: Annotated[Tenant, Depends(get_storefront_tenant)],
    service: Annotated[CommerceService, Depends(get_commerce_service)],
    response: Response,
    x_cart_id: Annotated[str | None, Header(alias="x-cart-id")] = None,
) -> CartResponse:
    cart = await service.get_or_create_cart(tenant.id, _parse_cart_id(x_cart_id))
    return _cart_response_with_header(response, cart)


@router.post("/cart/items", response_model=CartResponse)
async def add_cart_item(
    tenant: Annotated[Tenant, Depends(get_storefront_tenant)],
    service: Annotated[CommerceService, Depends(get_commerce_service)],
    response: Response,
    body: CartAddRequest,
    x_cart_id: Annotated[str | None, Header(alias="x-cart-id")] = None,
) -> CartResponse:
    cart = await service.get_or_create_cart(tenant.id, _parse_cart_id(x_cart_id))
    updated = await service.add_item(
        tenant.id, cart.id, variant_id=body.variant_id, quantity=body.quantity
    )
    return _cart_response_with_header(response, updated)


@router.patch("/cart/items", response_model=CartResponse)
async def update_cart_item(
    tenant: Annotated[Tenant, Depends(get_storefront_tenant)],
    service: Annotated[CommerceService, Depends(get_commerce_service)],
    response: Response,
    body: CartUpdateRequest,
    x_cart_id: Annotated[str | None, Header(alias="x-cart-id")] = None,
) -> CartResponse:
    cart_id = _parse_cart_id(x_cart_id)
    if cart_id is None:
        raise AppError("CART_NOT_FOUND", "El carrito no existe o expiró", 404)
    cart = await service.set_item_quantity(
        tenant.id, cart_id, variant_id=body.variant_id, quantity=body.quantity
    )
    return _cart_response_with_header(response, cart)


@router.post("/checkout", response_model=CheckoutResponse)
async def checkout(
    tenant: Annotated[Tenant, Depends(get_storefront_tenant)],
    service: Annotated[CommerceService, Depends(get_commerce_service)],
    response: Response,
    body: CheckoutRequest,
    x_cart_id: Annotated[str | None, Header(alias="x-cart-id")] = None,
) -> CheckoutResponse:
    cart_id = _parse_cart_id(x_cart_id)
    if cart_id is None:
        raise AppError("CART_NOT_FOUND", "El carrito no existe o expiró", 404)

    # Zonas de envío del tenant (settings) con fallback a las del plan MVP.
    zones: list[object] = []
    if runtime.tenant_repository is not None:
        settings_model = await runtime.tenant_repository.get_settings(tenant.id)
        zones = list(getattr(settings_model, "shipping_zones", None) or [])

    redirect_base = body.redirect_base_url
    if not redirect_base:
        raise AppError(
            "VALIDATION_ERROR",
            "redirect_base_url es requerido para volver del checkout",
            422,
        )
    result = await service.checkout(
        tenant.id,
        cart_id=cart_id,
        email=body.email,
        shipping_zone=body.shipping_zone,
        settings_zones=zones,
        shipping=body.shipping.model_dump(),
        redirect_base_url=redirect_base,
    )
    response.headers["X-Cart-ID"] = "converted"
    response.headers["Cache-Control"] = "no-store"
    return CheckoutResponse(**result)


def _cart_response_with_header(response: Response, cart: Cart) -> CartResponse:
    payload = cart_response(cart)
    response.headers["X-Cart-ID"] = str(cart.id)
    response.headers["Cache-Control"] = "no-store"
    return payload
