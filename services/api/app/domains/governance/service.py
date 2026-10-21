from __future__ import annotations

from app.core.errors import AppError
from app.domains.governance.models import Decision, PolicyInput, PolicyResult
from app.domains.governance.policies import decide, input_hash, redact
from app.domains.governance.repository import DecisionLogEntry, DecisionLogRepository


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
