from __future__ import annotations

import app.core.safe_json as safe_json
from app.core.safe_json import safe_json_list, safe_json_object


def test_object_passthrough_for_dict() -> None:
    assert safe_json_object({"a": 1}, context="t") == {"a": 1}


def test_object_parses_valid_json_string() -> None:
    assert safe_json_object('{"a": "b"}', context="t") == {"a": "b"}


def test_object_falls_back_on_corrupt_string(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    anomalies: list[tuple[str, str]] = []
    monkeypatch.setattr(
        safe_json, "report_anomaly", lambda context, detail: anomalies.append((context, detail))
    )
    assert safe_json_object("{not json", context="ctx") == {}
    assert anomalies and anomalies[0][0] == "ctx"


def test_object_falls_back_on_wrong_json_type(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    anomalies: list[str] = []
    monkeypatch.setattr(
        safe_json, "report_anomaly", lambda context, detail: anomalies.append(detail)
    )
    assert safe_json_object("[1, 2]", context="ctx") == {}
    assert anomalies


def test_object_falls_back_on_unexpected_types(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    anomalies: list[str] = []
    monkeypatch.setattr(
        safe_json, "report_anomaly", lambda context, detail: anomalies.append(detail)
    )
    assert safe_json_object(None, context="ctx") == {}
    assert safe_json_object(42, context="ctx") == {}
    assert len(anomalies) == 1  # None es ausencia válida, no anomalía


def test_list_parses_and_falls_back(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    assert safe_json_list('[{"a": 1}]', context="t") == [{"a": 1}]
    assert safe_json_list(["x"], context="t") == ["x"]

    anomalies: list[str] = []
    monkeypatch.setattr(
        safe_json, "report_anomaly", lambda context, detail: anomalies.append(detail)
    )
    assert safe_json_list("{oops", context="ctx") == []
    assert safe_json_list('{"not": "a list"}', context="ctx") == []
    assert safe_json_list(5, context="ctx") == []
    assert len(anomalies) == 3


def test_report_anomaly_never_raises() -> None:
    # Sin DSN configurada (test), solo loggea; nunca debe lanzar.
    safe_json.report_anomaly("ctx", "detail")
