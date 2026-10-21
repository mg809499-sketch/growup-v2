from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_tenant_resolver
from app.core.errors import AppError
from app.domains.tenants.models import (
    Tenant,
    TenantBootstrap,
    TenantSettings,
    TenantStatus,
)
from app.main import app


class FakeResolver:
    def __init__(self, result: TenantBootstrap | None = None) -> None:
        self.result = result
        self.hosts: list[str] = []

    async def bootstrap(self, host: str) -> TenantBootstrap:
        self.hosts.append(host)
        if self.result is None:
            raise AppError("TENANT_NOT_FOUND", "Tienda no encontrada", 404)
        return self.result


def _bootstrap() -> TenantBootstrap:
    return TenantBootstrap(
        tenant=Tenant(
            id=uuid4(),
            slug="ropa",
            name="Ropa",
            status=TenantStatus.ACTIVE,
        ),
        settings=TenantSettings(
            currency="COP",
            locale="es-CO",
            navigation={"main": [{"label": "Inicio", "href": "/"}]},
            seo_defaults={"title": "Ropa"},
            shipping_zones=[{"name": "Nacional", "price_cents": 1200000}],
            contact={"email": "hola@ropa.com"},
            social={"instagram": "https://instagram.com/ropa"},
        ),
    )


def test_bootstrap_uses_storefront_host_header() -> None:
    fake = FakeResolver(_bootstrap())
    app.dependency_overrides[get_tenant_resolver] = lambda: fake
    client = TestClient(app)

    try:
        response = client.get(
            "/v1/storefront/bootstrap",
            headers={"X-Storefront-Host": "ropa.growup.com"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant"]["slug"] == "ropa"
    assert payload["tenant"]["status"] == "active"
    assert payload["settings"]["currency"] == "COP"
    assert payload["settings"]["navigation"]["main"][0]["href"] == "/"
    assert fake.hosts == ["ropa.growup.com"]


def test_bootstrap_falls_back_to_host_header() -> None:
    fake = FakeResolver(_bootstrap())
    app.dependency_overrides[get_tenant_resolver] = lambda: fake
    client = TestClient(app)

    try:
        response = client.get(
            "/v1/storefront/bootstrap",
            headers={"host": "ropa.growup.com"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert fake.hosts == ["ropa.growup.com"]


def test_bootstrap_returns_tenant_not_found() -> None:
    fake = FakeResolver(None)
    app.dependency_overrides[get_tenant_resolver] = lambda: fake
    client = TestClient(app)

    try:
        response = client.get(
            "/v1/storefront/bootstrap",
            headers={"X-Storefront-Host": "nadie.growup.com"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TENANT_NOT_FOUND"
    assert response.json()["error"]["request_id"]
