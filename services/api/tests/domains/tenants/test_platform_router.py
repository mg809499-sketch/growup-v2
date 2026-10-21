from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_admin_context, get_platform_tenant_service
from app.core.errors import AppError
from app.domains.identity.models import Actor, RequestContext, Role
from app.domains.identity.permissions import permissions_for
from app.domains.tenants.models import Tenant, TenantStatus
from app.main import app


class FakePlatformTenantService:
    def __init__(self, *, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[dict[str, object]] = []

    async def create_tenant(self, **kwargs: object) -> Tenant:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return Tenant(
            id=uuid4(),
            slug=str(kwargs["slug"]),
            name=str(kwargs["name"]),
            status=TenantStatus.TRIALING,
        )


def _context(role: Role) -> RequestContext:
    tenant_id = None if role is Role.PLATFORM_ADMIN else uuid4()
    actor = Actor(
        user_id=uuid4(),
        tenant_id=tenant_id,
        role=role,
        email="user@example.com",
    )
    return RequestContext(
        tenant_id=tenant_id,
        actor=actor,
        permissions=permissions_for(role),
        trace_id="trace-1",
        request_id="req-1",
    )


@pytest.fixture(autouse=True)
def _clear_overrides() -> None:
    yield
    app.dependency_overrides.clear()


def test_platform_admin_creates_tenant() -> None:
    fake = FakePlatformTenantService()
    owner_user_id = uuid4()
    app.dependency_overrides[get_admin_context] = lambda: _context(Role.PLATFORM_ADMIN)
    app.dependency_overrides[get_platform_tenant_service] = lambda: fake
    client = TestClient(app)

    response = client.post(
        "/v1/platform/tenants",
        json={
            "slug": "ropa",
            "name": "Ropa",
            "owner_user_id": str(owner_user_id),
            "owner_email": "owner@ropa.com",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["slug"] == "ropa"
    assert payload["name"] == "Ropa"
    assert payload["status"] == "trialing"
    assert payload["host"] == "ropa.growup.com"
    assert payload["owner_user_id"] == str(owner_user_id)
    assert fake.calls[0]["slug"] == "ropa"
    assert fake.calls[0]["actor_type"] == "platform_admin"
    assert fake.calls[0]["owner_user_id"] == owner_user_id


def test_tenant_owner_cannot_create_tenants() -> None:
    fake = FakePlatformTenantService()
    app.dependency_overrides[get_admin_context] = lambda: _context(Role.OWNER)
    app.dependency_overrides[get_platform_tenant_service] = lambda: fake
    client = TestClient(app)

    response = client.post(
        "/v1/platform/tenants",
        json={
            "slug": "otra",
            "name": "Otra",
            "owner_user_id": str(uuid4()),
            "owner_email": "owner@otra.com",
        },
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
    assert fake.calls == []


def test_governance_denial_is_returned() -> None:
    fake = FakePlatformTenantService(
        error=AppError(
            "GOVERNANCE_DENIED",
            "La política denegó la acción",
            403,
            details={"reason_code": "PLATFORM_ADMIN_REQUIRED"},
        )
    )
    app.dependency_overrides[get_admin_context] = lambda: _context(Role.PLATFORM_ADMIN)
    app.dependency_overrides[get_platform_tenant_service] = lambda: fake
    client = TestClient(app)

    response = client.post(
        "/v1/platform/tenants",
        json={
            "slug": "ropa",
            "name": "Ropa",
            "owner_user_id": str(uuid4()),
            "owner_email": "owner@ropa.com",
        },
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "GOVERNANCE_DENIED"


def test_invalid_slug_is_rejected_by_schema() -> None:
    fake = FakePlatformTenantService()
    app.dependency_overrides[get_admin_context] = lambda: _context(Role.PLATFORM_ADMIN)
    app.dependency_overrides[get_platform_tenant_service] = lambda: fake
    client = TestClient(app)

    response = client.post(
        "/v1/platform/tenants",
        json={
            "slug": "Ropa",
            "name": "Ropa",
            "owner_user_id": str(uuid4()),
            "owner_email": "owner@ropa.com",
        },
    )

    assert response.status_code == 422
    assert fake.calls == []
