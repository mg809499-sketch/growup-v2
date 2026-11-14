from __future__ import annotations

from typing import Any, cast

import pytest

from app.core.errors import AppError
from app.domains.commerce.repository import wompi_event_checksum
from app.domains.commerce.schemas import parse_wompi_event
from app.domains.commerce.service import CommerceService

_VALID_EVENT: dict[str, Any] = {
    "id": "evt_123",
    "event": "transaction.updated",
    "data": {
        "transaction": {
            "id": "tx_1",
            "reference": "ord_1",
            "status": "APPROVED",
            "payment_method_type": "CARD",
        }
    },
    "signature": {
        "properties": ["transaction.id", "transaction.status"],
        "timestamp": 1700000000,
        "checksum": "deadbeef",
    },
}


def test_parse_valid_event() -> None:
    event = parse_wompi_event(_VALID_EVENT)
    assert event.id == "evt_123"
    assert event.data.transaction.reference == "ord_1"
    assert event.data.transaction.status == "APPROVED"
    assert event.signature.checksum == "deadbeef"
    assert event.signature.properties == ["transaction.id", "transaction.status"]


def test_parse_accepts_checksum_sha256_alias() -> None:
    raw = {
        **_VALID_EVENT,
        "signature": {
            "properties": ["transaction.id"],
            "timestamp": 1700000000,
            "checksum-sha256": "cafebabe",
        },
    }
    event = parse_wompi_event(raw)
    assert event.signature.checksum_sha256 == "cafebabe"


def test_parse_rejects_wrong_container_types() -> None:
    with pytest.raises(AppError) as excinfo:
        parse_wompi_event({"id": "e", "data": ["no-un-dict"]})
    assert excinfo.value.code == "WOMPI_EVENT_INVALID"
    assert excinfo.value.status_code == 400

    with pytest.raises(AppError):
        parse_wompi_event({"id": "e", "data": {"transaction": "not-a-dict"}})

    with pytest.raises(AppError):
        parse_wompi_event({"signature": "not-a-dict"})


def test_parse_rejects_properties_wrong_type() -> None:
    raw = {
        **_VALID_EVENT,
        "signature": {"properties": "transaction.id", "timestamp": 1700000000},
    }
    with pytest.raises(AppError) as excinfo:
        parse_wompi_event(raw)
    assert excinfo.value.code == "WOMPI_EVENT_INVALID"


def test_parse_rejects_non_dict_input() -> None:
    with pytest.raises(AppError):
        parse_wompi_event(cast(Any, ["not", "a", "dict"]))


async def test_process_event_without_identifier_is_400() -> None:
    service = CommerceService(cast(Any, None))
    with pytest.raises(AppError) as excinfo:
        await service.process_wompi_event(
            {"data": {"transaction": {"reference": "ord_x", "status": "APPROVED"}}}
        )
    assert excinfo.value.code == "WOMPI_EVENT_INVALID"
    assert excinfo.value.status_code == 400


async def test_process_event_malformed_container_is_400_not_500() -> None:
    service = CommerceService(cast(Any, None))
    with pytest.raises(AppError) as excinfo:
        await service.process_wompi_event({"id": "e1", "data": ["basura"]})
    assert excinfo.value.code == "WOMPI_EVENT_INVALID"
    assert excinfo.value.status_code == 400


def test_checksum_fail_closed_on_malformed_input() -> None:
    assert wompi_event_checksum(cast(Any, "not-a-dict"), "secret") == ""
    assert wompi_event_checksum({"signature": "not-a-dict"}, "secret") == ""
    assert wompi_event_checksum({"signature": {"properties": "txn"}}, "secret") == ""
    assert wompi_event_checksum({"signature": {"properties": []}}, "secret") == ""
    malformed = {"signature": {"properties": ["a.b"]}, "data": "no-dict"}
    assert wompi_event_checksum(malformed, "s") == ""


def test_checksum_deterministic() -> None:
    digest = wompi_event_checksum(_VALID_EVENT, "events_secret")
    assert digest == wompi_event_checksum(_VALID_EVENT, "events_secret")
    assert len(digest) == 64
    assert wompi_event_checksum(_VALID_EVENT, "otro_secret") != digest
