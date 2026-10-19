"""Rename one concept in .okf/ and rewrite the links to it in .okf/ and docs/.

A rename stays in the concept's folder, so the concept's own relative links
still resolve. Links are found as ``kmctl check`` finds them (``kmctl.checks``):
outside code fences and code spans, inline or reference-style, with the
anchor kept. ``.okf/log.md`` is history and is never rewritten
(``.claude/rules/okf-bundle.md``). A decision keeps its number in its file
name, its ``title`` and its ``#`` heading, so a renumbering changes all three,
and the text ``ADR NNNN`` of each link to it.

Lines kmctl does not rewrite, such as a path in ``AGENTS.md``, a skill or a
script, are listed instead, for the person or agent to fix by hand.
"""

import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from kmctl.checks import _REF_DEF, _TARGET, _prose_lines, _target, _visible
from kmctl.concepts import ConceptError, append_log, slug
from kmctl.summary import SUMMARY, _git

#: A decision's file name: its four-digit number, a dash, then its name.
_NUMBERED = re.compile(r"([0-9]{4})-")
#: An inline link, with the text (group 2) and the target (group 4) apart.
_LINK = re.compile(r"(!?\[)([^\]]*)(\]\()" + _TARGET + r"\)")
#: A code span, kept whole so nothing inside it is rewritten.
_CODE_SPAN = re.compile(r"(`[^`]*`)")
_RESERVED = ("index", "log")
#: The most characters of a line a mention shows; a longer line is cut around the match.
EXCERPT = 160


@dataclass(frozen=True)
class Mention:
    """A line that still names the old concept after the move, which kmctl did not rewrite.

    Attributes
    ----------
    file : str
        The file, from the repository root.
    line : int
        The line number in ``file``, from 1.
    text : str
        The line, without its leading and trailing whitespace; a line longer
        than ``EXCERPT`` characters is cut to that many around the match,
        with ``...`` where it was cut.
    """

    file: str
    line: int
    text: str


@dataclass(frozen=True)
class Moved:
    """What ``mv`` did.

    Attributes
    ----------
    old : str
        The concept's id before the move.
    new : str
        Its id after it.
    path : str
        Its new file (a prototype's folder) from the repository root.
    updated : list[str]
        Each file whose links, title or ``checked.against`` it rewrote, from
        the repository root, sorted; ``.okf/log.md`` is left out.
    mentions : list[Mention]
        The lines, anywhere in the repository but ``.okf/log.md``, that
        still hold the old id or file name (a prototype's ``folder/``) or,
        for a renumbered decision, its old ``ADR NNNN``.
    """

    old: str
    new: str
    path: str
    updated: list[str]
    mentions: list[Mention]


def _clean(cid: str) -> str:
    """``cid`` without a trailing ``.md``."""
    return cid.removesuffix(".md")


def _locate(okf: Path, cid: str) -> Path:
    """The file or prototype folder concept ``cid`` names in ``okf``.

    Raises
    ------
    ConceptError
        When ``cid`` is at the bundle root, names a reserved file, holds an
        empty, ``.`` or ``..`` part, or names no concept.
    """
    parts = cid.split("/")
    if len(parts) == 1:
        raise ConceptError(
            f"{cid!r} is not in a section; kmctl mv renames a concept in a "
            "section, such as decisions/0007-use-a-queue, and the summary and "
            "manifesto keep their names"
        )
    if parts[-1] in _RESERVED:
        raise ConceptError(
            f"{cid!r} is a reserved file, not a concept; give a concept's id"
        )
    path = okf / f"{cid}.md"
    if parts[0] == "prototypes" and len(parts) == 2:
        path = okf / cid
    found = (path.is_dir() and (path / "README.md").is_file()) or path.is_file()
    if any(p in ("", ".", "..") or p.startswith(".") for p in parts) or not found:
        raise ConceptError(
            f"no concept {cid!r} in .okf/; give an id as kmctl review due prints "
            "it, such as decisions/0007-use-a-queue"
        )
    return path


def _check_new(okf: Path, old_id: str, new_id: str, old: Path) -> Path:
    """The path concept ``old_id`` moves to as ``new_id``, checked to be free.

    Raises
    ------
    ConceptError
        When ``new_id`` is ``old_id``, leaves its folder, is not kebab-case,
        exists, or, in decisions/, has no number or one another record holds.
    """
    if new_id == old_id:
        raise ConceptError(f"{new_id!r} is the same id as {old_id!r}; give a new one")
    folder = PurePosixPath(old_id).parent.as_posix()
    if PurePosixPath(new_id).parent.as_posix() != folder:
        raise ConceptError(
            f"{new_id!r} is not in {folder}/: a concept must stay in its folder, "
            f"so give {folder}/NAME"
        )
    name = PurePosixPath(new_id).name
    try:
        fixed = slug(name)
    except ConceptError:
        fixed = None
    if fixed != name:
        raise ConceptError(
            f"{name!r} is not kebab-case (lowercase letters, digits and dashes)"
            + (f"; give {fixed!r}" if fixed else "")
        )
    new = old.with_name(name if old.is_dir() else f"{name}.md")
    if new.exists():
        raise ConceptError(
            f"{new.relative_to(okf.parent).as_posix()} already exists; pick another "
            "name, or move that concept first"
        )
    if folder == "decisions":
        number = _NUMBERED.match(name)
        if number is None:
            raise ConceptError(
                f"{name!r} does not start with a four-digit number; a decision's "
                "file name is NNNN-name, such as 0007-use-a-queue"
            )
        taken = [p for p in old.parent.glob(f"{number.group(1)}-*.md") if p != old]
        if taken:
            raise ConceptError(
                f"decision {number.group(1)} is taken by {taken[0].name}; renumber a "
                "run from the lowest free number upward, one kmctl mv at a time"
            )
    return new


def _new_target(
    raw: str, page: Path, base: Path, old: Path, new: Path
) -> tuple[str, bool] | None:
    """``raw``, a link target on ``page``, pointing at ``new``, or None when it does not point at ``old``.

    A ``/`` target resolves from ``base`` and stays a ``/`` target; any
    other resolves from the page's folder. The anchor or query stays, and so
    do angle brackets. The flag is True when the target is ``old`` itself
    rather than a file inside a moved folder.
    """
    target = _target(raw)
    if not target or "://" in target or target.startswith("mailto:"):
        return None
    if target.startswith("/"):
        resolved = (base / target.lstrip("/")).resolve()
    else:
        resolved = (page.parent / target).resolve()
    if resolved == old:
        moved, exact = new, True
    elif old.suffix != ".md" and resolved.is_relative_to(old):
        moved, exact = new / resolved.relative_to(old), False
    else:
        return None
    if target.startswith("/"):
        written = "/" + moved.relative_to(base.resolve()).as_posix()
    else:
        written = Path(os.path.relpath(moved, page.parent.resolve())).as_posix()
    wrapped = raw.startswith("<") and raw.endswith(">")
    inner = raw[1:-1] if wrapped else raw
    cut = min((i for i in (inner.find("#"), inner.find("?")) if i != -1), default=-1)
    written += inner[cut:] if cut != -1 else ""
    return (f"<{written}>" if wrapped else written), exact


def _rewrite(
    text: str,
    page: Path,
    base: Path,
    old: Path,
    new: Path,
    numbers: tuple[str, str] | None,
) -> str:
    """``text``, the page at ``page``, with each link to ``old`` pointing at ``new``.

    With ``numbers`` (old, new), a link to the record itself also has
    ``ADR OLD`` in its text changed to ``ADR NEW``.
    """
    prose = {number for number, _ in _prose_lines(text)}

    def link(match: re.Match[str]) -> str:
        found = _new_target(match.group(4), page, base, old, new)
        if found is None:
            return match.group(0)
        written, exact = found
        label = match.group(2)
        if numbers is not None and exact:
            label = re.sub(rf"\bADR {numbers[0]}\b", f"ADR {numbers[1]}", label)
        start = match.start()
        whole = match.group(0)
        return (
            match.group(1)
            + label
            + whole[match.end(2) - start : match.start(4) - start]
            + written
            + whole[match.end(4) - start :]
        )

    lines = text.splitlines(keepends=True)
    for number, line in enumerate(lines, start=1):
        if number not in prose:
            continue
        parts = _CODE_SPAN.split(line)
        parts[::2] = [_LINK.sub(link, part) for part in parts[::2]]
        if definition := _REF_DEF.match(parts[0]):
            found = _new_target(definition.group(1), page, base, old, new)
            if found is not None:
                start, end = definition.span(1)
                parts[0] = parts[0][:start] + found[0] + parts[0][end:]
        lines[number - 1] = "".join(parts)
    return "".join(lines)


def _renumber(text: str, old_n: str, new_n: str) -> str:
    """``text``, a decision record, with ``ADR OLD`` changed to ``ADR NEW`` in its title and ``#`` heading."""
    pattern = re.compile(rf"\bADR {old_n}\b")
    lines = text.splitlines(keepends=True)
    in_head = bool(lines) and lines[0].rstrip("\n") == "---"
    for i, line in enumerate(lines):
        if in_head and i > 0 and line.rstrip("\n") == "---":
            in_head = False
        elif in_head and line.startswith("title:"):
            lines[i] = pattern.sub(f"ADR {new_n}", line)
        elif not in_head and line.startswith("# "):
            lines[i] = pattern.sub(f"ADR {new_n}", line)
            break
    return "".join(lines)


def _checked(text: str, old_id: str, new_id: str) -> str:
    """``text``, the summary, with ``old_id`` in its front matter list items changed to ``new_id``."""
    end = text.find("\n---", 4)
    if not text.startswith("---\n") or end == -1:
        return text
    head = re.sub(
        rf"^([ \t]*-[ \t]*){re.escape(old_id)}([ \t]*)$",
        rf"\g<1>{new_id}\g<2>",
        text[:end],
        flags=re.MULTILINE,
    )
    return head + text[end:]


def _pages(root: Path) -> list[Path]:
    """The pages whose links ``mv`` rewrites: every visible .md file in .okf/ and docs/ but .okf/log.md."""
    pages = []
    for folder in (root / ".okf", root / "docs"):
        if folder.is_dir():
            pages += sorted(
                p for p in folder.rglob("*.md") if p.is_file() and _visible(folder, p)
            )
    return [p for p in pages if p != root / ".okf" / "log.md"]


def _repository_files(root: Path) -> list[Path]:
    """Every file in the repository that git does not ignore, or every file outside .git/ without git."""
    listed = _git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    if listed is None:
        found = (p for p in root.rglob("*") if ".git" not in p.relative_to(root).parts)
    else:
        found = (root / p for p in listed.split("\0") if p)
    return sorted({p for p in found if p.is_file()})


def _mentions(root: Path, terms: tuple[str, ...], old_n: str | None) -> list[Mention]:
    """The lines in ``root``, but in .okf/log.md and .loop/, that hold one of ``terms`` or, with ``old_n``, ``ADR OLD_N``.

    Both are history, which a move never rewrites.
    """
    adr = re.compile(rf"\bADR {old_n}\b") if old_n is not None else None
    found = []
    for path in _repository_files(root):
        rel = path.relative_to(root).as_posix()
        if rel == ".okf/log.md" or rel.startswith(".loop/"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            hits = [line.find(t) for t in terms if t in line]
            if adr is not None and (match := adr.search(line)):
                hits.append(match.start())
            if hits:
                found.append(
                    Mention(file=rel, line=number, text=_excerpt(line, min(hits)))
                )
    return found


def _excerpt(line: str, at: int) -> str:
    """``line`` stripped, or, when longer than ``EXCERPT`` characters, the part around position ``at``."""
    if len(line.strip()) <= EXCERPT:
        return line.strip()
    start = max(0, at - EXCERPT // 4)
    part = line[start : start + EXCERPT].strip()
    return (
        ("..." if start else "") + part + ("..." if start + EXCERPT < len(line) else "")
    )


def _id(okf: Path, path: Path) -> str:
    """The id a log line names ``path``, a page in ``okf``, by."""
    return path.relative_to(okf).with_suffix("").as_posix()


def mv(root: Path, old: str, new: str, now: datetime | None = None) -> Moved:
    """Rename concept ``old`` to ``new`` in its folder and rewrite the links to it.

    Parameters
    ----------
    root : Path
        The repository root, holding .okf/ and docs/.
    old : str
        The concept's id, as ``kmctl review due`` prints it, such as
        ``decisions/0008-use-a-queue`` or ``prototypes/parser-speed``.
    new : str
        Its new id, in the same folder. For a decision it starts with a
        four-digit number no other record holds.
    now : datetime | None
        The date of the log line; now when omitted.

    Returns
    -------
    Moved
        The two ids, the new path, the files rewritten and the mentions left.

    Raises
    ------
    ConceptError
        When ``old`` names no concept in a section, or ``new`` is the same,
        leaves the folder, is not kebab-case, exists, or, for a decision, has
        no number or one another record holds. Nothing is written.
    """
    now = now or datetime.now(UTC)
    okf = root / ".okf"
    old_id, new_id = _clean(old), _clean(new)
    old_path = _locate(okf, old_id)
    new_path = _check_new(okf, old_id, new_id, old_path)
    numbers = None
    if old_id.startswith("decisions/"):
        old_number = _NUMBERED.match(old_path.name)
        new_number = _NUMBERED.match(new_path.name)
        if old_number and new_number and old_number.group(1) != new_number.group(1):
            numbers = (old_number.group(1), new_number.group(1))

    terms = (old_id, old_path.name + ("/" if old_path.is_dir() else ""))
    old_resolved = old_path.resolve()
    # git mv stages the rename, so a later commit -a keeps the record.
    if _git(root, "mv", "--", str(old_path), str(new_path)) is None:
        old_path.rename(new_path)
    new_resolved = new_path.resolve()
    updated = []
    for page in _pages(root):
        base = okf if page.is_relative_to(okf) else root
        text = page.read_text(encoding="utf-8", errors="surrogateescape")
        result = _rewrite(text, page, base, old_resolved, new_resolved, numbers)
        if numbers is not None and page == new_path:
            result = _renumber(result, *numbers)
        if page == root / SUMMARY:
            result = _checked(result, old_id, new_id)
        if result != text:
            page.write_text(result, encoding="utf-8", errors="surrogateescape")
            updated.append(page)

    others = [
        f"`{_id(okf, p)}`"
        for p in updated
        if p.is_relative_to(okf) and not p.is_relative_to(new_path) and p != new_path
    ]
    line = f"- Moved `{old_id}` to `{new_id}` with `kmctl mv`"
    if others:
        line += ", rewriting links to it in " + ", ".join(others)
    append_log(okf / "log.md", line + ".", now)
    return Moved(
        old=old_id,
        new=new_id,
        path=new_path.relative_to(root).as_posix(),
        updated=sorted(p.relative_to(root).as_posix() for p in updated),
        mentions=_mentions(root, terms, numbers[0] if numbers else None),
    )
