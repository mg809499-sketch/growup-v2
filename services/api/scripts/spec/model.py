from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .text import strip_accents

REQUIREMENT_HEADER = re.compile(
    r"^\*\*(?P<id>[A-Z]{2,4}-\d{2})\s+[—–-]\s+(?P<title>.+?)\*\*\s*"
    r"\*\((?P<priority>[A-Za-z]+)\)\*",
)
WAVE_HEADING = re.compile(r"^##\s+Wave\s+(?P<wave>\d+)\s+[—–-]\s+(?P<title>.+?)\s*$")
TASK_ROW = re.compile(
    r"^\|\s*(?P<id>W\d-\d{2})\s*\|\s*(?P<title>[^|]*)\|\s*"
    r"(?P<depends>[^|]*)\|\s*(?P<acceptance>[^|]*)\|",
)
STATUS_ROW = re.compile(
    r"^\|\s*(?P<id>W\d-\d{2})\s*\|\s*(?P<status>[^|]*?)\s*\|\s*(?P<evidence>.*?)\s*\|\s*$",
)
DECISION_HEADING = re.compile(r"^##\s+(?P<id>D-\d{2})\s*[—–-]\s*(?P<title>.+?)\s*$")
DECISION_STATUS = re.compile(
    r"^\*\*(?P<priority>[^*]*?)\s*[—–-]\s*"
    r"(?P<status>CERRADA|PROPUESTA|ABIERTA|BORRADOR)(?P<extra>[^*]*)\*\*\s*$",
    re.IGNORECASE,
)
DECISION_OPTION = re.compile(
    r"^-\s+\*\*(?P<key>[A-Z])\.\s*(?P<title>[^*]+?)\*\*\s*(?P<detail>.*)$",
)
DECISION_RECOMMENDATION = re.compile(r"^\*\*Recomendaci[oó]n:\*\*\s*(?P<text>.+)$")
DECISION_PENDING = re.compile(r"^\*\*Pendientes?\s+derivad[oa]s?(?:[^:]*)?:\*\*\s*(?P<text>.*)$")
DESIGN_H2 = re.compile(r"^##\s+(?P<number>\d+)\.\s+(?P<title>.+?)\s*$")
DESIGN_H3 = re.compile(r"^###\s+(?P<number>\d+\.\d+)\s+(?P<title>.+?)\s*$")
ADR_STATUS = re.compile(r"^-\s+\*\*Estado:\*\*\s*(?P<status>.+)$")

VALID_STATUSES = ("Pendiente", "Parcial", "Hecho", "Bloqueado")
STATUS_RANK = {"Pendiente": 0, "Parcial": 1, "Hecho": 2, "Bloqueado": -1}

_STATUS_ALIASES = {
    "pendiente": "Pendiente",
    "parcial": "Parcial",
    "hecho": "Hecho",
    "hecha": "Hecho",
    "bloqueado": "Bloqueado",
}


def normalize_status(raw: str) -> str:
    return _STATUS_ALIASES.get(strip_accents(raw).strip().lower(), raw.strip())


def normalize_priority(raw: str) -> str:
    return strip_accents(raw).strip().upper()


@dataclass(frozen=True, slots=True)
class Requirement:
    id: str
    title: str
    priority: str
    line: int
    criteria: tuple[str, ...]

    @property
    def has_criteria(self) -> bool:
        return bool(self.criteria)


@dataclass(frozen=True, slots=True)
class TaskDefinition:
    id: str
    wave: int
    title: str
    depends: str
    acceptance: str
    line: int


@dataclass(frozen=True, slots=True)
class TaskState:
    id: str
    status: str
    evidence: str
    line: int


@dataclass(frozen=True, slots=True)
class TasksDoc:
    wave_titles: dict[int, str]
    definitions: dict[str, TaskDefinition]
    states: dict[str, TaskState]


@dataclass(frozen=True, slots=True)
class DecisionOption:
    key: str
    title: str
    detail: str


@dataclass(frozen=True, slots=True)
class PendingItem:
    text: str
    line: int


@dataclass(frozen=True, slots=True)
class Decision:
    id: str
    title: str
    priority: str
    status: str
    line: int
    options: tuple[DecisionOption, ...]
    recommendation: str
    pending: tuple[PendingItem, ...]
    path: Path

    @property
    def is_open(self) -> bool:
        return self.status != "CERRADA"


@dataclass(frozen=True, slots=True)
class DesignSection:
    number: str
    title: str
    line: int
    body: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OpenQuestion:
    text: str
    line: int


@dataclass(frozen=True, slots=True)
class AdrStatus:
    number: str
    title: str
    status: str
    line: int
    path: Path


def parse_adr_statuses(adr_dir: Path) -> list[AdrStatus]:
    statuses: list[AdrStatus] = []
    if not adr_dir.is_dir():
        return statuses
    for path in sorted(adr_dir.glob("*.md")):
        number = path.name[:4]
        if number == "0000" or not number.isdigit():
            continue
        title = ""
        status = ""
        line_number = 0
        for index, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
            stripped = line.strip()
            if not title and stripped.startswith("# "):
                title = stripped[2:].strip()
            match = ADR_STATUS.match(stripped)
            if match:
                status = match.group("status").strip()
                line_number = index
                break
        statuses.append(
            AdrStatus(
                number=number,
                title=title,
                status=status,
                line=line_number,
                path=path,
            )
        )
    return statuses


def _section_end(lines: list[str], start: int) -> int:
    for index in range(start, len(lines)):
        if lines[index].startswith("#"):
            return index
    return len(lines)


def parse_requirements(lines: list[str]) -> list[Requirement]:
    headers: list[tuple[int, re.Match[str]]] = []
    for index, line in enumerate(lines):
        match = REQUIREMENT_HEADER.match(line.strip())
        if match:
            headers.append((index, match))
    requirements: list[Requirement] = []
    for position, (start, match) in enumerate(headers):
        next_header = headers[position + 1][0] if position + 1 < len(headers) else len(lines)
        end = min(next_header, _section_end(lines, start + 1))
        criteria = tuple(
            line.strip()
            for line in lines[start + 1 : end]
            if line.strip().startswith(("- ", "* "))
        )
        requirements.append(
            Requirement(
                id=match.group("id"),
                title=match.group("title").strip(),
                priority=match.group("priority").strip(),
                line=start + 1,
                criteria=criteria,
            )
        )
    return requirements


def parse_tasks(lines: list[str]) -> TasksDoc:
    wave_titles: dict[int, str] = {}
    definitions: dict[str, TaskDefinition] = {}
    states: dict[str, TaskState] = {}
    wave: int | None = None
    in_states = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("## "):
            in_states = strip_accents(stripped.lower()).startswith("## estado actual")
            wave_match = WAVE_HEADING.match(stripped)
            wave = int(wave_match.group("wave")) if wave_match else None
            if wave_match:
                wave_titles[wave] = wave_match.group("title").strip()
            continue
        if in_states:
            status_match = STATUS_ROW.match(stripped)
            if status_match:
                task_id = status_match.group("id")
                states[task_id] = TaskState(
                    id=task_id,
                    status=normalize_status(status_match.group("status")),
                    evidence=status_match.group("evidence").strip(),
                    line=index + 1,
                )
            continue
        if wave is not None:
            task_match = TASK_ROW.match(stripped)
            if task_match:
                task_id = task_match.group("id")
                definitions[task_id] = TaskDefinition(
                    id=task_id,
                    wave=wave,
                    title=task_match.group("title").strip(),
                    depends=task_match.group("depends").strip(),
                    acceptance=task_match.group("acceptance").strip(),
                    line=index + 1,
                )
    return TasksDoc(wave_titles=wave_titles, definitions=definitions, states=states)


def _collect_pending(lines: list[str], start: int, inline: str) -> PendingItem:
    parts = [inline.strip()] if inline.strip() else []
    index = start + 1
    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped or stripped.startswith(("**", "#", "---")):
            break
        parts.append(stripped.lstrip("- ").strip())
        index += 1
    return PendingItem(text="; ".join(part for part in parts if part), line=start + 1)


def parse_decisions(lines: list[str], path: Path) -> list[Decision]:
    headings: list[tuple[int, re.Match[str]]] = []
    for index, line in enumerate(lines):
        match = DECISION_HEADING.match(line.strip())
        if match:
            headings.append((index, match))
    decisions: list[Decision] = []
    for position, (start, match) in enumerate(headings):
        end = headings[position + 1][0] if position + 1 < len(headings) else len(lines)
        priority = ""
        status = "DESCONOCIDA"
        options: list[DecisionOption] = []
        recommendation = ""
        pending: list[PendingItem] = []
        for index in range(start + 1, end):
            stripped = lines[index].strip()
            if not priority:
                status_match = DECISION_STATUS.match(stripped)
                if status_match:
                    priority = strip_accents(status_match.group("priority")).strip().upper()
                    status = status_match.group("status").upper()
                    continue
            option_match = DECISION_OPTION.match(stripped)
            if option_match:
                options.append(
                    DecisionOption(
                        key=option_match.group("key"),
                        title=option_match.group("title").strip(),
                        detail=option_match.group("detail").strip(),
                    )
                )
                continue
            recommendation_match = DECISION_RECOMMENDATION.match(stripped)
            if recommendation_match:
                recommendation = recommendation_match.group("text").strip()
                continue
            pending_match = DECISION_PENDING.match(stripped)
            if pending_match:
                pending.append(_collect_pending(lines, index, pending_match.group("text")))
        decisions.append(
            Decision(
                id=match.group("id"),
                title=match.group("title").strip(),
                priority=priority,
                status=status,
                line=start + 1,
                options=tuple(options),
                recommendation=recommendation,
                pending=tuple(pending),
                path=path,
            )
        )
    return decisions


def parse_design_sections(lines: list[str]) -> dict[str, DesignSection]:
    sections: dict[str, DesignSection] = {}
    marks: list[tuple[int, re.Match[str], str]] = []
    for index, line in enumerate(lines):
        h2 = DESIGN_H2.match(line.strip())
        if h2:
            marks.append((index, h2, "h2"))
            continue
        h3 = DESIGN_H3.match(line.strip())
        if h3:
            marks.append((index, h3, "h3"))
    for position, (start, match, _level) in enumerate(marks):
        end = marks[position + 1][0] if position + 1 < len(marks) else len(lines)
        number = match.group("number")
        sections[number] = DesignSection(
            number=number,
            title=match.group("title").strip(),
            line=start + 1,
            body=tuple(lines[start + 1 : end]),
        )
    return sections


def parse_open_questions(lines: list[str], section_number: str = "13") -> list[OpenQuestion]:
    sections = parse_design_sections(lines)
    section = sections.get(section_number)
    if section is None:
        return []
    return [
        OpenQuestion(text=line.strip().lstrip("- ").strip(), line=section.line + index)
        for index, line in enumerate(section.body, start=1)
        if line.strip().startswith("- ")
    ]
