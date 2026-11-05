from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

from .model import (
    Decision,
    DesignSection,
    Requirement,
    TasksDoc,
    parse_adr_statuses,
    parse_decisions,
    parse_design_sections,
    parse_requirements,
    parse_tasks,
)
from .paths import SpecPaths
from .text import iter_links, read_lines, strip_accents
from .traceability import Traceability, TraceabilityError, load_traceability

SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}
ALLOWED_PRIORITIES = {"MUST", "SHOULD", "COULD"}
ADR_REF = re.compile(r"\bADR[- ]?(\d{4})\b")


@dataclass(frozen=True, slots=True)
class Issue:
    code: str
    severity: str
    message: str
    path: Path
    line: int = 0

    def render(self, paths: SpecPaths) -> str:
        location = paths.relative(self.path)
        if self.line:
            location = f"{location}:{self.line}"
        return f"{self.severity:<7} {self.code:<26} {location}  {self.message}"


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    issues: tuple[Issue, ...]
    requirements: tuple[Requirement, ...]
    decisions: tuple[Decision, ...]
    tasks: TasksDoc
    trace: Traceability

    def count(self, severity: str) -> int:
        return sum(1 for issue in self.issues if issue.severity == severity)

    @property
    def failed(self) -> bool:
        return any(issue.severity == "error" for issue in self.issues)


def analyze(paths: SpecPaths) -> AnalysisResult:
    issues: list[Issue] = []
    requirement_lines = read_lines(paths.requirements)
    requirements = parse_requirements(requirement_lines)
    design_lines = read_lines(paths.design)
    design_sections = parse_design_sections(design_lines)
    task_lines = read_lines(paths.tasks)
    tasks = parse_tasks(task_lines)
    decisions: list[Decision] = []
    for decision_path in paths.decisions:
        decisions.extend(parse_decisions(read_lines(decision_path), decision_path))

    trace = _load_trace(paths, issues)
    _check_requirements(paths, requirements, issues)
    _check_tasks(paths, tasks, issues)
    _check_traceability(paths, requirements, design_sections, tasks, trace, issues)
    _check_decisions(decisions, issues)
    _check_adr_refs(paths, issues)
    _check_links(paths, issues)

    ordered = sorted(
        issues,
        key=lambda issue: (SEVERITY_ORDER.get(issue.severity, 9), str(issue.path), issue.line),
    )
    return AnalysisResult(
        issues=tuple(ordered),
        requirements=tuple(requirements),
        decisions=tuple(decisions),
        tasks=tasks,
        trace=trace,
    )


def _load_trace(paths: SpecPaths, issues: list[Issue]) -> Traceability:
    try:
        return load_traceability(paths.traceability)
    except TraceabilityError as error:
        issues.append(
            Issue(
                code="trace.invalid",
                severity="error",
                message=str(error),
                path=paths.traceability,
            )
        )
        return Traceability(requirements={})


def _check_requirements(
    paths: SpecPaths, requirements: list[Requirement], issues: list[Issue]
) -> None:
    seen: dict[str, Requirement] = {}
    for requirement in requirements:
        if requirement.id in seen:
            issues.append(
                Issue(
                    code="req.duplicate_id",
                    severity="error",
                    message=f"Requisito duplicado: {requirement.id}",
                    path=paths.requirements,
                    line=requirement.line,
                )
            )
        seen[requirement.id] = requirement
        if strip_accents(requirement.priority).upper() not in ALLOWED_PRIORITIES:
            issues.append(
                Issue(
                    code="req.unknown_priority",
                    severity="error",
                    message=(
                        f"{requirement.id}: prioridad '{requirement.priority}' "
                        "no es Must/Should/Could"
                    ),
                    path=paths.requirements,
                    line=requirement.line,
                )
            )
        if not requirement.has_criteria:
            issues.append(
                Issue(
                    code="req.no_criteria",
                    severity="warning",
                    message=f"{requirement.id}: no tiene criterios de aceptación",
                    path=paths.requirements,
                    line=requirement.line,
                )
            )
    if not requirements:
        issues.append(
            Issue(
                code="req.empty",
                severity="error",
                message="No se encontró ningún requisito con ID",
                path=paths.requirements,
            )
        )


def _check_tasks(paths: SpecPaths, tasks: TasksDoc, issues: list[Issue]) -> None:
    if not tasks.definitions:
        issues.append(
            Issue(
                code="task.empty",
                severity="error",
                message="No se encontraron tareas en las olas",
                path=paths.tasks,
            )
        )
    for wave, _title in sorted(tasks.wave_titles.items()):
        if not any(definition.wave == wave for definition in tasks.definitions.values()):
            issues.append(
                Issue(
                    code="task.wave_empty",
                    severity="error",
                    message=f"Wave {wave} no tiene tareas",
                    path=paths.tasks,
                )
            )
    for task_id, state in tasks.states.items():
        definition = tasks.definitions.get(task_id)
        if definition is None:
            issues.append(
                Issue(
                    code="task.undefined",
                    severity="error",
                    message=f"{task_id}: tiene estado pero no está definida en ninguna ola",
                    path=paths.tasks,
                    line=state.line,
                )
            )
            continue
        if state.status not in {"Pendiente", "Parcial", "Hecho", "Bloqueado"}:
            issues.append(
                Issue(
                    code="task.status_invalid",
                    severity="error",
                    message=f"{task_id}: estado '{state.status}' no es válido",
                    path=paths.tasks,
                    line=state.line,
                )
            )
        if state.status == "Hecho" and not state.evidence:
            issues.append(
                Issue(
                    code="task.hecho_without_evidence",
                    severity="error",
                    message=f"{task_id}: marcada Hecho sin evidencia",
                    path=paths.tasks,
                    line=state.line,
                )
            )
        if state.status == "Parcial" and not re.search(r"\bfalta", state.evidence, re.IGNORECASE):
            issues.append(
                Issue(
                    code="task.parcial_without_gap",
                    severity="warning",
                    message=f"{task_id}: marcada Parcial sin decir qué falta",
                    path=paths.tasks,
                    line=state.line,
                )
            )


def _check_traceability(
    paths: SpecPaths,
    requirements: list[Requirement],
    design_sections: dict[str, DesignSection],
    tasks: TasksDoc,
    trace: Traceability,
    issues: list[Issue],
) -> None:
    requirement_ids = {requirement.id for requirement in requirements}
    mapped_tasks: set[str] = set()
    for requirement_id, entry in sorted(trace.requirements.items()):
        if requirement_id not in requirement_ids:
            issues.append(
                Issue(
                    code="trace.unknown_requirement",
                    severity="error",
                    message=f"{requirement_id}: trazado pero no existe en requirements.md",
                    path=paths.traceability,
                )
            )
        if not entry.design:
            issues.append(
                Issue(
                    code="trace.no_design",
                    severity="error",
                    message=f"{requirement_id}: sin sección de diseño asociada",
                    path=paths.traceability,
                )
            )
        if not entry.tasks:
            issues.append(
                Issue(
                    code="trace.no_tasks",
                    severity="error",
                    message=f"{requirement_id}: sin tareas asociadas",
                    path=paths.traceability,
                )
            )
        for section in entry.design:
            if section not in design_sections:
                issues.append(
                    Issue(
                        code="trace.unknown_design",
                        severity="error",
                        message=f"{requirement_id}: la sección de diseño {section} no existe",
                        path=paths.traceability,
                    )
                )
        for task_id in entry.tasks:
            mapped_tasks.add(task_id)
            if task_id not in tasks.definitions:
                issues.append(
                    Issue(
                        code="trace.unknown_task",
                        severity="error",
                        message=f"{requirement_id}: la tarea {task_id} no existe en tasks.md",
                        path=paths.traceability,
                    )
                )
    for requirement in requirements:
        if requirement.id not in trace.requirements:
            issues.append(
                Issue(
                    code="trace.missing",
                    severity="error",
                    message=f"{requirement.id}: no está en docs/spec/traceability.json",
                    path=paths.requirements,
                    line=requirement.line,
                )
            )
    for task_id, definition in sorted(tasks.definitions.items()):
        if task_id not in mapped_tasks:
            issues.append(
                Issue(
                    code="task.unmapped",
                    severity="warning",
                    message=f"{task_id}: no cubre ningún requisito",
                    path=paths.tasks,
                    line=definition.line,
                )
            )


def _check_decisions(decisions: list[Decision], issues: list[Issue]) -> None:
    seen: set[tuple[Path, str]] = set()
    for decision in decisions:
        key = (decision.path, decision.id)
        if key in seen:
            issues.append(
                Issue(
                    code="decision.duplicate_id",
                    severity="error",
                    message=f"{decision.id}: decisión duplicada",
                    path=decision.path,
                    line=decision.line,
                )
            )
        seen.add(key)
        if decision.status == "DESCONOCIDA":
            issues.append(
                Issue(
                    code="decision.status_unknown",
                    severity="error",
                    message=f"{decision.id}: no tiene línea de estado reconocible",
                    path=decision.path,
                    line=decision.line,
                )
            )
        elif decision.is_open:
            issues.append(
                Issue(
                    code="decision.open",
                    severity="warning",
                    message=f"{decision.id} ({decision.priority}): sigue en {decision.status}",
                    path=decision.path,
                    line=decision.line,
                )
            )


def _check_adr_refs(paths: SpecPaths, issues: list[Issue]) -> None:
    sources = [paths.requirements, paths.design, paths.tasks, *paths.decisions, *paths.steering]
    spec_dir = paths.requirements.parent
    sources.extend(sorted(spec_dir.glob("*.md")))
    existing = (
        {path.name[:4] for path in paths.adr_dir.glob("*.md")} if paths.adr_dir.is_dir() else set()
    )
    referenced: set[str] = set()
    for source in sources:
        for index, line in enumerate(read_lines(source), start=1):
            for match in ADR_REF.finditer(line):
                number = match.group(1)
                referenced.add(number)
                if number not in existing:
                    issues.append(
                        Issue(
                            code="adr.missing_file",
                            severity="error",
                            message=f"ADR-{number} referenciado pero no existe en docs/adr/",
                            path=source,
                            line=index,
                        )
                    )
    for adr in parse_adr_statuses(paths.adr_dir):
        if "propuesta" in strip_accents(adr.status).lower():
            issues.append(
                Issue(
                    code="adr.proposal",
                    severity="warning",
                    message=f"ADR-{adr.number} sigue en propuesta",
                    path=adr.path,
                    line=adr.line,
                )
            )
        if adr.number not in referenced:
            issues.append(
                Issue(
                    code="adr.unreferenced",
                    severity="info",
                    message=(
                        f"ADR-{adr.number} no está referenciado en spec, "
                        "decisiones ni steering"
                    ),
                    path=adr.path,
                )
            )


def _check_links(paths: SpecPaths, issues: list[Issue]) -> None:
    sources = [
        paths.requirements,
        paths.design,
        paths.tasks,
        *paths.decisions,
        *paths.steering,
        paths.adr_dir / "README.md",
    ]
    for source in sources:
        if not source.is_file():
            continue
        for line_number, target in iter_links(read_lines(source)):
            if _is_external(target):
                continue
            clean = unquote(target.split("#", 1)[0].split("?", 1)[0])
            if not clean:
                continue
            resolved = (source.parent / clean).resolve()
            if not resolved.exists():
                issues.append(
                    Issue(
                        code="link.broken",
                        severity="error",
                        message=f"Enlace roto: {target}",
                        path=source,
                        line=line_number,
                    )
                )


def _is_external(target: str) -> bool:
    prefixes = ("http://", "https://", "mailto:", "#", "tel:", "{{")
    return target.startswith(prefixes) or target.startswith("/")


def format_issues(result: AnalysisResult, paths: SpecPaths) -> str:
    lines = [
        f"Spec: {paths.requirements.parent.relative_to(paths.root).as_posix()}",
        (
            f"Requisitos: {len(result.requirements)} | "
            f"Tareas: {len(result.tasks.definitions)} | "
            f"Decisiones: {len(result.decisions)}"
        ),
        (
            f"Hallazgos: {result.count('error')} errores, "
            f"{result.count('warning')} warnings, {result.count('info')} info"
        ),
        "",
    ]
    lines.extend(issue.render(paths) for issue in result.issues)
    if not result.issues:
        lines.append("Sin hallazgos.")
    return "\n".join(lines)


def format_issues_json(result: AnalysisResult, paths: SpecPaths) -> str:
    payload = {
        "summary": {
            "requirements": len(result.requirements),
            "tasks": len(result.tasks.definitions),
            "decisions": len(result.decisions),
            "errors": result.count("error"),
            "warnings": result.count("warning"),
            "info": result.count("info"),
        },
        "issues": [
            {
                "code": issue.code,
                "severity": issue.severity,
                "message": issue.message,
                "path": paths.relative(issue.path),
                "line": issue.line,
            }
            for issue in result.issues
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def issue_counter(result: AnalysisResult) -> Counter[str]:
    return Counter(issue.code for issue in result.issues)
