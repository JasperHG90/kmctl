"""Create one OKF concept with its front matter, heading skeleton, index entry and log line.

The agent writes the prose; this writes the structure, following the index
format in ``kmctl.checks`` and only the fields the OKF spec defines (I4).
"""

import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from importlib.metadata import version
from pathlib import Path
from typing import Literal

Kind = Literal["decision", "practice", "proposal", "prototype", "handoff"]

SECTIONS: dict[str, str] = {
    "decision": "decisions",
    "practice": "practices",
    "proposal": "proposals",
    "prototype": "prototypes",
    "handoff": "handoffs",
}

SKELETONS: dict[str, list[str]] = {
    "decision": ["Context", "Decision", "Consequences"],
    "practice": ["What happened", "The lesson", "Evidence"],
    "proposal": ["Problem", "Proposal", "Open questions"],
    "prototype": ["Question", "Method", "Results", "Conclusion"],
    "handoff": ["Summary", "Where it stands", "Next steps", "Key references"],
}

#: How long a new handoff stays live before kmctl review due lists it as expired.
HANDOFF_DAYS = 14


class ConceptError(Exception):
    """A concept kmctl refused to write; the message names the fix."""


@dataclass(frozen=True)
class NewConcept:
    """What ``new_concept`` wrote."""

    id: str
    path: str
    created_section: bool


def slug(title: str) -> str:
    """``title`` in kebab-case, as a file name."""
    ascii_title = (
        unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    )
    words = re.sub(r"[^a-z0-9]+", "-", ascii_title.lower()).strip("-")
    if not words:
        raise ConceptError(
            f"title {title!r} has no letters or digits to name a file with"
        )
    return words


def _link_text(title: str) -> str:
    """``title`` with square brackets turned into parentheses, so the entry parses as a link."""
    return title.replace("[", "(").replace("]", ")")


def _next_number(section: Path) -> int:
    numbers = [
        int(m.group(1))
        for p in section.glob("*.md")
        if (m := re.match(r"(\d{4})-", p.name))
    ]
    return max(numbers, default=0) + 1


def _front_matter(kind: str, title: str, description: str, now: datetime) -> str:
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "---",
        f"type: {kind}",
        f"title: {json.dumps(title)}",
        f"description: {json.dumps(description)}",
        f"tags: [{kind}]",
        "generated:",
        f"  by: process:kmctl/{version('kmctl')}",
        f"  at: {stamp}",
    ]
    if kind == "decision":
        lines.append("status: stable")
    if kind == "handoff":
        lines.append(
            f"stale_after: {(now + timedelta(days=HANDOFF_DAYS)).strftime('%Y-%m-%dT%H:%M:%SZ')}"
        )
    return "\n".join([*lines, "---", ""])


def _append_log(log: Path, line: str, now: datetime) -> None:
    text = log.read_text(encoding="utf-8") if log.exists() else "# Log\n"
    heading = f"## {now.date().isoformat()}"
    headings = [h for h in text.splitlines() if h.startswith("## ")]
    if not headings or headings[-1] != heading:
        text = text.rstrip("\n") + f"\n\n{heading}\n\n"
    else:
        text = text.rstrip("\n") + "\n"
    log.write_text(text + line + "\n", encoding="utf-8")


def _append_entry(index: Path, entry: str) -> None:
    text = index.read_text(encoding="utf-8")
    index.write_text(text.rstrip("\n") + "\n" + entry + "\n", encoding="utf-8")


def new_concept(
    root: Path, kind: Kind, title: str, description: str, now: datetime | None = None
) -> NewConcept:
    """Write a new concept of ``kind`` under ``root``'s .okf/ and index and log it.

    Parameters
    ----------
    root : Path
        The repository root, holding .okf/ set up by ``kmctl init``.
    kind : Kind
        Which section the concept goes in.
    title : str
        The concept's title; its kebab-case form names the file.
    description : str
        One sentence for the front matter and the index entry.
    now : datetime | None
        The time written into the concept; the current UTC time when omitted.

    Returns
    -------
    NewConcept
        The concept's id, its path from the repository root, and whether its
        section was created.

    Raises
    ------
    ConceptError
        When .okf/index.md is missing, the title names no file, or the file
        already exists. Nothing is written.
    """
    now = now or datetime.now(UTC)
    okf = root / ".okf"
    if not (okf / "index.md").is_file():
        raise ConceptError(f"{okf / 'index.md'} does not exist; run kmctl init first")
    description = " ".join(
        description.split()
    )  # one line, so the index entry stays one line
    if not description:
        raise ConceptError(
            "--description is empty; give one sentence about the concept"
        )
    name = SECTIONS[kind]
    section = okf / name
    base = slug(title)
    if kind == "decision":
        number = f"{_next_number(section):04d}" if section.is_dir() else "0001"
        rel = f"{number}-{base}.md"
        title = f"ADR {number}: {title}"
    elif kind == "prototype":
        rel = f"{base}/README.md"
    else:
        rel = f"{base}.md"
    path = section / rel
    if path.exists():
        raise ConceptError(
            f"{path.relative_to(root)} already exists; pick another title"
        )

    created_section = not (section / "index.md").is_file()
    if created_section:
        section.mkdir(exist_ok=True)
        (section / "index.md").write_text(f"# {name.capitalize()}\n", encoding="utf-8")
    if f"({name}/index.md)" not in (okf / "index.md").read_text(encoding="utf-8"):
        _append_entry(
            okf / "index.md", f"- [{name.capitalize()}]({name}/index.md): the {name}."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n\n".join(f"## {h}" for h in SKELETONS[kind])
    path.write_text(
        _front_matter(kind, title, description, now) + f"\n# {title}\n\n{body}\n",
        encoding="utf-8",
    )
    _append_entry(
        section / "index.md", f"- [{_link_text(title)}]({rel}): {description}"
    )
    cid = path.relative_to(okf).with_suffix("").as_posix()
    if kind == "prototype":
        cid = path.parent.relative_to(okf).as_posix()
    _append_log(okf / "log.md", f"- Added `{cid}` with `kmctl new {kind}`.", now)
    return NewConcept(
        id=cid, path=path.relative_to(root).as_posix(), created_section=created_section
    )
