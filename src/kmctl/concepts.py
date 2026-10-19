"""Create one OKF concept with its front matter, heading skeleton, index entry and log line.

The agent writes the prose; this writes the structure, following the index
format in ``kmctl.checks`` and only allowed OKF fields plus `handoff_key` (I4, ADR 0009).
"""

import calendar
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from importlib.metadata import version
from pathlib import Path
from typing import Literal

from kmctl.kinds import DRAFT, KINDS, skeleton
from kmctl.okf import (
    BadFrontMatter,
    as_datetime,
    field,
    front_matter,
    source_candidates,
)

Kind = Literal["decision", "practice", "proposal", "prototype", "handoff"]

SECTIONS: dict[str, str] = {
    "decision": "decisions",
    "practice": "practices",
    "proposal": "proposals",
    "prototype": "prototypes",
    "handoff": "handoffs",
}

#: How long a new handoff stays live before kmctl review due lists it as expired.
HANDOFF_DAYS = 14

#: The kinds that take ``--source``; kmctl review due never reads a handoff's sources.
SOURCE_KINDS = ("decision", "practice", "proposal", "prototype")

_STAMP = "%Y-%m-%dT%H:%M:%SZ"
#: ASCII digits only, and at most six, so a huge count is refused rather than crashing int().
_DURATION = re.compile(r"([0-9]{1,6})([dwmy])")


class ConceptError(Exception):
    """A concept kmctl refused to write; the message names the fix."""


@dataclass(frozen=True)
class NewConcept:
    """What ``new_concept`` wrote."""

    id: str
    path: str
    created_section: bool
    updated: bool = False


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


def one_line(text: str) -> str:
    """``text`` with every run of whitespace, line breaks included, as one space."""
    return " ".join(text.split())


def link_text(title: str) -> str:
    """``title`` on one line, with square brackets turned into parentheses, so an index entry parses."""
    return one_line(title).replace("[", "(").replace("]", ")")


def _add_months(when: datetime, months: int) -> datetime:
    """``when`` moved ``months`` calendar months on, its day clamped to the new month's last day."""
    year, month = divmod(when.month - 1 + months, 12)
    year += when.year
    day = min(when.day, calendar.monthrange(year, month + 1)[1])
    return when.replace(year=year, month=month + 1, day=day)


def stale_after_time(value: str, now: datetime) -> datetime:
    """The UTC time ``--stale-after`` names, which must be after ``now``.

    Parameters
    ----------
    value : str
        A duration from ``now`` (``30d`` days, ``12w`` weeks, ``6m`` calendar
        months, ``1y`` calendar years), a date (``2027-01-15``, read as its
        midnight UTC) or a timestamp (``2027-01-15T08:00:00Z``; one without an
        offset is UTC).
    now : datetime
        The time the concept is written.

    Returns
    -------
    datetime
        The time, in UTC.

    Raises
    ------
    ConceptError
        When ``value`` is none of those forms, or is not after ``now``. A zero
        duration and today's date are both refused.
    """
    if match := _DURATION.fullmatch(value):
        count, unit = int(match.group(1)), match.group(2)
        try:
            if unit == "d":
                when = now + timedelta(days=count)
            elif unit == "w":
                when = now + timedelta(weeks=count)
            else:
                when = _add_months(now, count * (12 if unit == "y" else 1))
        except (OverflowError, ValueError) as error:
            raise ConceptError(
                f"--stale-after {value!r} is too far in the future"
            ) from error
    else:
        parsed = as_datetime(value) if re.match(r"\d{4}-\d{2}-\d{2}", value) else None
        if parsed is None:
            raise ConceptError(
                f"--stale-after {value!r} is not a duration (30d, 12w, 6m, 1y) "
                "or a date (2027-01-15, or 2027-01-15T08:00:00Z)"
            )
        when = parsed
    if when <= now:
        raise ConceptError(
            f"--stale-after {value!r} is not in the future; give a later date or a duration"
        )
    return when.astimezone(UTC)


def _check_sources(
    root: Path, okf: Path, concept: Path, sources: list[str]
) -> list[str]:
    """``sources`` stripped, each one checked to exist on disk inside ``root``.

    The lookup is the one kmctl review due uses, so the two never disagree;
    git is not needed, so a file not yet added is accepted.

    Raises
    ------
    ConceptError
        When a source is blank, or names no file or folder in the repository.
    """
    checked = []
    for resource in sources:
        clean = resource.strip()
        if not clean or not any(
            (root / rel).exists()
            for rel in source_candidates(root, okf, concept, clean)
        ):
            raise ConceptError(
                f"--source {resource!r} names no file or folder in the repository; "
                "give a path from the repository root, or one starting with / from .okf/"
            )
        checked.append(clean)
    return checked


def _next_number(section: Path) -> int:
    numbers = [
        int(m.group(1))
        for p in section.glob("*.md")
        if (m := re.match(r"(\d{4,})-", p.name))
    ]
    return max(numbers, default=0) + 1


def _front_matter(
    kind: str,
    title: str,
    description: str,
    now: datetime,
    key: str | None = None,
    stale_after: datetime | None = None,
    sources: list[str] | None = None,
    draft: bool = False,
) -> str:
    """The front matter block for a new or updated concept.

    A handoff without ``stale_after`` gets one ``HANDOFF_DAYS`` from ``now``;
    ``sources`` are written as ``resource`` mappings, in order. ``draft``
    writes ``status: draft`` in place of the kind's own status.
    """
    stamp = now.strftime(_STAMP)
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
    if (status := DRAFT if draft else KINDS[kind].status) is not None:
        lines.append(f"status: {status}")
    if stale_after is None and kind == "handoff":
        stale_after = now + timedelta(days=HANDOFF_DAYS)
    if stale_after is not None:
        lines.append(f"stale_after: {stale_after.strftime(_STAMP)}")
    if sources:
        lines.append("sources:")
        lines += [f"  - resource: {json.dumps(s)}" for s in sources]
    if key is not None:
        lines.append(
            f"handoff_key: {json.dumps(key)}"
        )  # the one extension field (ADR 0009)
    return "\n".join([*lines, "---", ""])


def append_log(log: Path, line: str, now: datetime) -> None:
    text = log.read_text(encoding="utf-8") if log.exists() else "# Log\n"
    heading = f"## {now.date().isoformat()}"
    headings = [h for h in text.splitlines() if h.startswith("## ")]
    if not headings or headings[-1] != heading:
        text = text.rstrip("\n") + f"\n\n{heading}\n\n"
    else:
        text = text.rstrip("\n") + "\n"
    log.write_text(text + line + "\n", encoding="utf-8")


def _by_key(section: Path, key: str) -> Path | None:
    """The handoff in ``section`` whose ``handoff_key`` is ``key``, if one exists."""
    for path in sorted(section.glob("*.md")):
        if path.name == "index.md":
            continue
        try:
            if field(front_matter(path), "handoff_key") == key:
                return path
        except BadFrontMatter:
            continue
    return None


def _replace_entry(index: Path, rel: str, entry: str) -> None:
    """Replace the index line that links ``rel`` with ``entry``, or append it."""
    lines = index.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if f"]({rel})" in line:
            lines[i] = entry
            index.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return
    _append_entry(index, entry)


def _append_entry(index: Path, entry: str) -> None:
    text = index.read_text(encoding="utf-8")
    index.write_text(text.rstrip("\n") + "\n" + entry + "\n", encoding="utf-8")


def new_concept(
    root: Path,
    kind: Kind,
    title: str,
    description: str,
    now: datetime | None = None,
    key: str | None = None,
    stale_after: str | None = None,
    sources: list[str] | None = None,
    draft: bool = False,
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
    key : str | None
        Handoffs only: the session key (``handoff_key``, ADR 0009). When a
        handoff with this key exists, it is updated in place: same file and
        index entry, new title, description, body skeleton and dates.
    stale_after : str | None
        When kmctl review due lists the concept as due (expired, for a
        handoff): a duration or a date, read by ``stale_after_time``. A
        handoff gets ``HANDOFF_DAYS`` when omitted; other kinds get none.
    sources : list[str] | None
        Not for handoffs: the files or folders the concept describes, written
        in order as its ``sources``. Each must exist, found the way kmctl
        review due finds sources, so a change to one makes the concept due.
    draft : bool
        Decisions only: write ``status: draft`` instead of ``stable``, for a
        choice written down but not yet accepted (ADR 0031).

    Returns
    -------
    NewConcept
        The concept's id, its path from the repository root, and whether its
        section was created.

    Raises
    ------
    ConceptError
        When .okf/index.md is missing, the description is empty, the title
        names no file, the file already exists, ``key`` is given for a kind
        other than handoff, ``draft`` is set for a kind other than decision,
        ``key`` is empty or blank, ``stale_after`` is
        unreadable or not in the future, ``sources`` is given for a handoff,
        or a source names nothing. Nothing is written.
    """
    now = now or datetime.now(UTC)
    title = one_line(title)
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
    if key is not None and kind != "handoff":
        raise ConceptError("--key is for handoffs only; leave it out")
    if draft and kind != "decision":
        raise ConceptError("--draft is for decisions only; leave it out")
    if key is not None and not key.strip():
        raise ConceptError(
            "--key is empty; pass a session id, or leave --key out when there is none"
        )
    if sources and kind not in SOURCE_KINDS:
        raise ConceptError(
            "--source is not for handoffs: kmctl review due never reads a handoff's "
            "sources; leave it out"
        )
    when = stale_after_time(stale_after, now) if stale_after is not None else None
    name = SECTIONS[kind]
    section = okf / name
    existing = _by_key(section, key) if key is not None and section.is_dir() else None
    if existing is not None:
        slug(title)  # the same title check a new handoff gets
        rel = existing.relative_to(section).as_posix()
        body = "\n\n".join(f"## {h}" for h in skeleton(kind))
        existing.write_text(
            _front_matter(kind, title, description, now, key, when)
            + f"\n# {title}\n\n{body}\n",
            encoding="utf-8",
        )
        _replace_entry(
            section / "index.md", rel, f"- [{link_text(title)}]({rel}): {description}"
        )
        cid = existing.relative_to(okf).with_suffix("").as_posix()
        line = f"- Updated `{cid}` with `kmctl new handoff --key`."
        log = okf / "log.md"
        lines = log.read_text(encoding="utf-8").rstrip("\n").splitlines()
        headings = [h for h in lines if h.startswith("## ")]
        today = f"## {now.date().isoformat()}"
        # A repeat update on the same day adds no second identical line; a later day logs again.
        if not (lines and lines[-1] == line and headings and headings[-1] == today):
            append_log(log, line, now)
        return NewConcept(
            id=cid,
            path=existing.relative_to(root).as_posix(),
            created_section=False,
            updated=True,
        )
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
    written_sources = _check_sources(root, okf, path, sources or [])

    created_section = not (section / "index.md").is_file()
    if created_section:
        section.mkdir(exist_ok=True)
        (section / "index.md").write_text(f"# {name.capitalize()}\n", encoding="utf-8")
    if f"({name}/index.md)" not in (okf / "index.md").read_text(encoding="utf-8"):
        _append_entry(
            okf / "index.md", f"- [{name.capitalize()}]({name}/index.md): the {name}."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n\n".join(f"## {h}" for h in skeleton(kind))
    path.write_text(
        _front_matter(kind, title, description, now, key, when, written_sources, draft)
        + f"\n# {title}\n\n{body}\n",
        encoding="utf-8",
    )
    _append_entry(section / "index.md", f"- [{link_text(title)}]({rel}): {description}")
    cid = path.relative_to(okf).with_suffix("").as_posix()
    if kind == "prototype":
        cid = path.parent.relative_to(okf).as_posix()
    append_log(okf / "log.md", f"- Added `{cid}` with `kmctl new {kind}`.", now)
    return NewConcept(
        id=cid, path=path.relative_to(root).as_posix(), created_section=created_section
    )
