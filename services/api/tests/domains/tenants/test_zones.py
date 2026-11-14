from __future__ import annotations

from typing import Any, cast

import pytest
from pydantic import ValidationError

import app.core.safe_json as safe_json
from app.core.errors import AppError
from app.domains.commerce.service import DEFAULT_SHIPPING_ZONES, CommerceService
from app.domains.tenants.zones import ShippingZone, parse_shipping_zones


def test_parse_zones_valid() -> None:
    raw = [
        {"code": "bogota", "name": "Bogotá D.C.", "price_cents": 800_000},
        {"code": "resto", "name": "Resto del país", "price_cents": 1_500_000, "extra": "ignored"},
    ]
    zones = parse_shipping_zones(raw)
    assert [zone["code"] for zone in zones] == ["bogota", "resto"]
    assert zones[0]["price_cents"] == 800_000


def test_parse_zones_drops_invalid_and_reports(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    anomalies: list[str] = []
    monkeypatch.setattr(
        safe_json, "report_anomaly", lambda context, detail: anomalies.append(detail)
    )
    # Note: zones.py imports report_anomaly directly; patch it there too.
    import app.domains.tenants.zones as zones_module

    monkeypatch.setattr(
        zones_module, "report_anomaly", lambda context, detail: anomalies.append(detail)
    )

    raw = [
        {"code": "bogota", "name": "Bogotá", "price_cents": 100},
        {"code": "", "name": "Sin código", "price_cents": 100},
        {"name": "Sin código", "price_cents": 100},
        {"code": "resto", "name": "Resto", "price_cents": -1},
        {"code": "resto", "name": "Resto", "price_cents": "no-es-numero"},
        "basura",
    ]
    zones = parse_shipping_zones(raw)
    assert [zone["code"] for zone in zones] == ["bogota"]
    assert len(anomalies) == 5


def test_parse_zones_non_list_input(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    anomalies: list[str] = []
    import app.domains.tenants.zones as zones_module

    monkeypatch.setattr(
        zones_module, "report_anomaly", lambda context, detail: anomalies.append(detail)
    )
    assert parse_shipping_zones('{"code": "bogota"}') == []
    assert parse_shipping_zones(None) == []
    assert parse_shipping_zones(42) == []
    assert len(anomalies) == 2  # None es ausencia válida


def _service() -> CommerceService:
    return CommerceService(cast(Any, None))


def test_shipping_zones_fallback_to_mvp_when_empty_or_corrupt() -> None:
    service = _service()
    assert service.shipping_zones([]) == DEFAULT_SHIPPING_ZONES
    assert service.shipping_zones([{"code": "x", "name": "x", "price_cents": "bad"}]) == (
        DEFAULT_SHIPPING_ZONES
    )


def test_zone_price_existing_zone() -> None:
    service = _service()
    assert service.zone_price("bogota", []) == 800_000
    tenant_zones = [{"code": "medellin", "name": "Medellín", "price_cents": 400_000}]
    assert service.zone_price("medellin", tenant_zones) == 400_000


def test_zone_price_unknown_zone_raises_422() -> None:
    service = _service()
    with pytest.raises(AppError) as excinfo:
        service.zone_price("no-existe", [])
    assert excinfo.value.code == "SHIPPING_ZONE_INVALID"
    assert excinfo.value.status_code == 422


def test_shipping_zone_rejects_negative_price() -> None:
    with pytest.raises(ValidationError):
        ShippingZone(code="bogota", name="Bogotá", price_cents=-1)


def test_zone_id_pattern() -> None:
    with pytest.raises(ValidationError):
        ShippingZone(code="BOGOTA!!", name="Bogotá", price_cents=0)
