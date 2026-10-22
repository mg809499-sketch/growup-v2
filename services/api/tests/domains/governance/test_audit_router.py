from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_governance_service, get_tenant_context
from app.domains.governance.repository import DecisionLogRecord
from app.domains.identity.models import Actor, RequestContext, Role
from app.domains.identity.permissions import permissions_for
from app.main import app

TENANT_ID = uuid4()


class FakeGovernanceService:
    def __init__(self) -> None:
        self.records: tuple[DecisionLogRecord, ...] = ()
        self.next_cursor: int | None = None
        self.valid = True
        self.calls: list[tuple[str, object]] = []

    async def list_logs(
        self,
        tenant_id: object,
        *,
        action: str | None,
        decision: str | None,
        limit: int,
        before_seq: int | None,
    ) -> tuple[tuple[DecisionLogRecord, ...], int | None]:
        self.calls.append(
            (
                "list_logs",
                {
                    "tenant_id": tenant_id,
                    "action": action,
                    "decision": decision,
                    "limit": limit,
                    "before_seq": before_seq,
                },
            )
        )
        return self.records, self.next_cursor

    async def verify_tenant_chain(self, tenant_id: object) -> bool:
        self.calls.append(("verify_tenant_chain", tenant_id))
        return self.valid


def _context(role: Role) -> RequestContext:
    actor = Actor(
        user_id=uuid4(),
        tenant_id=TENANT_ID,
        role=role,
        email="owner@example.com",
    )
    return RequestContext(
        tenant_id=TENANT_ID,
        actor=actor,
        permissions=permissions_for(role),
        trace_id="trace-1",
        request_id="req-1",
    )


def _record() -> DecisionLogRecord:
    return DecisionLogRecord(
        id=uuid4(),
        seq=42,
        actor_type="staff",
        actor_id="actor-1",
        action="catalog.update_product",
        resource_type="product",
        resource_id=str(uuid4()),
        policy_id="catalog.update_product",
        policy_version="v1",
        decision="ALLOW",
        reason_code="ALLOWED",
        input_hash="a" * 64,
        context_summary={"slug": "camisa"},
        latency_ms=1,
        trace_id="trace-1",
        created_at=datetime.now(UTC),
    )


@pytest.fixture(autouse=True)
def _clear_overrides() -> None:
    yield
    app.dependency_overrides.clear()


def test_list_audit_logs() -> None:
    fake = FakeGovernanceService()
    fake.records = (_record(),)
    fake.next_cursor = 42
    app.dependency_overrides[get_tenant_context] = lambda: _context(Role.OWNER)
    app.dependency_overrides[get_governance_service] = lambda: fake
    client = TestClient(app)

    response = client.get(
        "/v1/admin/audit?action=catalog.update_product&decision=ALLOW&limit=20&before_seq=50"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["next_cursor"] == 42
    assert payload["items"][0]["seq"] == 42
    assert payload["items"][0]["decision"] == "ALLOW"
    assert payload["items"][0]["context_summary"] == {"slug": "camisa"}
    call = fake.calls[0][1]
    assert isinstance(call, dict)
    assert call["tenant_id"] == TENANT_ID
    assert call["action"] == "catalog.update_product"
    assert call["decision"] == "ALLOW"
    assert call["limit"] == 20
    assert call["before_seq"] == 50


def test_verify_audit_chain() -> None:
    fake = FakeGovernanceService()
    fake.valid = True
    app.dependency_overrides[get_tenant_context] = lambda: _context(Role.OWNER)
    app.dependency_overrides[get_governance_service] = lambda: fake
    client = TestClient(app)

    response = client.get("/v1/admin/audit/verify")

    assert response.status_code == 200
    assert response.json() == {"chain_key": str(TENANT_ID), "valid": True}
    assert fake.calls == [("verify_tenant_chain", TENANT_ID)]


def test_manager_cannot_read_audit() -> None:
    fake = FakeGovernanceService()
    app.dependency_overrides[get_tenant_context] = lambda: _context(Role.MANAGER)
    app.dependency_overrides[get_governance_service] = lambda: fake
    client = TestClient(app)

    response = client.get("/v1/admin/audit")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
    assert fake.calls == []


def test_invalid_decision_is_rejected() -> None:
    fake = FakeGovernanceService()
    app.dependency_overrides[get_tenant_context] = lambda: _context(Role.OWNER)
    app.dependency_overrides[get_governance_service] = lambda: fake
    client = TestClient(app)

    response = client.get("/v1/admin/audit?decision=MAYBE")

    assert response.status_code == 422
    assert fake.calls == []
