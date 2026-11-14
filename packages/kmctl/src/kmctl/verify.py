"""Record that a person checked a concept or docs page, so it leaves kmctl review due.

Only the ``verified`` list (and ``stale_after``, when asked) changes; every
other line of the file stays as it was. Only a person verifies: an audit
never writes the entry (ADR 0005, I2), and an agent runs this only when the
person it names has confirmed the content (ADR 0023).
"""

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import yaml

from kmctl.concepts import _STAMP, ConceptError, append_log, stale_after_time
from kmctl.okf import BadFrontMatter, field, front_matter, has_passed

#: A person's id as ``verified[].by`` holds it: ``human:`` and a name or address.
_PERSON = re.compile(r"human:[A-Za-z0-9._@+-]+")
#: A front matter line that starts a top-level key.
_KEY = re.compile(r"[^\s#-][^:]*:")
#: A trailing YAML comment and the space before it.
_COMMENT = re.compile(r"(?:^|\s+)#.*$")


@dataclass(frozen=True)
class Verified:
    """What ``verify`` wrote: the id, the file, the entry and any new ``stale_after``."""

    id: str
    path: str
    by: str
    at: str
    stale_after: str | None


def _target(root: Path, cid: str) -> tuple[Path, str]:
    """The file an id from kmctl review due names, and that id in its one spelling.

    ``docs/...`` is under docs/, anything else under .okf/. The id must be
    spelled as kmctl review due prints it, so ``./``, ``//``, ``..``, an
    absolute path or a symlink out of the folder is refused rather than
    resolved to some other file.
    """
    cid = cid.removesuffix(".md")
    docs = cid.startswith("docs/")
    base = (root / "docs" if docs else root / ".okf").resolve()
    name = cid.removeprefix("docs/") if docs else cid
    path = (base / f"{name}.md").resolve()
    shown = f"{'docs' if docs else '.okf'}/{name}.md"
    if not path.is_relative_to(base) or not path.is_file():
        raise ConceptError(
            f"no concept or docs page {cid!r} at {shown}; give an id as kmctl review due prints it"
        )
    canonical = ("docs/" if docs else "") + path.relative_to(base).with_suffix(
        ""
    ).as_posix()
    if canonical != cid:
        raise ConceptError(
            f"{cid!r} is not spelled as kmctl review due prints it; give {canonical!r}"
        )
    return path, canonical


def _block(lines: list[str], start: int) -> int:
    """The index after the last line of the top-level value that starts at ``lines[start]``."""
    end = start + 1
    while end < len(lines) and not _KEY.match(lines[end]) and lines[end].strip():
        end += 1
    return end


def _with_entry(head: list[str], by: str, at: str) -> list[str]:
    """``head`` (the front matter lines) with ``{by, at}`` appended to its ``verified`` list.

    A trailing comment on the ``verified:`` line stays on that line.
    """
    item = [f"  - by: {by}", f"    at: {at}"]
    starts = [i for i, line in enumerate(head) if line.startswith("verified:")]
    if not starts:
        return [*head, "verified:", *item]
    k = starts[0]
    end = _block(head, k)
    value = head[k].split(":", 1)[1]
    found = _COMMENT.search(value)
    comment = found.group(0) if found else ""
    rest = value[: found.start()].strip() if found else value.strip()
    body = head[k + 1 : end]
    if rest in ("", "~", "null", "[]"):
        if not body:
            return [*head[:k], f"verified:{comment}", *item, *head[end:]]
        indent = len(body[0]) - len(body[0].lstrip())
        pad = " " * indent
        if body[0].lstrip().startswith("- "):
            item = [f"{pad}- by: {by}", f"{pad}  at: {at}"]
            return [*head[:end], *item, *head[end:]]
        # one mapping: make it the list's first item, then add ours
        mapped = [pad + "- " + body[0][indent:]] + [
            pad + "  " + line[indent:] for line in body[1:]
        ]
        item = [f"{pad}- by: {by}", f"{pad}  at: {at}"]
        return [*head[:k], f"verified:{comment}", *mapped, *item, *head[end:]]
    flow = f"{{by: {json.dumps(by)}, at: {json.dumps(at)}}}"
    if not body and rest.startswith("[") and rest.endswith("]"):
        line = f"verified: {rest[:-1].rstrip()}, {flow}]{comment}"
        return [*head[:k], line, *head[end:]]
    if not body and rest.startswith("{") and rest.endswith("}"):
        return [*head[:k], f"verified: [{rest}, {flow}]{comment}", *head[end:]]
    raise ConceptError(
        "its verified field is in a form kmctl cannot extend; rewrite it as a "
        "block list (verified:, then '  - by: human:<id>' and '    at: <time>')"
    )


def _with_stale_after(head: list[str], when: str) -> list[str]:
    """``head`` with ``stale_after`` set to ``when``, replacing the old value or added at the end."""
    for i, line in enumerate(head):
        if line.startswith("stale_after:"):
            return [*head[:i], f"stale_after: {when}", *head[_block(head, i) :]]
    return [*head, f"stale_after: {when}"]


def verify(
    root: Path,
    cid: str,
    by: str,
    stale_after: str | None = None,
    now: datetime | None = None,
) -> Verified:
    """Append a person's ``verified`` entry to the concept or docs page ``cid``.

    Parameters
    ----------
    root : Path
        The repository root.
    cid : str
        The id as kmctl review due prints it: a concept id under .okf/
        (``decisions/0001-x``, ``manifesto``) or a docs page id
        (``docs/how-to/run``).
    by : str
        The person who checked it, as ``human:<id>``.
    stale_after : str | None
        A new ``stale_after``, in the forms ``kmctl new --stale-after`` takes;
        required when the file's ``stale_after`` has passed.
    now : datetime | None
        The time written as ``at``; now when omitted.

    Returns
    -------
    Verified
        The id, the repository-relative path, the entry and any new
        ``stale_after``.

    Raises
    ------
    ConceptError
        When ``by`` is not a person, the id names no file, names a handoff,
        the front matter is unreadable or missing, or ``stale_after`` has
        passed and no new one is given. Nothing is written.
    """
    now = (now or datetime.now(UTC)).astimezone(UTC)
    if not _PERSON.fullmatch(by):
        raise ConceptError(
            f"--by {by!r} is not a person; only a person verifies, so give it as "
            "human:<id>, such as human:jasper"
        )
    path, cid = _target(root, cid)
    if cid.startswith("handoffs/"):
        raise ConceptError(
            f"{cid} is a handoff, and handoffs are never verified; "
            "kmctl review due lists one only once it expires"
        )
    # Name the file by its path in the repository, as kmctl review due does,
    # even when docs/ or .okf/ is a symlink to a folder outside it.
    rel = f"{cid}.md" if cid.startswith("docs/") else f".okf/{cid}.md"
    try:
        meta = front_matter(path)
    except BadFrontMatter as error:
        raise ConceptError(f"{error}; fix its front matter first") from error
    raw = path.read_bytes().decode("utf-8")
    newline = "\r\n" if "\r\n" in raw else "\n"
    text = raw.replace("\r\n", "\n")
    end = text.find("\n---", 4)
    if not text.startswith("---\n") or end == -1:
        raise ConceptError(
            f"{rel} has no front matter; add one (kmctl schema lists each kind's) first"
        )
    when = None
    if stale_after is not None:
        when = stale_after_time(stale_after, now).strftime(_STAMP)
    elif has_passed(field(meta, "stale_after"), now):
        raise ConceptError(
            f"{cid}'s stale_after has passed, and a verified entry does not clear "
            f"that; give a new one: kmctl verify {cid} --by {by} --stale-after 6m"
        )
    at = now.strftime(_STAMP)
    head = _with_entry(text[4:end].split("\n"), by, at)
    if when is not None:
        head = _with_stale_after(head, when)
    new = "---\n" + "\n".join(head) + text[end:]
    try:
        written = yaml.safe_load("\n".join(head))
    except yaml.YAMLError as error:
        raise ConceptError(
            f"{rel}'s front matter would not parse after adding the entry; "
            "rewrite its verified field as a block list"
        ) from error
    if not isinstance(written, dict) or len(field(written, "verified[].by")) != (
        len(field(meta, "verified[].by")) + 1
    ):
        raise ConceptError(
            f"{rel}'s verified field did not take the entry; "
            "rewrite it as a block list (verified:, then '  - by: human:<id>')"
        )
    path.write_bytes(new.replace("\n", newline).encode("utf-8"))
    if not cid.startswith("docs/"):
        append_log(root / ".okf" / "log.md", f"- Verified `{cid}` ({by}).", now)
    return Verified(id=cid, path=rel, by=by, at=at, stale_after=when)
