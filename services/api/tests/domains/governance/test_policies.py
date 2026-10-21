from __future__ import annotations

from uuid import uuid4

import pytest

from app.domains.governance import policies
from app.domains.governance.models import Decision, PolicyInput
from app.domains.governance.policies import decide, input_hash, redact


def _input(
    *,
    actor_type: str = "platform_admin",
    context: dict[str, object] | None = None,
) -> PolicyInput:
    return PolicyInput(
        tenant_id=None,
        actor_id="actor-1",
        actor_type=actor_type,
        action="platform.create_tenant",
        resource_type="tenant",
        resource_id=None,
        context=context if context is not None else {"slug": "ropa"},
        trace_id="trace-1",
    )


def test_platform_admin_can_create_tenant() -> None:
    result = decide("platform.create_tenant", _input())

    assert result.decision is Decision.ALLOW
    assert result.policy_id == "platform.create_tenant"
    assert result.policy_version == "v1"
    assert result.reason_code == "PLATFORM_ADMIN_ALLOWED"
    assert result.latency_ms >= 0


def test_staff_cannot_create_tenant() -> None:
    result = decide("platform.create_tenant", _input(actor_type="staff"))

    assert result.decision is Decision.DENY
    assert result.reason_code == "PLATFORM_ADMIN_REQUIRED"


def test_missing_slug_is_denied() -> None:
    result = decide("platform.create_tenant", _input(context={}))

    assert result.decision is Decision.DENY
    assert result.reason_code == "SLUG_REQUIRED"


def test_unknown_policy_fails_closed() -> None:
    result = decide("no.existe", _input())

    assert result.decision is Decision.DENY
    assert result.reason_code == "POLICY_NOT_FOUND"
    assert result.policy_version == "unknown"
    assert result.latency_ms == 0


def test_policy_exception_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    def _explode(_: PolicyInput) -> policies._Outcome:
        raise RuntimeError("boom")

    monkeypatch.setitem(
        policies._POLICIES,
        "platform.create_tenant",
        policies._PolicySpec(
            id="platform.create_tenant",
            version="v1",
            evaluate=_explode,
        ),
    )

    result = decide("platform.create_tenant", _input())

    assert result.decision is Decision.DENY
    assert result.reason_code == "POLICY_ERROR"


def test_input_hash_is_stable_and_sensitive_to_context() -> None:
    first = input_hash(_input(context={"slug": "ropa"}))
    second = input_hash(_input(context={"slug": "ropa"}))

    assert first == second
    assert len(first) == 64
    assert int(first, 16) >= 0

    different = input_hash(_input(context={"slug": "joyas"}))
    assert different != first


def test_redact_keeps_only_allowlisted_keys() -> None:
    summary = redact(
        {
            "slug": "ropa",
            "owner_user_id": str(uuid4()),
            "owner_email": "owner@example.com",
            "amount_cents": 1200000,
            "secret": "no-auditar",
        }
    )

    assert summary == {"slug": "ropa", "amount_cents": 1200000}
