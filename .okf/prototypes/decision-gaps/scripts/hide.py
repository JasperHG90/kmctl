"""Hide a unit's decision: drop decision files from its changes and decision sentences from its text.

``strip`` removes every sentence that names an ADR, a decision record or a
recorded choice; ``leaks`` says whether text still names one after that.
"""

from __future__ import annotations

import re
from pathlib import Path

LEAK = re.compile(
    r"\b(ADRs?|decisions?|decided|recorded|records? (that|why|the))\b"
    r"|\.okf/|summary\.md|log\.md|\bnext free\b|\bthe number\b",
    re.I,
)
_SENTENCE = re.compile(r"(?<=[.!?;])\s+|\n\s*[-*]\s+")
HIDDEN_PATHS = re.compile(r"^\.(okf|loop)/")


def strip(text: str) -> str:
    """``text`` without the sentences or bullets that name an ADR or a decision."""
    parts = _SENTENCE.split(text)
    return " ".join(" ".join(p.split()) for p in parts if p.strip() and not LEAK.search(p))


def leaks(text: str) -> bool:
    """Whether ``text`` still names an ADR or a decision."""
    return bool(LEAK.search(text))


def visible_files(files: list[list[str]]) -> list[list[str]]:
    """The unit's (status, path) changes outside the bookkeeping folders .okf/ and .loop/, for every unit alike."""
    return [f for f in files if not HIDDEN_PATHS.match(f[1])]


def intent(repo: Path, slug: str | None) -> str:
    """The Intent section of the ticket's plan, or '' when the unit has no plan."""
    if not slug:
        return ""
    for plan in (repo / ".loop" / "plans" / slug / "README.md", repo / ".loop" / "archive" / slug / "plans" / "README.md"):
        if plan.exists():
            body = plan.read_text()
            if "## Intent" in body:
                return body.split("## Intent", 1)[1].split("\n## ", 1)[0].strip()
    return ""
