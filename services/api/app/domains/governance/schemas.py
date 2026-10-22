from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.domains.governance.models import Decision
from app.domains.governance.repository import DecisionLogRecord


class AuditLogResponse(BaseModel):
    id: UUID
    seq: int
    actor_type: str
    actor_id: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    policy_id: str
    policy_version: str
    decision: Decision
    reason_code: str
    input_hash: str
    context_summary: dict[str, Any]
    latency_ms: int
    trace_id: str | None
    created_at: datetime

    @classmethod
    def from_record(cls, record: DecisionLogRecord) -> AuditLogResponse:
        return cls(
            id=record.id,
            seq=record.seq,
            actor_type=record.actor_type,
            actor_id=record.actor_id,
            action=record.action,
            resource_type=record.resource_type,
            resource_id=record.resource_id,
            policy_id=record.policy_id,
            policy_version=record.policy_version,
            decision=Decision(record.decision),
            reason_code=record.reason_code,
            input_hash=record.input_hash,
            context_summary=record.context_summary,
            latency_ms=record.latency_ms,
            trace_id=record.trace_id,
            created_at=record.created_at,
        )


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    next_cursor: int | None


class AuditVerifyResponse(BaseModel):
    chain_key: str
    valid: bool
