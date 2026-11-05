from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterator
from pathlib import Path

CODE_SPAN = re.compile(r"`(?P<code>[^`]+)`")
LINK = re.compile(r"\[[^\]]*\]\((?P<target>[^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE = "```"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def read_lines(path: Path) -> list[str]:
    return read_text(path).splitlines()


def code_spans(line: str) -> list[str]:
    return [match.group("code").strip() for match in CODE_SPAN.finditer(line)]


def strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def iter_links(lines: list[str]) -> Iterator[tuple[int, str]]:
    """Itera enlaces markdown fuera de bloques de código."""
    in_fence = False
    for number, line in enumerate(lines, start=1):
        if line.lstrip().startswith(FENCE):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for match in LINK.finditer(line):
            yield number, match.group("target")
