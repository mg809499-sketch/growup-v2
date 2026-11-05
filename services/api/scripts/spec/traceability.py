from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


class TraceabilityError(ValueError):
    """El archivo de trazabilidad no existe o no es válido."""


@dataclass(frozen=True, slots=True)
class RequirementTrace:
    id: str
    design: tuple[str, ...]
    tasks: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Traceability:
    requirements: dict[str, RequirementTrace]


def load_traceability(path: Path) -> Traceability:
    if not path.is_file():
        raise TraceabilityError(f"No existe el mapa de trazabilidad: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as error:
        raise TraceabilityError(f"JSON inválido en {path}: {error}") from error
    if not isinstance(payload, dict):
        raise TraceabilityError(f"{path} debe contener un objeto JSON")
    raw_requirements = payload.get("requirements")
    if not isinstance(raw_requirements, dict):
        raise TraceabilityError(f"{path} no contiene la clave 'requirements'")
    requirements: dict[str, RequirementTrace] = {}
    for requirement_id, entry in raw_requirements.items():
        if not isinstance(entry, dict):
            raise TraceabilityError(f"Entrada inválida para {requirement_id}")
        design = entry.get("design", [])
        tasks = entry.get("tasks", [])
        if not isinstance(design, list) or not isinstance(tasks, list):
            raise TraceabilityError(f"{requirement_id}: 'design' y 'tasks' deben ser listas")
        requirements[requirement_id] = RequirementTrace(
            id=requirement_id,
            design=tuple(str(item) for item in design),
            tasks=tuple(str(item) for item in tasks),
        )
    return Traceability(requirements=requirements)


def tasks_for_requirement(trace: Traceability, requirement_id: str) -> tuple[str, ...]:
    entry = trace.requirements.get(requirement_id)
    return entry.tasks if entry is not None else ()
