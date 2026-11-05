from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from .model import Requirement, TasksDoc, TaskState, parse_requirements, parse_tasks
from .paths import SpecPaths
from .text import code_spans, read_lines
from .traceability import Traceability, TraceabilityError, load_traceability

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "node_modules",
    "__pycache__",
    ".next",
    ".turbo",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".playwright-mcp",
    "dist",
    "build",
    "coverage",
}
PATH_SUFFIX = re.compile(
    r"\.(py|sql|md|ts|tsx|js|mjs|json|ya?ml|toml|svg|cfg|ini|txt|sh|ps1)$", re.IGNORECASE
)
TEST_EVIDENCE = re.compile(
    r"\b(tests?|pgTAP|pytest|playwright|e2e|vectores|reservas|compras|casos|escenarios)\b",
    re.IGNORECASE,
)
CONTRADICTION = re.compile(
    r"\b(falta|faltan|pendiente|sin implementar|no implementado)\b", re.IGNORECASE
)
UPPER_TODO = re.compile(r"\bTODO\b")


@dataclass(frozen=True, slots=True)
class Artifact:
    token: str
    status: str
    path: str = ""


@dataclass(frozen=True, slots=True)
class TaskClaim:
    id: str
    status: str
    evidence: str
    artifacts: tuple[Artifact, ...]
    unverifiable: bool
    contradiction: str
    line: int


@dataclass(frozen=True, slots=True)
class RequirementState:
    id: str
    title: str
    status: str
    tasks: tuple[tuple[str, str], ...]

    @property
    def done(self) -> int:
        return sum(1 for _, status in self.tasks if status == "Hecho")

    @property
    def total(self) -> int:
        return len(self.tasks)


@dataclass(frozen=True, slots=True)
class WaveState:
    number: int
    title: str
    total: int
    done: int
    partial: int
    pending: int
    blocked: int
    unstarted: int


@dataclass(frozen=True, slots=True)
class ConvergenceResult:
    claims: tuple[TaskClaim, ...]
    requirements: tuple[RequirementState, ...]
    waves: tuple[WaveState, ...]
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def converged(self) -> bool:
        return not self.errors

    @property
    def done(self) -> int:
        return sum(1 for claim in self.claims if claim.status == "Hecho")


def converge(paths: SpecPaths) -> ConvergenceResult:
    tasks = parse_tasks(read_lines(paths.tasks))
    requirements = parse_requirements(read_lines(paths.requirements))
    errors: list[str] = []
    warnings: list[str] = []
    try:
        trace = load_traceability(paths.traceability)
    except TraceabilityError as error:
        trace = Traceability(requirements={})
        errors.append(str(error))

    index = _file_index(paths.root)
    claims = tuple(
        _build_claim(state, paths.root, index)
        for state in sorted(tasks.states.values(), key=lambda item: item.id)
    )
    for claim in claims:
        if claim.contradiction:
            errors.append(
                f"{claim.id} (línea {claim.line}): marcada Hecho pero la evidencia dice "
                f"'{claim.contradiction}': {claim.evidence}"
            )
        for artifact in claim.artifacts:
            if artifact.status == "missing" and claim.status == "Hecho":
                errors.append(
                    f"{claim.id} (línea {claim.line}): cita `{artifact.token}` y no existe"
                )
            elif artifact.status == "ambiguous" and claim.status == "Hecho":
                warnings.append(f"{claim.id}: `{artifact.token}` es ambiguo ({artifact.path})")
        if claim.unverifiable:
            warnings.append(
                f"{claim.id} (línea {claim.line}): evidencia sin test, comando ni artefacto"
            )

    requirement_states = tuple(
        _requirement_state(requirement, trace, tasks) for requirement in requirements
    )
    waves = _wave_states(tasks)
    return ConvergenceResult(
        claims=claims,
        requirements=requirement_states,
        waves=waves,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _build_claim(
    state: TaskState,
    root: Path,
    index: dict[str, list[str]],
) -> TaskClaim:
    artifacts = tuple(_classify(token, root, index) for token in code_spans(state.evidence))
    has_artifact = any(artifact.status == "resolved" for artifact in artifacts)
    has_test = bool(TEST_EVIDENCE.search(state.evidence))
    contradiction = ""
    if state.status == "Hecho":
        match = CONTRADICTION.search(state.evidence) or UPPER_TODO.search(state.evidence)
        contradiction = match.group(0) if match else ""
    return TaskClaim(
        id=state.id,
        status=state.status,
        evidence=state.evidence,
        artifacts=artifacts,
        unverifiable=state.status == "Hecho" and not has_artifact and not has_test,
        contradiction=contradiction,
        line=state.line,
    )


def _file_index(root: Path) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for current, directories, files in os.walk(root):
        directories[:] = [name for name in directories if name not in SKIP_DIRS]
        for name in files:
            if not PATH_SUFFIX.search(name):
                continue
            relative = Path(current, name).relative_to(root).as_posix()
            index.setdefault(name, []).append(relative)
    return index


def _classify(token: str, root: Path, index: dict[str, list[str]]) -> Artifact:
    value = token.strip()
    if not value or " " in value:
        return Artifact(token, "ignored")
    if any(char in value for char in "*<>${}"):
        return Artifact(token, "ignored")
    if value.startswith(("/", "#", "http://", "https://", "mailto:")):
        return Artifact(token, "ignored")
    clean = value.rstrip(".,;:)")
    if "/" in clean or "\\" in clean:
        candidate = root / clean.replace("\\", "/")
        if candidate.exists():
            return Artifact(token, "resolved", candidate.relative_to(root).as_posix())
        return Artifact(token, "missing")
    if PATH_SUFFIX.search(clean):
        matches = index.get(Path(clean).name, [])
        if len(matches) == 1:
            return Artifact(token, "resolved", matches[0])
        if len(matches) > 1:
            return Artifact(token, "ambiguous", ", ".join(sorted(matches)))
        return Artifact(token, "missing")
    return Artifact(token, "ignored")


def _requirement_state(
    requirement: Requirement, trace: Traceability, tasks: TasksDoc
) -> RequirementState:
    entry = trace.requirements.get(requirement.id)
    task_ids = entry.tasks if entry is not None else ()
    rows = tuple(
        (task_id, tasks.states[task_id].status if task_id in tasks.states else "Pendiente")
        for task_id in task_ids
    )
    if not rows:
        status = "SIN_TRAZA"
    elif all(row_status == "Hecho" for _, row_status in rows):
        status = "CONVERGED"
    elif all(row_status == "Pendiente" for _, row_status in rows):
        status = "PENDIENTE"
    else:
        status = "PARCIAL"
    return RequirementState(
        id=requirement.id,
        title=requirement.title,
        status=status,
        tasks=rows,
    )


def _wave_states(tasks: TasksDoc) -> tuple[WaveState, ...]:
    waves: list[WaveState] = []
    for number, title in sorted(tasks.wave_titles.items()):
        definitions = [item for item in tasks.definitions.values() if item.wave == number]
        statuses = [
            tasks.states[item.id].status if item.id in tasks.states else "Sin estado"
            for item in definitions
        ]
        waves.append(
            WaveState(
                number=number,
                title=title,
                total=len(definitions),
                done=statuses.count("Hecho"),
                partial=statuses.count("Parcial"),
                pending=statuses.count("Pendiente"),
                blocked=statuses.count("Bloqueado"),
                unstarted=statuses.count("Sin estado"),
            )
        )
    return tuple(waves)


def format_convergence_text(result: ConvergenceResult) -> str:
    lines = [
        f"Convergencia: {'CONVERGED' if result.converged else 'NOT CONVERGED'}",
        (
            f"Tareas con estado: {len(result.claims)} "
            f"(Hecho: {result.done}, Parcial: "
            f"{sum(1 for claim in result.claims if claim.status == 'Parcial')}, "
            f"Pendiente: {sum(1 for claim in result.claims if claim.status == 'Pendiente')})"
        ),
        (
            "Requisitos: "
            f"{sum(1 for item in result.requirements if item.status == 'CONVERGED')} converged, "
            f"{sum(1 for item in result.requirements if item.status == 'PARCIAL')} parcial, "
            f"{sum(1 for item in result.requirements if item.status == 'PENDIENTE')} pendiente, "
            f"{sum(1 for item in result.requirements if item.status == 'SIN_TRAZA')} sin traza"
        ),
        "",
    ]
    if result.errors:
        lines.append("Contradicciones:")
        lines.extend(f"  ERROR {message}" for message in result.errors)
        lines.append("")
    if result.warnings:
        lines.append("Advertencias:")
        lines.extend(f"  WARN  {message}" for message in result.warnings)
        lines.append("")
    lines.append("Olas:")
    for wave in result.waves:
        lines.append(
            f"  W{wave.number:<2} {wave.title:<38} "
            f"{wave.done}/{wave.total} Hecho, {wave.partial} Parcial, "
            f"{wave.pending} Pendiente, {wave.blocked} Bloqueado, {wave.unstarted} sin estado"
        )
    if not result.errors and not result.warnings:
        lines.append("")
        lines.append("Sin hallazgos.")
    return "\n".join(lines)


def format_convergence_markdown(result: ConvergenceResult, generated: str) -> str:
    verdict = "CONVERGED" if result.converged else "NOT CONVERGED"
    lines = [
        "# Converge — Storefront Platform V2",
        "",
        f"- **Generado:** {generated}",
        f"- **Estado:** {verdict}",
        f"- **Tareas con estado:** {len(result.claims)}",
        "",
        "## Contradicciones",
        "",
    ]
    if result.errors:
        lines.extend(f"- {message}" for message in result.errors)
    else:
        lines.append("- Ninguna.")
    lines.extend(["", "## Evidencia no verificable", ""])
    if result.warnings:
        lines.extend(f"- {message}" for message in result.warnings)
    else:
        lines.append("- Ninguna.")
    lines.extend(
        [
            "",
            "## Requisitos",
            "",
            "| Requisito | Estado | Hechas | Total | Tareas |",
            "|---|---|---|---|---|",
        ]
    )
    for item in result.requirements:
        tasks = ", ".join(f"{task} ({status})" for task, status in item.tasks)
        lines.append(f"| {item.id} | {item.status} | {item.done} | {item.total} | {tasks} |")
    lines.extend(
        [
            "",
            "## Olas",
            "",
            "| Ola | Foco | Hecho | Parcial | Pendiente | Bloqueado | Sin estado | Total |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    for wave in result.waves:
        lines.append(
            f"| W{wave.number} | {wave.title} | {wave.done} | {wave.partial} | "
            f"{wave.pending} | {wave.blocked} | {wave.unstarted} | {wave.total} |"
        )
    return "\n".join(lines) + "\n"


def format_convergence_json(result: ConvergenceResult) -> str:
    payload = {
        "converged": result.converged,
        "tasks": len(result.claims),
        "errors": list(result.errors),
        "warnings": list(result.warnings),
        "requirements": [
            {
                "id": item.id,
                "status": item.status,
                "done": item.done,
                "total": item.total,
                "tasks": [{"id": task, "status": status} for task, status in item.tasks],
            }
            for item in result.requirements
        ],
        "waves": [
            {
                "number": wave.number,
                "title": wave.title,
                "done": wave.done,
                "partial": wave.partial,
                "pending": wave.pending,
                "blocked": wave.blocked,
                "unstarted": wave.unstarted,
                "total": wave.total,
            }
            for wave in result.waves
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)
