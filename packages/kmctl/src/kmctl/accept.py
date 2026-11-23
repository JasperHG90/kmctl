"""Accept a draft decision record: its status becomes stable and the log names who accepted it.

Only a person accepts (ADR 0050). An agent runs this only when the person it
names has said yes to the record; CI never does. Only the ``status`` line of
the front matter changes; the body and every other key stay as they were.
"""

import re
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from kmctl.concepts import ConceptError, append_log
from kmctl.kinds import DRAFT, STABLE
from kmctl.okf import BadFrontMatter, field, front_matter
from kmctl.supersede import _number, _record
from kmctl.verify import _PERSON


@dataclass(frozen=True)
class Accepted:
    """What ``accept`` wrote: the record's id and path, and who accepted it."""

    id: str
    path: str
    by: str


def git_person(root: Path) -> str | None:
    """``human:`` and the repository's git ``user.email``, or None when git has none."""
    done = subprocess.run(
        ["git", "-C", str(root), "config", "user.email"],
        capture_output=True,
        text=True,
        check=False,
    )
    email = done.stdout.strip()
    return f"human:{email}" if done.returncode == 0 and email else None


def accept(
    root: Path, number: str, by: str | None = None, now: datetime | None = None
) -> Accepted:
    """Set decision ``number``'s status from draft to stable and log who accepted it.

    Parameters
    ----------
    root : Path
        The repository root, holding .okf/decisions/.
    number : str
        The record's number, such as ``3`` or ``0003``.
    by : str | None
        The person who accepted it, as ``human:<id>``; the repository's git
        ``user.email`` when omitted.
    now : datetime | None
        The date of the log line; now when omitted.

    Returns
    -------
    Accepted
        The record's id, its repository-relative path and the person.

    Raises
    ------
    ConceptError
        When ``by`` is not a person and git names none, the record is missing,
        its front matter is unreadable, or its status is not draft. Nothing is
        written.
    """
    now = now or datetime.now(UTC)
    if by is None:
        by = git_person(root)
        if by is None:
            raise ConceptError(
                "git has no user.email here to name who accepted it; "
                "give --by human:<id>, such as --by human:jasper"
            )
    if not _PERSON.fullmatch(by):
        raise ConceptError(
            f"--by {by!r} is not a person; only a person accepts a decision, so give "
            "it as human:<id>, such as human:jasper"
        )
    okf = root / ".okf"
    path = _record(okf / "decisions", _number(number))
    cid = f"decisions/{path.stem}"
    try:
        status = field(front_matter(path), "status")
    except BadFrontMatter as error:
        raise ConceptError(f"{error}; fix its front matter first") from error
    if status != DRAFT:
        raise ConceptError(
            f"{cid} has status {status or 'none'}, not {DRAFT}; only a draft is accepted"
        )
    raw = path.read_bytes().decode("utf-8")
    newline = "\r\n" if "\r\n" in raw else "\n"
    text = raw.replace("\r\n", "\n")
    end = text.index("\n---", 4)
    head = re.sub(
        r"^status:.*$", f"status: {STABLE}", text[:end], count=1, flags=re.MULTILINE
    )
    path.write_bytes((head + text[end:]).replace("\n", newline).encode("utf-8"))
    append_log(okf / "log.md", f"- Accepted `{cid}` ({by}).", now)
    return Accepted(id=cid, path=f".okf/{cid}.md", by=by)
