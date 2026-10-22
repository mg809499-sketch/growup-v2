from __future__ import annotations

from uuid import UUID

from app.core.errors import AppError
from app.domains.governance.models import Decision, PolicyInput, PolicyResult
from app.domains.governance.policies import decide, input_hash, redact
from app.domains.governance.repository import (
    DecisionLogEntry,
    DecisionLogRecord,
    DecisionLogRepository,
)

_DECISIONS = {decision.value for decision in Decision}


class GovernanceService:
    """Decide y audita. Si la auditoría falla, la mutación no ocurre."""

    def __init__(self, repository: DecisionLogRepository) -> None:
        self._repository = repository

    async def evaluate_and_record(
        self,
        policy_id: str,
        input: PolicyInput,
    ) -> PolicyResult:
        result = decide(policy_id, input)

        entry = DecisionLogEntry(
            tenant_id=input.tenant_id,
            actor_type=input.actor_type,
            actor_id=input.actor_id,
            action=input.action,
            resource_type=input.resource_type,
            resource_id=input.resource_id,
            policy_id=result.policy_id,
            policy_version=result.policy_version,
            decision=result.decision.value,
            reason_code=result.reason_code,
            input_hash=input_hash(input),
            context_summary=redact(input.context),
            latency_ms=result.latency_ms,
            trace_id=input.trace_id,
        )

        try:
            await self._repository.append(entry)
        except AppError:
            raise
        except Exception as exc:  # noqa: BLE001 - fallo de auditoría = fallo cerrado
            raise AppError(
                "GOVERNANCE_AUDIT_FAILED",
                "No se pudo registrar la decisión",
                503,
            ) from exc

        if result.decision is not Decision.ALLOW:
            raise AppError(
                "GOVERNANCE_DENIED",
                f"La política denegó la acción: {result.reason_code}",
                403,
                details={"policy_id": result.policy_id, "reason_code": result.reason_code},
            )

        return result

    async def verify_chain(self, chain_key: str) -> bool:
        return await self._repository.verify_chain(chain_key)

    async def list_logs(
        self,
        tenant_id: UUID,
        *,
        action: str | None,
        decision: str | None,
        limit: int,
        before_seq: int | None,
    ) -> tuple[tuple[DecisionLogRecord, ...], int | None]:
        if limit < 1 or limit > 100:
            raise AppError("INVALID_LIMIT", "El límite debe estar entre 1 y 100", 422)
        if decision is not None and decision not in _DECISIONS:
            raise AppError("INVALID_DECISION", "Decisión inválida", 422)
        if before_seq is not None and before_seq < 1:
            raise AppError("INVALID_CURSOR", "El cursor debe ser positivo", 422)

        normalized_action = action.strip() if action else None
        if normalized_action is not None and len(normalized_action) > 120:
            raise AppError("ACTION_TOO_LONG", "La acción es demasiado larga", 422)

        return await self._repository.list_logs(
            tenant_id,
            action=normalized_action,
            decision=decision,
            limit=limit,
            before_seq=before_seq,
        )

    async def verify_tenant_chain(self, tenant_id: UUID) -> bool:
        return await self._repository.verify_chain(str(tenant_id))
