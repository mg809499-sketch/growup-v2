from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.domains.content.schemas import ThemeUpsertRequest, validate_theme_tokens

_GOOD = {
    "colors": {"surface": "#faf9f4", "ink": "#1a1a1a"},
    "radius": 4,
    "dark": False,
    "tags": ["ropa", "joyeria"],
}


def test_validate_accepts_well_formed_tokens() -> None:
    assert validate_theme_tokens(dict(_GOOD)) == _GOOD


def test_validate_rejects_deep_nesting() -> None:
    tokens = {"a": {"b": {"c": {"d": {"e": "too deep"}}}}}
    with pytest.raises(ValueError):
        validate_theme_tokens(tokens)


def test_validate_rejects_bad_key() -> None:
    with pytest.raises(ValueError):
        validate_theme_tokens({"clave con espacios": 1})


def test_validate_rejects_oversized_string() -> None:
    with pytest.raises(ValueError):
        validate_theme_tokens({"color": "x" * 2049})


def test_validate_rejects_too_many_keys() -> None:
    tokens = {f"key_{i}": i for i in range(201)}
    with pytest.raises(ValueError):
        validate_theme_tokens(tokens)


def test_validate_rejects_non_primitive_values() -> None:
    with pytest.raises(ValueError):
        validate_theme_tokens({"payload": b"bytes-crudos"})


def test_validate_rejects_oversized_list() -> None:
    with pytest.raises(ValueError):
        validate_theme_tokens({"tags": ["t"] * 51})


def test_upsert_request_rejects_invalid_tokens() -> None:
    with pytest.raises(ValidationError):
        ThemeUpsertRequest(tokens={"key con espacio": 1})


def test_upsert_request_accepts_valid_tokens() -> None:
    request = ThemeUpsertRequest(tokens=dict(_GOOD))
    assert request.tokens["radius"] == 4
