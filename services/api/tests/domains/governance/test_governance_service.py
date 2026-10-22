from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.core.errors import AppError
from app.domains.governance.models import Decision, PolicyInput
from app.domains.governance.repository import DecisionLogEntry, DecisionLogRecord
from app.domains.governance.service import GovernanceService


class FakeDecisionLogRepository:
    def __init__(self) -> None:
        self.entries: list[DecisionLogEntry] = []
        self.append_error: Exception | None = None
        self.chain_result = True
        self.logs: tuple[DecisionLogRecord, ...] = ()
        self.next_cursor: int | None = None
        self.listed: list[dict[str, object]] = []

    async def append(self, entry: DecisionLogEntry) -> object:
        if self.append_error is not None:
            raise self.append_error
        self.entries.append(entry)
        return uuid4()

    async def list_logs(
        self,
        tenant_id: UUID,
        *,
        action: str | None,
        decision: str | None,
        limit: int,
        before_seq: int | None,
    ) -> tuple[tuple[DecisionLogRecord, ...], int | None]:
        self.listed.append(
            {
                "tenant_id": tenant_id,
                "action": action,
                "decision": decision,
                "limit": limit,
                "before_seq": before_seq,
            }
        )
        return self.logs, self.next_cursor

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


def _record(seq: int = 1) -> DecisionLogRecord:
    return DecisionLogRecord(
        id=uuid4(),
        seq=seq,
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


async def test_list_logs_validates_filters() -> None:
    service = GovernanceService(FakeDecisionLogRepository())

    with pytest.raises(AppError) as invalid_limit:
        await service.list_logs(
            uuid4(),
            action=None,
            decision=None,
            limit=0,
            before_seq=None,
        )
    assert invalid_limit.value.code == "INVALID_LIMIT"

    with pytest.raises(AppError) as invalid_decision:
        await service.list_logs(
            uuid4(),
            action=None,
            decision="MAYBE",
            limit=50,
            before_seq=None,
        )
    assert invalid_decision.value.code == "INVALID_DECISION"

    with pytest.raises(AppError) as invalid_cursor:
        await service.list_logs(
            uuid4(),
            action=None,
            decision=None,
            limit=50,
            before_seq=0,
        )
    assert invalid_cursor.value.code == "INVALID_CURSOR"

    with pytest.raises(AppError) as long_action:
        await service.list_logs(
            uuid4(),
            action="x" * 121,
            decision=None,
            limit=50,
            before_seq=None,
        )
    assert long_action.value.code == "ACTION_TOO_LONG"


async def test_list_logs_delegates_and_normalizes_action() -> None:
    repository = FakeDecisionLogRepository()
    repository.logs = (_record(),)
    repository.next_cursor = 7
    service = GovernanceService(repository)
    tenant_id = uuid4()

    records, next_cursor = await service.list_logs(
        tenant_id,
        action="  catalog.update_product  ",
        decision="ALLOW",
        limit=20,
        before_seq=10,
    )

    assert records == repository.logs
    assert next_cursor == 7
    assert repository.listed == [
        {
            "tenant_id": tenant_id,
            "action": "catalog.update_product",
            "decision": "ALLOW",
            "limit": 20,
            "before_seq": 10,
        }
    ]


async def test_verify_tenant_chain_uses_tenant_uuid() -> None:
    repository = FakeDecisionLogRepository()
    service = GovernanceService(repository)
    tenant_id = uuid4()

    assert await service.verify_tenant_chain(tenant_id) is True
