"""Zonas de envío del tenant (settings JSON) con parseo fuertemente tipado.

El jsonb viene de una celda escrita por el comercio; nada garantiza su forma.
Ante entradas corruptas se descartan solo las inválidas (con anomalía en logs y
Sentry) y se conserva el resto; si no queda ninguna, el llamador usa el fallback
del MVP. Nunca se propaga una excepción a un checkout.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.safe_json import report_anomaly

_CODE_PATTERN = r"^[a-z0-9_-]{1,60}$"


class ShippingZone(BaseModel):
    model_config = ConfigDict(extra="ignore")

    code: str = Field(min_length=1, max_length=60, pattern=_CODE_PATTERN)
    name: str = Field(min_length=1, max_length=120)
    price_cents: int = Field(ge=0, le=100_000_000)


def parse_shipping_zones(
    raw: object, *, context: str = "tenant_settings.shipping_zones"
) -> list[dict[str, Any]]:
    """Valida zonas de envío; descarta inválidas y reporta anomalías.

    Devuelve dicts planos (compatibles con el contrato público `list[Any]`).
    """
    if not isinstance(raw, list):
        if raw not in (None, []):
            report_anomaly(context, f"shipping_zones no es array: {type(raw).__name__}")
        return []
    zones: list[dict[str, Any]] = []
    for index, item in enumerate(raw):
        try:
            zone = ShippingZone.model_validate(item)
        except ValidationError:
            report_anomaly(context, f"zona #{index} inválida (descartada)")
            continue
        zones.append(zone.model_dump())
    return zones
