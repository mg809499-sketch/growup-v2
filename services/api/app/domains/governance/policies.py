from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.domains.governance.models import Decision, PolicyInput, PolicyResult

_CONTEXT_SUMMARY_KEYS = frozenset(
    {
        "slug",
        "host",
        "plan_id",
        "page_id",
        "payment_id",
        "order_id",
        "amount_cents",
        "refund_amount_cents",
    }
)


@dataclass(frozen=True, slots=True)
class _Outcome:
    decision: Decision
    reason_code: str


@dataclass(frozen=True, slots=True)
class _PolicySpec:
    id: str
    version: str
    evaluate: Callable[[PolicyInput], _Outcome]


def _platform_create_tenant(input: PolicyInput) -> _Outcome:
    if input.actor_type != "platform_admin":
        return _Outcome(Decision.DENY, "PLATFORM_ADMIN_REQUIRED")
    slug = input.context.get("slug")
    if not isinstance(slug, str) or not slug:
        return _Outcome(Decision.DENY, "SLUG_REQUIRED")
    return _Outcome(Decision.ALLOW, "PLATFORM_ADMIN_ALLOWED")


_POLICIES: dict[str, _PolicySpec] = {
    "platform.create_tenant": _PolicySpec(
        id="platform.create_tenant",
        version="v1",
        evaluate=_platform_create_tenant,
    ),
}


def decide(policy_id: str, input: PolicyInput) -> PolicyResult:
    """Ejecuta una política determinista. Ante cualquier error, DENY."""
    spec = _POLICIES.get(policy_id)
    if spec is None:
        return PolicyResult(
            decision=Decision.DENY,
            policy_id=policy_id,
            policy_version="unknown",
            reason_code="POLICY_NOT_FOUND",
            latency_ms=0,
        )

    start = time.perf_counter()
    try:
        outcome = spec.evaluate(input)
    except Exception:  # noqa: BLE001 - una política rota nunca permite
        outcome = _Outcome(Decision.DENY, "POLICY_ERROR")

    latency_ms = int((time.perf_counter() - start) * 1000)
    return PolicyResult(
        decision=outcome.decision,
        policy_id=spec.id,
        policy_version=spec.version,
        reason_code=outcome.reason_code,
        latency_ms=latency_ms,
    )


def input_hash(input: PolicyInput) -> str:
    """SHA-256 del input canónico, para auditar sin guardar el payload."""
    payload = {
        "tenant_id": str(input.tenant_id) if input.tenant_id is not None else None,
        "actor_id": input.actor_id,
        "actor_type": input.actor_type,
        "action": input.action,
        "resource_type": input.resource_type,
        "resource_id": input.resource_id,
        "context": input.context,
        "trace_id": input.trace_id,
    }
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def redact(context: dict[str, Any]) -> dict[str, Any]:
    """Deja en el resumen auditado solo las claves de la allowlist."""
    return {key: value for key, value in context.items() if key in _CONTEXT_SUMMARY_KEYS}
