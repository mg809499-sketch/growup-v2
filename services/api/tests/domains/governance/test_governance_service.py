from __future__ import annotations

from uuid import uuid4

import pytest

from app.core.errors import AppError
from app.domains.governance.models import Decision, PolicyInput
from app.domains.governance.repository import DecisionLogEntry
from app.domains.governance.service import GovernanceService


class FakeDecisionLogRepository:
    def __init__(self) -> None:
        self.entries: list[DecisionLogEntry] = []
        self.append_error: Exception | None = None
        self.chain_result = True

    async def append(self, entry: DecisionLogEntry) -> object:
        if self.append_error is not None:
            raise self.append_error
        self.entries.append(entry)
        return uuid4()

    async def verify_chain(self, chain_key: str) -> bool:
        return self.chain_result


def _input(*, actor_type: str = "platform_admin") -> PolicyInput:
    return PolicyInput(
        tenant_id=None,
        actor_id="actor-1",
        actor_type=actor_type,
        action="platform.create_tenant",
        resource_type="tenant",
        resource_id=None,
        context={
            "slug": "ropa",
            "owner_user_id": str(uuid4()),
            "owner_email": "owner@example.com",
        },
        trace_id="trace-1",
    )


async def test_allow_is_recorded_and_returned() -> None:
    repository = FakeDecisionLogRepository()
    service = GovernanceService(repository)

    result = await service.evaluate_and_record("platform.create_tenant", _input())

    assert result.decision is Decision.ALLOW
    assert len(repository.entries) == 1
    entry = repository.entries[0]
    assert entry.decision == "ALLOW"
    assert entry.reason_code == "PLATFORM_ADMIN_ALLOWED"
    assert entry.actor_type == "platform_admin"
    assert entry.context_summary == {"slug": "ropa"}
    assert len(entry.input_hash) == 64
    assert entry.trace_id == "trace-1"


async def test_deny_is_recorded_and_raises() -> None:
    repository = FakeDecisionLogRepository()
    service = GovernanceService(repository)

    with pytest.raises(AppError) as exc_info:
        await service.evaluate_and_record(
            "platform.create_tenant",
            _input(actor_type="staff"),
        )

    error = exc_info.value
    assert error.code == "GOVERNANCE_DENIED"
    assert error.status_code == 403
    assert error.details["reason_code"] == "PLATFORM_ADMIN_REQUIRED"
    assert len(repository.entries) == 1
    assert repository.entries[0].decision == "DENY"


async def test_unknown_policy_is_recorded_as_deny() -> None:
    repository = FakeDecisionLogRepository()
    service = GovernanceService(repository)

    with pytest.raises(AppError):
        await service.evaluate_and_record("no.existe", _input())

    assert repository.entries[0].decision == "DENY"
    assert repository.entries[0].reason_code == "POLICY_NOT_FOUND"


async def test_audit_failure_fails_closed() -> None:
    repository = FakeDecisionLogRepository()
    repository.append_error = RuntimeError("db down")
    service = GovernanceService(repository)

    with pytest.raises(AppError) as exc_info:
        await service.evaluate_and_record("platform.create_tenant", _input())

    assert exc_info.value.code == "GOVERNANCE_AUDIT_FAILED"
    assert exc_info.value.status_code == 503


async def test_verify_chain_delegates() -> None:
    repository = FakeDecisionLogRepository()
    repository.chain_result = False
    service = GovernanceService(repository)

    assert await service.verify_chain("platform") is False
