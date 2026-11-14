"""Deserialización segura de JSON almacenado en base de datos.

Regla del proyecto (mismo estándar que los bloques cerrados del builder):
nunca dejar que un JSON corrupto en una columna jsonb/text tumbe un endpoint,
un worker o un checkout. Toda anomalía se registra en los logs y en Sentry
(si GROWUP_SENTRY_DSN está configurada) y se recurre a un fallback acotado.
"""

from __future__ import annotations

import json
from typing import Any

from app.core.observability import get_logger

logger = get_logger("growup.json")


def report_anomaly(context: str, detail: str) -> None:
    """Registra la anomalía en logs estructurados y en Sentry (si está configurada)."""
    logger.warning("json_anomaly", context=context, detail=detail)
    from app.core.config import settings

    if not settings.sentry_dsn:
        return
    try:
        import sentry_sdk

        sentry_sdk.capture_message(
            f"JSON corrupto en almacenamiento ({context}): {detail}",
            level="warning",
        )
    except Exception:  # noqa: BLE001 - Sentry nunca debe tumbar el flujo de negocio
        logger.warning("json_anomaly_sentry_failed", context=context)


def safe_json_object(value: object, *, context: str) -> dict[str, Any]:
    """Devuelve un dict a partir de una celda jsonb/text; fallback {} ante anomalías."""
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except ValueError:
            report_anomaly(context, "JSON inválido")
            return {}
        if isinstance(parsed, dict):
            return parsed
        report_anomaly(context, f"se esperaba object, llegó {type(parsed).__name__}")
        return {}
    if value is None:
        return {}
    report_anomaly(context, f"tipo inesperado {type(value).__name__} para object")
    return {}


def safe_json_list(value: object, *, context: str) -> list[Any]:
    """Devuelve una lista a partir de una celda jsonb/text; fallback [] ante anomalías."""
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except ValueError:
            report_anomaly(context, "JSON inválido")
            return []
        if isinstance(parsed, list):
            return parsed
        report_anomaly(context, f"se esperaba array, llegó {type(parsed).__name__}")
        return []
    if value is None:
        return []
    report_anomaly(context, f"tipo inesperado {type(value).__name__} para array")
    return []
