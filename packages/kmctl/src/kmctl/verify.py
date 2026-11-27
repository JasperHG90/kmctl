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
from kmctl.okf import (
    BadFrontMatter,
    field,
    front_matter,
    has_passed,
    split_front_matter,
    without,
)
from kmctl.pages import concept_files, docs_pages

#: The front matter fields ``kmctl verify`` writes. A change to these alone is
#: no edit for kmctl review due (ADR 0032) and no change for the summary (ADR 0054).
VERIFY_FIELDS = {"verified", "stale_after"}
#: A person's id as ``verified[].by`` holds it: ``human:`` and a name or address.
_PERSON = re.compile(r"human:[A-Za-z0-9._@+-]+")
#: A front matter line that starts a top-level key.
_KEY = re.compile(r"[^\s#-][^:]*:")
#: A trailing YAML comment and the space before it.
_COMMENT = re.compile(r"(?:^|\s+)#.*$")


def outside_verify(text: str | None) -> tuple[object, str] | None:
    """``text`` without the fields kmctl verify writes, to compare two versions of a file by.

    None for a missing file. A file whose front matter does not parse is
    compared whole.
    """
    if text is None:
        return None
    try:
        parsed = split_front_matter(text)
    except BadFrontMatter:
        return None, text
    return without(parsed[0], VERIFY_FIELDS), parsed[1]


@dataclass(frozen=True)
class Verified:
    """What ``verify`` wrote: the id, the file, the entry and any new ``stale_after``."""

    id: str
    path: str
    by: str
    at: str
    stale_after: str | None


def _pages(root: Path, docs: bool) -> dict[str, Path]:
    """Every page kmctl review due tracks under docs/ (``docs``) or .okf/, by id."""
    if docs:
        base = root / "docs"
        found = docs_pages(base) if base.is_dir() else []
        return {
            "docs/" + p.relative_to(base).with_suffix("").as_posix(): p for p in found
        }
    base = root / ".okf"
    found = concept_files(base) if base.is_dir() else []
    return {p.relative_to(base).with_suffix("").as_posix(): p for p in found}


def _folder_hint(base: Path, name: str, docs: bool, by: str) -> str:
    """The folder form of ``kmctl verify`` for the nearest folder above ``name``, or ''."""
    parent = Path(name).parent
    while parent != Path(".") and not (base / parent).is_dir():
        parent = parent.parent
    if parent == Path("."):
        return ""
    folder = ("docs/" if docs else "") + parent.as_posix()
    return f"; to verify every page in {folder}, give kmctl verify {folder} --by {by}"


def _targets(root: Path, given: str, by: str) -> list[tuple[Path, str]]:
    """The files an id or folder names, each with its id as kmctl review due prints it.

    An id names one page: ``decisions/0001-x``, ``docs/how-to/run``, or the
    same path from the repository root with ``.md`` (``.okf/decisions/0001-x.md``).
    A folder (``decisions``, ``docs/how-to``) names every page under it that
    kmctl review due tracks, without handoffs. Anything else spelled oddly
    (``./``, ``//``, ``..``, an absolute path, a symlink out of the folder) is
    refused rather than resolved to some other file, as is a file kmctl review
    due never lists, such as a section's ``index.md``.

    Raises
    ------
    ConceptError
        When ``given`` names no page or folder of pages, names one only by
        another spelling, or names a file kmctl review due never lists.
    """
    cid = given.rstrip("/").removesuffix(".md")
    in_okf = cid.startswith(".okf/")
    cid = cid.removeprefix(".okf/")
    docs = cid.startswith("docs/") and not in_okf
    base = (root / "docs" if docs else root / ".okf").resolve()
    name = cid.removeprefix("docs/") if docs else cid
    shown = f"{'docs' if docs else '.okf'}/{name}"
    hint = _folder_hint(base, name, docs, by) if name else ""
    file = (base / f"{name}.md").resolve()
    folder = (base / name).resolve()
    if name and file.is_relative_to(base) and file.is_file():
        found = file.relative_to(base).with_suffix("").as_posix()
        kind = "page"
    elif name and folder.is_relative_to(base) and folder != base and folder.is_dir():
        found = folder.relative_to(base).as_posix()
        kind = "folder"
    else:
        raise ConceptError(
            f"no concept, docs page or folder {given!r} at {shown}(.md); give an id "
            f"or folder as kmctl review due prints it{hint}"
        )
    canonical = ("docs/" if docs else "") + found
    if canonical != cid:
        raise ConceptError(
            f"{given!r} is not spelled as kmctl review due prints it; give {canonical!r}"
        )
    pages = _pages(root, docs)
    if kind == "page":
        if canonical not in pages:
            raise ConceptError(
                f"{shown}.md is not a page kmctl review due lists, so it is never "
                f"verified{hint}"
            )
        return [(file, canonical)]
    if found == "handoffs" or found.startswith("handoffs/"):
        raise ConceptError(
            f"{canonical} holds handoffs, and handoffs are never verified; "
            "kmctl review due lists one only once it expires"
        )
    inside = [
        (path, pid)
        for pid, path in pages.items()
        if pid.startswith(canonical + "/") and not pid.startswith("handoffs/")
    ]
    if not inside:
        raise ConceptError(
            f"the folder {shown} holds no page kmctl review due lists; give an id "
            "as kmctl review due prints it"
        )
    return inside


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


@dataclass(frozen=True)
class _Pending:
    """A verification checked and ready to write: the file, its new bytes, and what it records."""

    path: Path
    data: bytes
    result: Verified


def _prepare(
    path: Path, cid: str, by: str, stale_after: str | None, now: datetime
) -> _Pending:
    """The bytes ``verify_all`` writes to ``path``, the page ``cid``, checked by its rules; nothing is written."""
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
    return _Pending(
        path,
        new.replace("\n", newline).encode("utf-8"),
        Verified(id=cid, path=rel, by=by, at=at, stale_after=when),
    )


def verify_all(
    root: Path,
    cids: list[str],
    by: str,
    stale_after: str | None = None,
    now: datetime | None = None,
) -> list[Verified]:
    """Append a person's ``verified`` entry to each concept or docs page in ``cids`` (ADR 0055).

    Every id is checked before any file is written, so one refused id leaves
    every file as it was. A page named twice, by its id or a folder, is
    verified once.

    Parameters
    ----------
    root : Path
        The repository root.
    cids : list[str]
        The ids as kmctl review due prints them: a concept id under .okf/
        (``decisions/0001-x``, ``manifesto``) or a docs page id
        (``docs/how-to/run``); the same path from the repository root with
        ``.md`` (``.okf/decisions/0001-x.md``); or a folder (``decisions``,
        ``docs/how-to``) for every page under it that kmctl review due tracks.
    by : str
        The person who checked them, as ``human:<id>``.
    stale_after : str | None
        A new ``stale_after`` for each file, in the forms ``kmctl new
        --stale-after`` takes; required for a file whose ``stale_after`` has
        passed.
    now : datetime | None
        The time written as ``at``; now when omitted.

    Returns
    -------
    list[Verified]
        For each id, in the order given: the id, the repository-relative
        path, the entry and any new ``stale_after``.

    Raises
    ------
    ConceptError
        When ``by`` is not a person, an id names no page or folder of pages,
        names a file kmctl review due never lists, or names a handoff,
        a front matter is unreadable or missing, or a ``stale_after`` has
        passed and no new one is given. Nothing is written.
    """
    if not _PERSON.fullmatch(by):
        raise ConceptError(
            f"--by {by!r} is not a person; only a person verifies, so give it as "
            "human:<id>, such as human:jasper"
        )
    now = (now or datetime.now(UTC)).astimezone(UTC)
    targets: dict[str, Path] = {}
    for given in cids:
        for path, cid in _targets(root, given, by):
            targets.setdefault(cid, path)
    pending = [
        _prepare(path, cid, by, stale_after, now) for cid, path in targets.items()
    ]
    for p in pending:
        p.path.write_bytes(p.data)
        if not p.result.id.startswith("docs/"):
            append_log(
                root / ".okf" / "log.md", f"- Verified `{p.result.id}` ({by}).", now
            )
    return [p.result for p in pending]


def verify(
    root: Path,
    cid: str,
    by: str,
    stale_after: str | None = None,
    now: datetime | None = None,
) -> Verified:
    """Append a person's ``verified`` entry to the concept or docs page ``cid``; ``verify_all`` for one id."""
    return verify_all(root, [cid], by, stale_after, now)[0]
