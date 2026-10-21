from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_admin_context, get_auth_service
from app.core.errors import AppError
from app.domains.identity.models import Actor, RequestContext, Role
from app.domains.identity.permissions import permissions_for
from app.main import app


def _context(role: Role = Role.OWNER) -> RequestContext:
    actor = Actor(
        user_id=uuid4(),
        tenant_id=uuid4(),
        role=role,
        email="owner@example.com",
    )
    return RequestContext(
        tenant_id=actor.tenant_id,
        actor=actor,
        permissions=permissions_for(role),
        trace_id="trace-1",
        request_id="req-1",
    )


class FakeAuthService:
    async def authenticate(self, token: str) -> Actor:
        raise AppError("TOKEN_INVALID", "Token inválido", 401)


def test_me_returns_context() -> None:
    context = _context()
    app.dependency_overrides[get_admin_context] = lambda: context
    client = TestClient(app)

    try:
        response = client.get("/v1/admin/me")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == str(context.actor.user_id)
    assert payload["tenant_id"] == str(context.tenant_id)
    assert payload["role"] == "owner"
    assert "content:publish" in payload["permissions"]


def test_me_without_token_returns_401() -> None:
    app.dependency_overrides.clear()
    client = TestClient(app)

    response = client.get("/v1/admin/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "TOKEN_INVALID"


def test_me_with_invalid_token_returns_401() -> None:
    app.dependency_overrides[get_auth_service] = lambda: FakeAuthService()
    client = TestClient(app)

    try:
        response = client.get(
            "/v1/admin/me",
            headers={"Authorization": "Bearer bad-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "TOKEN_INVALID"
