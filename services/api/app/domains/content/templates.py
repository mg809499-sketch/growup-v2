"""Plantillas predefinidas de e-commerce (starter/joyeria) — validadas con
los mismos esquemas que seusan para guardar borradores."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from app.core.errors import AppError
from app.domains.content.blocks import PageLayout

_DIR = Path(__file__).parent / "templates"


class TemplateSummary(BaseModel):
    template_id: str
    name: str
    description: str


def list_templates() -> list[TemplateSummary]:
    results: list[TemplateSummary] = []
    if not _DIR.is_dir():
        return results
    for path in sorted(_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            item = TemplateSummary(
                template_id=data["template_id"],
                name=data.get("name", path.stem),
                description=data.get("description", ""),
            )
            results.append(item)
        except Exception:
            continue
    return results


def load_template(template_id: str) -> PageLayout:
    if not template_id or "/" in template_id or "\\" in template_id:
        raise AppError("TEMPLATE_NOT_FOUND", "Plantilla no encontrada", 404)
    path = _DIR / f"{template_id}.json"
    if not path.is_file():
        raise AppError("TEMPLATE_NOT_FOUND", "Plantilla no encontrada", 404)
    raw = json.loads(path.read_text(encoding="utf-8"))
    blocks = raw.get("blocks")
    if not isinstance(blocks, list):
        raise AppError("TEMPLATE_INVALID", "Plantilla sin bloques", 422)
    try:
        return PageLayout(version=1, blocks=blocks)
    except Exception as exc:  # noqa: BLE001 - la validación de bloques pertenece al edge
        raise AppError(
            "TEMPLATE_INVALID",
            "La plantilla no pasó validación",
            422,
            {"reason": str(exc)},
        ) from exc
