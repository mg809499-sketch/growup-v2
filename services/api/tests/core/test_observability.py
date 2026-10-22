from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.api.deps import get_storefront_tenant, get_tenant_context
from app.core.errors import AppError
from app.domains.identity.models import Actor, RequestContext, Role
from app.domains.identity.permissions import permissions_for
from app.domains.tenants.models import Tenant, TenantStatus
from app.main import app as main_app


def _request(*, host: str | None = None) -> Request:
    headers = [(b"host", host.encode())] if host else []
    return Request({"type": "http", "method": "GET", "path": "/", "headers": headers})


def _context(tenant_id: object) -> RequestContext:
    actor = Actor(
        user_id=uuid4(),
        tenant_id=tenant_id,  # type: ignore[arg-type]
        role=Role.OWNER,
        email="owner@example.com",
    )
    return RequestContext(
        tenant_id=tenant_id,  # type: ignore[arg-type]
        actor=actor,
        permissions=permissions_for(Role.OWNER),
        trace_id="trace-1",
        request_id="req-1",
    )


async def test_tenant_context_binds_tenant_id_to_request_state() -> None:
    tenant_id = uuid4()
    request = _request()

    context = await get_tenant_context(request, _context(tenant_id))

    assert context.tenant_id == tenant_id
    assert request.state.tenant_id == str(tenant_id)


async def test_tenant_context_without_tenant_is_forbidden() -> None:
    request = _request()

    with pytest.raises(AppError) as exc_info:
        await get_tenant_context(request, _context(None))

    assert exc_info.value.code == "FORBIDDEN"
    assert not hasattr(request.state, "tenant_id")


async def test_storefront_tenant_binds_tenant_id_to_request_state() -> None:
    tenant = Tenant(
        id=uuid4(),
        slug="ropa",
        name="Ropa",
        status=TenantStatus.ACTIVE,
    )

    class FakeResolver:
        async def resolve(self, host: str) -> Tenant:
            assert host == "ropa.growup.com"
            return tenant

    request = _request(host="ropa.growup.com")

    resolved = await get_storefront_tenant(request, FakeResolver())  # type: ignore[arg-type]

    assert resolved.id == tenant.id
    assert request.state.tenant_id == str(tenant.id)


def test_http_request_log_has_no_query_string(capsys: pytest.CaptureFixture[str]) -> None:
    client = TestClient(main_app)

    response = client.get("/healthz?token=super-secret")

    assert response.status_code == 200
    output = capsys.readouterr().out
    assert "http_request" in output
    assert "/healthz" in output
    assert "super-secret" not in output


def test_request_id_is_echoed() -> None:
    client = TestClient(main_app)

    response = client.get("/healthz", headers={"X-Request-ID": "req-123"})

    assert response.headers["x-request-id"] == "req-123"
