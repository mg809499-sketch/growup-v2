from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, cast
from uuid import UUID

import asyncpg  # type: ignore[import-untyped]

from app.core.db import Database
from app.core.errors import AppError


@dataclass(frozen=True, slots=True)
class DecisionLogEntry:
    tenant_id: UUID | None
    actor_type: str
    actor_id: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    policy_id: str
    policy_version: str
    decision: str
    reason_code: str
    input_hash: str
    context_summary: dict[str, Any]
    latency_ms: int
    trace_id: str | None


@dataclass(frozen=True, slots=True)
class DecisionLogRecord:
    id: UUID
    seq: int
    actor_type: str
    actor_id: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    policy_id: str
    policy_version: str
    decision: str
    reason_code: str
    input_hash: str
    context_summary: dict[str, Any]
    latency_ms: int
    trace_id: str | None
    created_at: datetime


class DecisionLogRepository(Protocol):
    async def append(self, entry: DecisionLogEntry) -> UUID: ...

    async def list_logs(
        self,
        tenant_id: UUID,
        *,
        action: str | None,
        decision: str | None,
        limit: int,
        before_seq: int | None,
    ) -> tuple[tuple[DecisionLogRecord, ...], int | None]: ...

    async def verify_chain(self, chain_key: str) -> bool: ...


class PostgresDecisionLogRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    async def append(self, entry: DecisionLogEntry) -> UUID:
        try:
            transaction = (
                self._database.public_transaction()
                if entry.tenant_id is None
                else self._database.tenant_transaction(entry.tenant_id)
            )
            async with transaction as connection:
                log_id = await connection.fetchval(
                    "select app.append_decision_log("
                    "$1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::jsonb, "
                    "$13, $14)",
                    entry.tenant_id,
                    entry.actor_type,
                    entry.actor_id,
                    entry.action,
                    entry.resource_type,
                    entry.resource_id,
                    entry.policy_id,
                    entry.policy_version,
                    entry.decision,
                    entry.reason_code,
                    entry.input_hash,
                    json.dumps(entry.context_summary),
                    entry.latency_ms,
                    entry.trace_id,
                )
        except asyncpg.PostgresError as exc:
            raise AppError(
                "GOVERNANCE_AUDIT_FAILED",
                "No se pudo registrar la decisión",
                503,
            ) from exc

        if log_id is None:
            raise AppError(
                "GOVERNANCE_AUDIT_FAILED",
                "No se pudo registrar la decisión",
                503,
            )
        return cast(UUID, log_id)

    async def verify_chain(self, chain_key: str) -> bool:
        async with self._database.public_transaction() as connection:
            return bool(
                await connection.fetchval(
                    "select app.verify_decision_chain($1)",
                    chain_key,
                )
            )

    async def list_logs(
        self,
        tenant_id: UUID,
        *,
        action: str | None,
        decision: str | None,
        limit: int,
        before_seq: int | None,
    ) -> tuple[tuple[DecisionLogRecord, ...], int | None]:
        async with self._database.tenant_transaction(tenant_id) as connection:
            rows = await connection.fetch(
                """
                select seq, id, actor_type, actor_id, action, resource_type,
                       resource_id, policy_id, policy_version, decision,
                       reason_code, input_hash, context_summary, latency_ms,
                       trace_id, created_at
                from app.decision_logs
                where tenant_id = $1
                  and ($2::text is null or action = $2)
                  and ($3::text is null or decision = $3)
                  and ($4::bigint is null or seq < $4)
                order by seq desc
                limit $5::int
                """,
                tenant_id,
                action,
                decision,
                before_seq,
                limit + 1,
            )

        has_more = len(rows) > limit
        page_rows = rows[:limit]
        next_cursor = int(page_rows[-1]["seq"]) if has_more and page_rows else None
        return tuple(_record(row) for row in page_rows), next_cursor


def _record(row: Any) -> DecisionLogRecord:
    return DecisionLogRecord(
        id=row["id"],
        seq=row["seq"],
        actor_type=row["actor_type"],
        actor_id=row["actor_id"],
        action=row["action"],
        resource_type=row["resource_type"],
        resource_id=row["resource_id"],
        policy_id=row["policy_id"],
        policy_version=row["policy_version"],
        decision=row["decision"],
        reason_code=row["reason_code"],
        input_hash=row["input_hash"],
        context_summary=_as_dict(row["context_summary"]),
        latency_ms=row["latency_ms"],
        trace_id=row["trace_id"],
        created_at=row["created_at"],
    )


def _as_dict(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed
    return {}
