from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .model import STATUS_RANK, parse_tasks
from .paths import SpecPaths
from .text import read_lines

RULE_TYPES = {"file_exists", "file_contains", "file_not_contains", "task_status"}


class ProfileError(ValueError):
    """Perfil regulatorio inválido o inexistente."""


@dataclass(frozen=True, slots=True)
class Control:
    id: str
    title: str
    rule: dict[str, object]
    evidence: str


@dataclass(frozen=True, slots=True)
class Profile:
    id: str
    title: str
    sources: tuple[str, ...]
    controls: tuple[Control, ...]


@dataclass(frozen=True, slots=True)
class ControlResult:
    id: str
    title: str
    status: str
    detail: str
    evidence: str


@dataclass(frozen=True, slots=True)
class ProfileReport:
    profile: Profile
    results: tuple[ControlResult, ...]

    def count(self, status: str) -> int:
        return sum(1 for result in self.results if result.status == status)

    @property
    def failed(self) -> bool:
        return any(result.status == "FAIL" for result in self.results)


def load_profiles(directory: Path) -> list[Profile]:
    if not directory.is_dir():
        return []
    profiles: list[Profile] = []
    for path in sorted(directory.glob("*.json")):
        profiles.append(_load_profile(path))
    return profiles


def load_profile(directory: Path, profile_id: str) -> Profile:
    for profile in load_profiles(directory):
        if profile.id == profile_id:
            return profile
    available = ", ".join(profile.id for profile in load_profiles(directory)) or "ninguno"
    raise ProfileError(f"Perfil '{profile_id}' no existe. Disponibles: {available}")


def _load_profile(path: Path) -> Profile:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as error:
        raise ProfileError(f"JSON inválido en {path}: {error}") from error
    if not isinstance(payload, dict):
        raise ProfileError(f"{path} debe contener un objeto JSON")
    profile_id = payload.get("id")
    title = payload.get("title")
    raw_controls = payload.get("controls")
    if not isinstance(profile_id, str) or not isinstance(title, str):
        raise ProfileError(f"{path} necesita 'id' y 'title' de tipo string")
    if not isinstance(raw_controls, list):
        raise ProfileError(f"{path} necesita una lista 'controls'")
    controls: list[Control] = []
    for raw in raw_controls:
        if not isinstance(raw, dict):
            raise ProfileError(f"{path}: control inválido")
        control_id = raw.get("id")
        control_title = raw.get("title")
        rule = raw.get("rule")
        if not isinstance(control_id, str) or not isinstance(control_title, str):
            raise ProfileError(f"{path}: cada control necesita 'id' y 'title'")
        if not isinstance(rule, dict) or rule.get("type") not in RULE_TYPES:
            raise ProfileError(f"{path}: control {control_id} tiene una regla inválida")
        controls.append(
            Control(
                id=control_id,
                title=control_title,
                rule=dict(rule),
                evidence=str(raw.get("evidence", "")),
            )
        )
    sources = payload.get("sources", [])
    return Profile(
        id=profile_id,
        title=title,
        sources=tuple(str(item) for item in sources) if isinstance(sources, list) else (),
        controls=tuple(controls),
    )


def check_profile(profile: Profile, paths: SpecPaths) -> ProfileReport:
    results = tuple(_check_control(control, paths) for control in profile.controls)
    return ProfileReport(profile=profile, results=results)


def _check_control(control: Control, paths: SpecPaths) -> ControlResult:
    rule_type = str(control.rule.get("type"))
    try:
        status, detail = _evaluate(rule_type, control.rule, paths)
    except (KeyError, ValueError) as error:
        status, detail = "UNKNOWN", f"regla inválida: {error}"
    return ControlResult(
        id=control.id,
        title=control.title,
        status=status,
        detail=detail,
        evidence=control.evidence,
    )


def _evaluate(rule_type: str, rule: dict[str, object], paths: SpecPaths) -> tuple[str, str]:
    if rule_type == "file_exists":
        target = paths.root / str(rule["path"])
        if target.exists():
            return "PASS", f"existe {rule['path']}"
        return "FAIL", f"no existe {rule['path']}"
    if rule_type == "task_status":
        task_id = str(rule["task"])
        minimum = str(rule.get("min", "Hecho"))
        tasks = parse_tasks(read_lines(paths.tasks))
        state = tasks.states.get(task_id)
        if state is None:
            if task_id in tasks.definitions:
                return "FAIL", f"{task_id} definida pero sin estado (Pendiente)"
            return "UNKNOWN", f"{task_id} no existe en tasks.md"
        if state.status == "Bloqueado":
            return "FAIL", f"{task_id} está bloqueada"
        if STATUS_RANK.get(state.status, 0) >= STATUS_RANK.get(minimum, 2):
            return "PASS", f"{task_id} está en {state.status}"
        return "FAIL", f"{task_id} está en {state.status} (mínimo {minimum})"
    pattern = str(rule["pattern"])
    compiled = re.compile(pattern)
    files = _expand(str(rule["glob"]), paths)
    if rule_type == "file_not_contains":
        if not files:
            return "UNKNOWN", f"sin archivos para {rule['glob']}"
        offenders = [paths.relative(path) for path in files if compiled.search(_read(path))]
        if offenders:
            return "FAIL", "coincide en " + ", ".join(offenders)
        return "PASS", f"0 coincidencias en {len(files)} archivo(s)"
    if rule_type == "file_contains":
        if not files:
            return "UNKNOWN", f"sin archivos para {rule['glob']}"
        matched = 0
        files_with_match = 0
        for path in files:
            hits = len(compiled.findall(_read(path)))
            matched += hits
            files_with_match += 1 if hits else 0
        minimum = int(str(rule.get("min_count", 1)))
        if matched >= minimum:
            return "PASS", f"{matched} coincidencia(s) en {files_with_match} archivo(s)"
        return "FAIL", f"{matched} coincidencia(s), mínimo {minimum}"
    return "UNKNOWN", f"tipo de regla desconocido: {rule_type}"


def _expand(pattern: str, paths: SpecPaths) -> list[Path]:
    return sorted(path for path in paths.root.glob(pattern) if path.is_file())


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def format_profiles(profiles: list[Profile]) -> str:
    if not profiles:
        return "No hay perfiles regulatorios en docs/regulatory/profiles/."
    lines = ["Perfiles regulatorios:", ""]
    for profile in profiles:
        lines.append(f"  {profile.id:<12} {profile.title} ({len(profile.controls)} controles)")
        for source in profile.sources:
            lines.append(f"               fuente: {source}")
    return "\n".join(lines)


def format_profile_text(report: ProfileReport) -> str:
    lines = [
        f"Perfil: {report.profile.id} — {report.profile.title}",
        (
            f"Controles: {len(report.results)} | PASS {report.count('PASS')} | "
            f"FAIL {report.count('FAIL')} | UNKNOWN {report.count('UNKNOWN')}"
        ),
        "",
    ]
    for result in report.results:
        lines.append(f"  {result.status:<7} {result.id:<14} {result.title}")
        lines.append(f"          {result.detail}")
        if result.evidence:
            lines.append(f"          evidencia: {result.evidence}")
    return "\n".join(lines)


def format_profile_markdown(report: ProfileReport) -> str:
    lines = [
        f"# Perfil regulatorio — {report.profile.title}",
        "",
        f"- **ID:** `{report.profile.id}`",
        f"- **Controles:** {len(report.results)}",
        f"- **Resultado:** PASS {report.count('PASS')} · FAIL {report.count('FAIL')} · "
        f"UNKNOWN {report.count('UNKNOWN')}",
        "",
    ]
    if report.profile.sources:
        lines.append("**Fuentes:** " + ", ".join(f"`{item}`" for item in report.profile.sources))
        lines.append("")
    lines.extend(
        [
            "| Control | Estado | Detalle | Evidencia esperada |",
            "|---|---|---|---|",
        ]
    )
    for result in report.results:
        lines.append(
            f"| {result.id} — {result.title} | {result.status} | {result.detail} | "
            f"{result.evidence} |"
        )
    return "\n".join(lines) + "\n"


def format_profile_json(report: ProfileReport) -> str:
    payload = {
        "profile": report.profile.id,
        "title": report.profile.title,
        "summary": {
            "total": len(report.results),
            "pass": report.count("PASS"),
            "fail": report.count("FAIL"),
            "unknown": report.count("UNKNOWN"),
        },
        "controls": [
            {
                "id": result.id,
                "title": result.title,
                "status": result.status,
                "detail": result.detail,
                "evidence": result.evidence,
            }
            for result in report.results
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)
