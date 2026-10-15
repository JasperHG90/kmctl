"""Supersede one decision record with another, writing both sides of the link.

A record is never rewritten: the old one gets ``status: deprecated`` and an
appended dated Correction section, and its body above that stays as it was
(``.claude/rules/okf-bundle.md``). Only spec fields are written (I4), so a
hand-added ``decision_status`` is left alone.
"""

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from kmctl.concepts import ConceptError, append_log
from kmctl.okf import BadFrontMatter, front_matter


@dataclass(frozen=True)
class Superseded:
    """The two records ``supersede`` linked, as concept ids."""

    old: str
    new: str


def _number(value: str) -> str:
    if not re.fullmatch(r"[0-9]+", value):
        raise ConceptError(f"{value!r} is not a decision number; give it as 3 or 0003")
    return f"{int(value):04d}"


def _record(decisions: Path, number: str) -> Path:
    found = sorted(decisions.glob(f"{number}-*.md"))
    if not found:
        raise ConceptError(
            f"no decision {number} in {decisions}; kmctl new decision creates one"
        )
    return found[0]


def _entry_end(lines: list[str], start: int) -> int:
    """The last line of the entry starting at ``start``: it runs to a blank line or the next item."""
    end = start
    for i in range(start + 1, len(lines)):
        if not lines[i].strip() or re.match(r"^\s*[-*+]\s", lines[i]):
            break
        end = i
    return end


def _deprecate(text: str) -> str:
    """``text`` with its front matter ``status`` set to deprecated, body untouched."""
    end = text.index("\n---", 4)
    head, body = text[:end], text[end:]
    if re.search(r"^status:.*$", head, re.MULTILINE):
        head = re.sub(
            r"^status:.*$", "status: deprecated", head, count=1, flags=re.MULTILINE
        )
    else:
        head += "\nstatus: deprecated"
    return head + body


def supersede(
    root: Path, old: str, new: str, now: datetime | None = None
) -> Superseded:
    """Mark decision ``old`` superseded by decision ``new`` and link them both ways.

    Parameters
    ----------
    root : Path
        The repository root, holding .okf/decisions/.
    old : str
        The number of the decision being replaced, such as ``3`` or ``0003``.
    new : str
        The number of the decision that replaces it.
    now : datetime | None
        The date written into the correction and the log; now when omitted.

    Returns
    -------
    Superseded
        The ids of both records.

    Raises
    ------
    ConceptError
        When either record is missing, they are the same, or ``old`` is
        already deprecated. Nothing is written.
    """
    now = now or datetime.now(UTC)
    okf = root / ".okf"
    decisions = okf / "decisions"
    old_n, new_n = _number(old), _number(new)
    if old_n == new_n:
        raise ConceptError(
            f"a decision cannot supersede itself ({old_n}); give the new record's number to --by"
        )
    old_path, new_path = _record(decisions, old_n), _record(decisions, new_n)
    try:
        if front_matter(old_path).get("status") == "deprecated":
            raise ConceptError(
                f"decision {old_n} is already deprecated; supersede the record that replaced it"
            )
    except BadFrontMatter as error:
        raise ConceptError(f"{error}; fix its front matter first") from error
    index = decisions / "index.md"
    lines = index.read_text(encoding="utf-8").splitlines() if index.is_file() else []
    hits = [i for i, line in enumerate(lines) if f"]({old_path.name})" in line]
    if not hits:
        raise ConceptError(
            f"{index} has no entry for {old_path.name}; add a line "
            f"'- [title]({old_path.name}): description' to it, then run this again"
        )

    date = now.date().isoformat()
    old_text = _deprecate(old_path.read_text(encoding="utf-8")).rstrip("\n")
    old_path.write_text(
        old_text
        + f"\n\n## Correction, {date}\n\nSuperseded by [ADR {new_n}]({new_path.name}).\n",
        encoding="utf-8",
    )
    new_text = new_path.read_text(encoding="utf-8").rstrip("\n")
    new_path.write_text(
        new_text + f"\n\nSupersedes [ADR {old_n}]({old_path.name}).\n", encoding="utf-8"
    )
    lines[_entry_end(lines, hits[0])] += f" (superseded by ADR {new_n})"
    index.write_text("\n".join(lines) + "\n", encoding="utf-8")
    old_id = f"decisions/{old_path.stem}"
    new_id = f"decisions/{new_path.stem}"
    append_log(okf / "log.md", f"- Superseded `{old_id}` with `{new_id}`.", now)
    return Superseded(old=old_id, new=new_id)
