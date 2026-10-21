from __future__ import annotations

import json
from dataclasses import dataclass
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


class DecisionLogRepository(Protocol):
    async def append(self, entry: DecisionLogEntry) -> UUID: ...

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
