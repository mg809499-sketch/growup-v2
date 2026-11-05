from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .model import (
    Decision,
    DecisionOption,
    parse_adr_statuses,
    parse_decisions,
    parse_requirements,
)
from .paths import SpecPaths
from .text import read_lines, strip_accents

PRIORITY_RANK = {"CRITICA": 0, "IMPORTANTE": 1, "A_CONSIDERAR": 2}
REQUIREMENT_PRIORITY = {"MUST": "IMPORTANTE", "SHOULD": "A_CONFIRMAR", "COULD": "A_CONSIDERAR"}
AMBIGUITY = re.compile(
    r"\b(TBD|TODO|por definir|sin definir|a confirmar|pendiente de definici[oó]n)\b",
    re.IGNORECASE,
)
STOPWORDS = {
    "para",
    "como",
    "con",
    "del",
    "las",
    "los",
    "una",
    "uno",
    "por",
    "que",
    "sus",
    "sin",
    "the",
    "and",
}


@dataclass(frozen=True, slots=True)
class Question:
    id: str
    kind: str
    priority: str
    title: str
    detail: str
    options: tuple[DecisionOption, ...]
    recommendation: str
    blocking: bool
    path: Path
    line: int

    @property
    def rank(self) -> int:
        return PRIORITY_RANK.get(strip_accents(self.priority).upper(), 9)


def collect_questions(paths: SpecPaths, limit: int = 0) -> list[Question]:
    decisions = _load_decisions(paths)
    questions: list[Question] = []
    seen_titles: list[set[str]] = []

    for decision in decisions:
        if decision.is_open:
            question = Question(
                id=decision.id,
                kind="decision",
                priority=decision.priority or "A_CONFIRMAR",
                title=decision.title,
                detail=f"Decisión en {decision.status.lower()}; no se puede asumir en silencio.",
                options=decision.options,
                recommendation=decision.recommendation,
                blocking=strip_accents(decision.priority).upper() in {"CRITICA", "IMPORTANTE"},
                path=decision.path,
                line=decision.line,
            )
            _append_unique(question, questions, seen_titles)
            continue
        for pending in decision.pending:
            if not pending.text:
                continue
            question = Question(
                id=f"{decision.id}-P",
                kind="pending_derived",
                priority=decision.priority or "A_CONFIRMAR",
                title=pending.text,
                detail=f"Pendiente derivado de {decision.id} ({decision.title}).",
                options=(),
                recommendation="",
                blocking=False,
                path=decision.path,
                line=pending.line,
            )
            _append_unique(question, questions, seen_titles)

    design_lines = read_lines(paths.design)
    del design_lines

    for adr in parse_adr_statuses(paths.adr_dir):
        if "propuesta" in strip_accents(adr.status).lower():
            question = Question(
                id=f"ADR-{adr.number}",
                kind="adr_proposal",
                priority="IMPORTANTE",
                title=_strip_adr_prefix(adr.title),
                detail=f"ADR-{adr.number} está en propuesta; la arquitectura aún no es firme.",
                options=(),
                recommendation="",
                blocking=True,
                path=adr.path,
                line=adr.line,
            )
            _append_unique(question, questions, seen_titles)

    for requirement in parse_requirements(read_lines(paths.requirements)):
        if requirement.has_criteria:
            continue
        question = Question(
            id=requirement.id,
            kind="requirement_ambiguity",
            priority=REQUIREMENT_PRIORITY.get(
                strip_accents(requirement.priority).upper(), "A_CONFIRMAR"
            ),
            title=requirement.title,
            detail="Requisito sin criterios de aceptación verificables.",
            options=(),
            recommendation="",
            blocking=False,
            path=paths.requirements,
            line=requirement.line,
        )
        _append_unique(question, questions, seen_titles)

    for source in (paths.requirements, paths.design):
        for index, line in enumerate(read_lines(source), start=1):
            if not AMBIGUITY.search(line):
                continue
            question = Question(
                id=f"MARKER-{source.stem}-{index}",
                kind="marker",
                priority="A_CONFIRMAR",
                title=_collapse(line),
                detail="Marcador de ambigüedad en el documento fuente.",
                options=(),
                recommendation="",
                blocking=False,
                path=source,
                line=index,
            )
            _append_unique(question, questions, seen_titles)

    questions.sort(key=lambda question: (not question.blocking, question.rank, question.id))
    if limit > 0:
        return questions[:limit]
    return questions


def _load_decisions(paths: SpecPaths) -> list[Decision]:
    best: dict[str, Decision] = {}
    for path in paths.decisions:
        for decision in parse_decisions(read_lines(path), path):
            current = best.get(decision.id)
            if current is None or _decision_score(decision) > _decision_score(current):
                best[decision.id] = decision
    return [best[key] for key in sorted(best)]


def _decision_score(decision: Decision) -> tuple[int, int, int]:
    return (len(decision.options), len(decision.pending), len(decision.recommendation))


def _append_unique(question: Question, questions: list[Question], seen: list[set[str]]) -> bool:
    tokens = _tokens(question.title)
    for existing in seen:
        if _overlap(tokens, existing):
            return False
    questions.append(question)
    seen.append(tokens)
    return True


def _tokens(value: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", strip_accents(value).lower())
    return {word for word in words if len(word) > 4 and word not in STOPWORDS}


def _overlap(left: set[str], right: set[str]) -> bool:
    if not left or not right:
        return False
    shared = len(left & right)
    return shared >= 2 and shared / min(len(left), len(right)) >= 0.6


def _collapse(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lstrip("- ")).strip()


def _strip_adr_prefix(title: str) -> str:
    match = re.match(r"^ADR-\d{4}\s*[—–-]\s*(?P<rest>.+)$", title)
    return match.group("rest").strip() if match else title


def format_questions_text(questions: list[Question], paths: SpecPaths) -> str:
    if not questions:
        return "Sin preguntas abiertas: los documentos de decisión están cerrados."
    lines = [f"Preguntas abiertas: {len(questions)}", ""]
    for index, question in enumerate(questions, start=1):
        flag = "BLOQUEA" if question.blocking else "informativa"
        lines.append(f"[{index}] {question.id} ({question.priority}, {flag}) {question.title}")
        lines.append(f"    fuente: {paths.relative(question.path)}:{question.line}")
        if question.detail:
            lines.append(f"    detalle: {question.detail}")
        if question.options:
            options = " | ".join(
                f"{option.key}) {option.title}" for option in question.options
            )
            lines.append(f"    opciones: {options}")
        if question.recommendation:
            lines.append(f"    recomendación: {question.recommendation}")
        lines.append("")
    return "\n".join(lines).rstrip()


def format_questions_markdown(questions: list[Question], paths: SpecPaths) -> str:
    if not questions:
        return "## Clarify\n\nSin preguntas abiertas.\n"
    lines = [f"## Clarify — {len(questions)} preguntas", ""]
    for index, question in enumerate(questions, start=1):
        flag = "`bloquea`" if question.blocking else "`informativa`"
        lines.append(f"### {index}. {question.id} — {question.title}")
        lines.append("")
        lines.append(f"- **Prioridad:** {question.priority} | {flag}")
        lines.append(f"- **Fuente:** `{paths.relative(question.path)}:{question.line}`")
        if question.detail:
            lines.append(f"- **Detalle:** {question.detail}")
        if question.options:
            lines.append("")
            for option in question.options:
                detail = f" — {option.detail}" if option.detail else ""
                lines.append(f"  - **{option.key}.** {option.title}{detail}")
        if question.recommendation:
            lines.append("")
            lines.append(f"**Recomendación:** {question.recommendation}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def format_questions_json(questions: list[Question], paths: SpecPaths) -> str:
    payload = [
        {
            "id": question.id,
            "kind": question.kind,
            "priority": question.priority,
            "blocking": question.blocking,
            "title": question.title,
            "detail": question.detail,
            "options": [
                {"key": option.key, "title": option.title, "detail": option.detail}
                for option in question.options
            ],
            "recommendation": question.recommendation,
            "source": f"{paths.relative(question.path)}:{question.line}",
        }
        for question in questions
    ]
    return json.dumps(payload, indent=2, ensure_ascii=False)
