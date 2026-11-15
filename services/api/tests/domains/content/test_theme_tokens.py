from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.domains.content.schemas import (
    COLOR_SCHEMES,
    FONT_REGISTRY,
    MOTION_LEVELS,
    THEME_PRESETS,
    ThemeTokensV1,
    ThemeUpsertRequest,
    validate_theme_tokens,
)

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


def test_theme_tokens_v1_accepts_nova_preset() -> None:
    payload = {
        "schema_version": 1,
        "preset": "nova",
        "color_scheme": "dark",
        "font_display": "Unbounded",
        "font_body": "Geist",
        "font_mono": "Geist Mono",
        "colors": {
            "surface": "oklch(0.155 0.012 265)",
            "surface_2": "oklch(0.205 0.015 265)",
            "ink": "oklch(0.975 0.004 265)",
            "signal": "oklch(0.88 0.19 128)",
            "muted": "oklch(0.76 0.015 265)",
            "hairline": "oklch(0.34 0.015 265)",
        },
        "radius_px": 0,
        "clip_angle_px": 10,
        "motion": "technical",
    }
    request = ThemeUpsertRequest(tokens=payload)
    assert request.tokens["preset"] == "nova"
    model = ThemeTokensV1.model_validate(payload)
    assert model.font_display == "Unbounded"


def test_theme_tokens_v1_rejects_unregistered_font_or_preset() -> None:
    with pytest.raises(ValidationError):
        ThemeUpsertRequest(tokens={"preset": "cyberpunk-unknown"})

    with pytest.raises(ValidationError):
        ThemeUpsertRequest(tokens={"font_display": "Comic Sans MS"})

    with pytest.raises(ValidationError):
        ThemeUpsertRequest(
            tokens={
                "schema_version": 1,
                "preset": "nova",
                "unknown_field": "forbidden",
            }
        )


def test_registry_parity_between_python_and_typescript() -> None:
    config_ts = (
        Path(__file__).resolve().parents[5] / "packages" / "config" / "src" / "index.ts"
    ).read_text(encoding="utf-8")

    presets_match = re.search(r"THEME_PRESETS\s*=\s*\[(.*?)\]\s*as const", config_ts, re.S)
    fonts_match = re.search(r"FONT_REGISTRY\s*=\s*\[(.*?)\]\s*as const", config_ts, re.S)
    schemes_match = re.search(r"COLOR_SCHEMES\s*=\s*\[(.*?)\]\s*as const", config_ts, re.S)
    motions_match = re.search(r"MOTION_LEVELS\s*=\s*\[(.*?)\]\s*as const", config_ts, re.S)

    assert presets_match is not None
    assert fonts_match is not None
    assert schemes_match is not None
    assert motions_match is not None

    ts_presets = tuple(re.findall(r'"([^"]+)"', presets_match.group(1)))
    ts_fonts = tuple(re.findall(r'"([^"]+)"', fonts_match.group(1)))
    ts_schemes = tuple(re.findall(r'"([^"]+)"', schemes_match.group(1)))
    ts_motions = tuple(re.findall(r'"([^"]+)"', motions_match.group(1)))

    assert ts_presets == THEME_PRESETS
    assert ts_fonts == FONT_REGISTRY
    assert ts_schemes == COLOR_SCHEMES
    assert ts_motions == MOTION_LEVELS
