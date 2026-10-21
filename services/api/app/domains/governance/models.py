from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import UUID


class Decision(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HANDOFF = "HANDOFF"


@dataclass(frozen=True, slots=True)
class PolicyInput:
    tenant_id: UUID | None
    actor_id: str | None
    actor_type: str
    action: str
    resource_type: str | None
    resource_id: str | None
    context: dict[str, Any]
    trace_id: str | None


@dataclass(frozen=True, slots=True)
class PolicyResult:
    decision: Decision
    policy_id: str
    policy_version: str
    reason_code: str
    latency_ms: int
