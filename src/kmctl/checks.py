"""Deterministic knowledge checks: indexes, prototype READMEs, and links that must resolve.

The index format, which every kmctl verb that writes an index follows:

- Each Diataxis folder under docs/ (tutorials, how-to, reference,
  explanation) has a README.md index that kmctl generates (see
  ``kmctl.docs_index``); a missing or out-of-date one fails, and
  ``kmctl check --fix`` writes it. A hand-written one, without the marker,
  is left alone with a warning and checked like any index.
  docs/README.md links each of those folders (a warning when it does not)
  and indexes every other page under docs/. Each .okf/ section's index.md
  indexes the concepts in that section; .okf/index.md indexes the sections
  and any concept at the bundle root.
- A docs/ page may carry front matter: ``description``, ``stale_after``,
  ``verified`` and ``sources``, the OKF v0.2 fields of those names (check
  name ``front-matter``). Each one present must have its OKF shape.
- An entry is a markdown list item, outside a code fence, whose first link is
  a relative link to a page in that folder or below. In .okf/prototypes/ the
  concept is each prototype's README.md. External links, anchors and links
  that leave the folder are not entries.
- A target is read without <angle brackets>, #anchor or ?query, and
  percent-decoded, as GitHub renders it. Reference-style definitions
  (``[ref]: path``) are links, but never index entries.
- Hidden files and folders (a name starting with ".") are not pages.
- A decision record, ``.okf/decisions/NNNN-slug.md``, whose ``title`` or
  ``#`` heading starts with ``ADR`` and a number must carry its file's
  number (check name ``decision``). The decisions index's entry for a record
  reads the record's title, or just ``ADR NNNN`` (check name ``index``).
- Every folder directly under .okf/prototypes/ is a prototype and needs a
  README.md (check name ``prototype``).
- Every link in docs/, and every .okf/ link that leaves the bundle, must
  resolve (check name ``link``); links inside .okf/ are the okf validator's.
- The body of .okf/summary.md, outside its front matter, holds at most
  ``WORD_LIMIT`` words (check name ``summary``). A summary behind the
  concepts that changed after it is a warning, never a failure.
- No concept counts are written or checked.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import unquote

from kmctl.concepts import link_text
from kmctl.docs_index import (
    FOLDER_TITLES,
    diataxis_folders,
    folder_index,
    folder_pages,
    is_generated,
)
from kmctl.okf import (
    BadFrontMatter,
    as_datetime,
    field,
    front_matter,
    split_front_matter,
)
from kmctl.summary import SUMMARY, WORD_LIMIT, body_words, changed_concepts
from kmctl.summary import reason as summary_reason

RESERVED = {"index.md", "log.md"}
_TARGET = r"(<[^<>\n]*>|[^<)\s][^)\s]*)(?:\s+(?:\"[^\"]*\"|'[^']*'))?"
_ENTRY = re.compile(r"^\s*[-*+]\s+.*?\[([^\]]*)\]\(" + _TARGET + r"\)")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_LINK = re.compile(r"!?\[[^\]]*\]\(" + _TARGET + r"\)")
# A footnote definition ([^1]: text) is not a link.
_REF_DEF = re.compile(r"^ {0,3}\[(?!\^)[^\]]+\]:\s*(<[^<>\n]*>(?=\s|$)|[^<\s]\S*)")
_CODE_SPAN = re.compile(r"`[^`]*`")
_RECORD = re.compile(r"(\d{4,})-.+\.md")
_ADR = re.compile(r"ADR (\d+)\b")


@dataclass(frozen=True)
class Finding:
    """One result of a check, as the CLI and the CI action report it.

    Attributes
    ----------
    check : str
        The check that produced it, such as ``index``.
    file : str
        The file or folder it is about, relative to the repository root.
    line : int | None
        The line in ``file``, when the finding is about one line.
    message : str
        What is wrong, in one line.
    level : Literal["error", "warning", "skipped"]
        ``error`` for a failure; ``warning`` for something to fix that does
        not fail the check; ``skipped`` for a part of the repository a check
        had nothing to look at.
    """

    check: str
    file: str
    line: int | None
    message: str
    level: Literal["error", "warning", "skipped"] = "error"


class _Unreadable(Exception):
    """An index that is not UTF-8 text."""


def _read(path: Path) -> str:
    """The UTF-8 text of ``path``.

    Raises
    ------
    _Unreadable
        When ``path`` is not UTF-8 text.
    """
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise _Unreadable(str(path)) from error


def _prose_lines(text: str) -> list[tuple[int, str]]:
    """The (line number, text) of each line outside a code fence.

    A fence opens on 0-3 spaces then 3+ backticks or tildes, and closes only on
    a line of the same character at least as long, with nothing after it.
    """
    lines = []
    fence = ""  # the opening fence while inside a code block, else ""
    for number, line in enumerate(text.splitlines(), start=1):
        opener = _FENCE.match(line)
        if opener:
            mark = opener.group(1)
            if not fence:
                fence = mark
            elif (
                mark[0] == fence[0]
                and len(mark) >= len(fence)
                and not line.strip()[len(mark) :]
            ):
                fence = ""
            continue
        if not fence:
            lines.append((number, line))
    return lines


def _target(raw: str) -> str:
    """A link target as a file path: brackets, anchor and query dropped, percent-decoded."""
    target = raw[1:-1] if raw.startswith("<") and raw.endswith(">") else raw
    target = target.split("#", 1)[0].split("?", 1)[0]
    return unquote(target)


def _entries(index: Path) -> list[tuple[int, str, str]]:
    """The (line, target, link text) of each entry in ``index``, by the format in the module docstring.

    Raises
    ------
    _Unreadable
        When ``index`` is not UTF-8 text.
    """
    found = []
    folder = index.parent.resolve()
    for number, text in _prose_lines(_read(index)):
        match = _ENTRY.match(text)
        if not match:
            continue
        target = _target(match.group(2))
        if not target or target.startswith(("/", "mailto:")) or "://" in target:
            continue
        if not (index.parent / target).resolve().is_relative_to(folder):
            continue
        found.append((number, target, match.group(1)))
    return found


def _rel(root: Path, path: Path) -> str:
    """``path`` relative to ``root``, with forward slashes, as findings name files."""
    return path.relative_to(root).as_posix()


def _visible(folder: Path, path: Path) -> bool:
    """True when no part of ``path`` below ``folder`` is hidden."""
    return not any(part.startswith(".") for part in path.relative_to(folder).parts)


def _check_index(
    root: Path,
    index: Path,
    members: list[Path],
    missing_ok: frozenset[Path] = frozenset(),
) -> list[Finding]:
    """Findings for one index: members it does not list, and entries with no file.

    An entry linking a path in ``missing_ok`` (a folder index already reported
    missing) is not reported again.
    """
    try:
        entries = _entries(index)
    except _Unreadable:
        return [Finding("index", _rel(root, index), None, "index is not UTF-8 text")]
    findings = []
    listed = set()
    for line, target, _ in entries:
        path = (index.parent / target).resolve()
        listed.add(path)
        if not path.exists() and path not in missing_ok:
            findings.append(
                Finding(
                    "index",
                    _rel(root, index),
                    line,
                    f"entry links {target}, which does not exist",
                )
            )
    for member in members:
        if member.resolve() not in listed:
            findings.append(
                Finding(
                    "index",
                    _rel(root, member),
                    None,
                    f"not listed in {_rel(root, index)}",
                )
            )
    return findings


def _section_concepts(section: Path) -> list[Path]:
    """The concepts a section's index must list: every visible page, or each prototype's README.md."""
    if section.name == "prototypes":
        return sorted(
            p / "README.md"
            for p in section.iterdir()
            if not p.name.startswith(".") and (p / "README.md").is_file()
        )
    return sorted(
        p
        for p in section.rglob("*.md")
        if p.name not in RESERVED and _visible(section, p)
    )


def entry_targets(index: Path) -> list[str]:
    """The target of each entry in ``index``, or none when it is not UTF-8 text."""
    try:
        return [target for _, target, _ in _entries(index)]
    except _Unreadable:
        return []


def links_folder(root_index: Path, folder: Path) -> bool:
    """True when docs/README.md has an entry linking ``folder`` or its README.md."""
    targets = {folder.resolve(), (folder / "README.md").resolve()}
    return any(
        (root_index.parent / t).resolve() in targets for t in entry_targets(root_index)
    )


def _check_folder(root: Path, root_index: Path, folder: Path) -> list[Finding]:
    """Findings for one Diataxis folder: its index, and its link from docs/README.md."""
    index = folder / "README.md"
    findings = []
    if not links_folder(root_index, folder):
        findings.append(
            Finding(
                "index",
                _rel(root, root_index),
                None,
                f"does not link {folder.name}/; add "
                f"'- [{FOLDER_TITLES[folder.name]}]({folder.name}/README.md)'",
                "warning",
            )
        )
    if not index.is_file():
        findings.append(
            Finding(
                "index",
                _rel(root, folder),
                None,
                "folder has no README.md index; run kmctl check --fix",
            )
        )
    elif is_generated(index):
        if _read(index) != folder_index(folder):
            findings.append(
                Finding(
                    "index",
                    _rel(root, index),
                    None,
                    "index does not match the pages in its folder; run kmctl check --fix",
                )
            )
    else:
        findings.append(
            Finding(
                "index",
                _rel(root, index),
                None,
                "hand-written index: kmctl does not manage it, so kmctl check --fix "
                "leaves it alone; delete it to have kmctl generate it",
                "warning",
            )
        )
        findings += _check_index(root, index, folder_pages(folder))
    return findings


def _bad_date(value: object) -> bool:
    return as_datetime(value) is None


def _field_problems(
    description: object, stale_after: object, verified: object, sources: object
) -> list[str]:
    """What is wrong with each docs page front matter field present (not None), by its OKF shape."""
    problems = []
    if description is not None and not isinstance(description, str):
        problems.append("description must be a string")
    if stale_after is not None and _bad_date(stale_after):
        problems.append("stale_after must be a date or a UTC timestamp")
    if verified is not None:
        items = [verified] if isinstance(verified, dict) else verified
        if not isinstance(items, list) or not all(
            isinstance(i, dict)
            and isinstance(i.get("by"), str)
            and not _bad_date(i.get("at"))
            for i in items
        ):
            problems.append("verified must be a list of {by, at} with a date at")
    if sources is not None and (
        not isinstance(sources, list)
        or not all(
            isinstance(i, str)
            or (isinstance(i, dict) and isinstance(i.get("resource"), str))
            for i in sources
        )
    ):
        problems.append("sources must be a list of paths, or of {resource} mappings")
    return problems


def _check_front_matter(root: Path, page: Path) -> list[Finding]:
    """Findings for the front matter of one docs page; a page without any passes."""
    try:
        meta = front_matter(page)
    except BadFrontMatter:
        return [
            Finding(
                "front-matter", _rel(root, page), None, "front matter does not parse"
            )
        ]
    problems = _field_problems(
        field(meta, "description"),
        field(meta, "stale_after"),
        field(meta, "verified"),
        field(meta, "sources"),
    )
    return [Finding("front-matter", _rel(root, page), None, p) for p in problems]


def check_docs(root: Path) -> list[Finding]:
    """Check docs/: each Diataxis folder's index, docs/README.md, and each page's front matter."""
    docs = root / "docs"
    if not docs.is_dir():
        return [
            Finding("index", "docs/", None, "skipped docs/: no docs/ folder", "skipped")
        ]
    index = docs / "README.md"
    if not index.is_file():
        return [
            Finding("index", "docs/README.md", None, "docs/ has no README.md index")
        ]
    folders = diataxis_folders(root)
    findings = []
    for folder in folders:
        findings += _check_folder(root, index, folder)
    pages = sorted(p for p in docs.rglob("*.md") if p != index and _visible(docs, p))
    others = [p for p in pages if not any(p.is_relative_to(f) for f in folders)]
    missing = frozenset(
        (f / "README.md").resolve() for f in folders if not (f / "README.md").is_file()
    )
    findings += _check_index(root, index, others, missing)
    for page in pages:
        if page.name != "README.md":
            findings += _check_front_matter(root, page)
    return findings


def check_okf(root: Path) -> list[Finding]:
    """Check the root index lists every section and root concept, each section its concepts, and decision numbers."""
    okf = root / ".okf"
    if not okf.is_dir():
        return [
            Finding("index", ".okf/", None, "skipped .okf/: no .okf/ folder", "skipped")
        ]
    root_index = okf / "index.md"
    if not root_index.is_file():
        return [Finding("index", ".okf/index.md", None, ".okf/ has no index.md")]
    sections = sorted(
        p for p in okf.iterdir() if p.is_dir() and not p.name.startswith(".")
    )
    root_concepts = sorted(p for p in okf.glob("*.md") if p.name not in RESERVED)
    findings = _check_index(root, root_index, root_concepts)
    try:
        linked: set[Path] | None = {
            (okf / t).resolve() for _, t, _ in _entries(root_index)
        }
    except _Unreadable:
        linked = None  # already reported once; do not report every section as unlinked
    for section in sections:
        targets = {section.resolve(), (section / "index.md").resolve()}
        if linked is not None and not targets & linked:
            findings.append(
                Finding(
                    "index",
                    _rel(root, section),
                    None,
                    "section is not linked from .okf/index.md",
                )
            )
        index = section / "index.md"
        if not index.is_file():
            findings.append(
                Finding("index", _rel(root, section), None, "section has no index.md")
            )
            continue
        findings += _check_index(root, index, _section_concepts(section))
        if section.name == "decisions":
            findings += _check_decisions(root, section)
    return findings


def _check_decisions(root: Path, section: Path) -> list[Finding]:
    """Findings for decision records whose ADR number is not their file's, and index entries that misname them.

    A record's ``title`` or ``#`` heading that starts with ``ADR NNNN`` must
    carry the number its file name starts with. The section index's entry
    for a record must read the record's title, or just ``ADR NNNN``. A record
    whose front matter does not parse is the okf validator's to report.
    """
    findings = []
    records: dict[Path, tuple[str, str | None]] = {}
    for record in sorted(section.glob("*.md")):
        match = _RECORD.fullmatch(record.name)
        if not match:
            continue
        number = match.group(1)
        try:
            text = _read(record)
            meta, body = split_front_matter(text)
        except (_Unreadable, BadFrontMatter):
            continue
        title = field(meta, "title")
        title = title if isinstance(title, str) else None
        records[record.resolve()] = (number, title)
        offset = text[: len(text) - len(body)].count("\n")
        heading = next(
            (
                (offset + n, line[2:].strip())
                for n, line in _prose_lines(body)
                if line.startswith("# ")
            ),
            (None, None),
        )
        for name, line, value in (("title", None, title), ("# heading", *heading)):
            adr = _ADR.match(value or "")
            if adr and adr.group(1) != number:
                findings.append(
                    Finding(
                        "decision",
                        _rel(root, record),
                        line,
                        f"{name} says ADR {adr.group(1)}, but the file is number "
                        f"{number}; make it ADR {number}",
                    )
                )
    index = section / "index.md"
    try:
        entries = _entries(index)
    except _Unreadable:
        return findings  # _check_index already reported it
    for line, target, text in entries:
        found = records.get((section / target).resolve())
        if found is None:
            continue
        number, title = found
        short = f"ADR {number}"
        if text == short or (title and text == link_text(title)):
            continue
        fix = (
            f"the record's title, '{link_text(title)}', or '{short}'"
            if title
            else f"'{short}'"
        )
        findings.append(
            Finding(
                "index",
                _rel(root, index),
                line,
                f"entry for {target} reads '{text}'; make it {fix}",
            )
        )
    return findings


def check_prototypes(root: Path) -> list[Finding]:
    """Check that every folder directly under .okf/prototypes/ has a README.md concept.

    Folders below a prototype (its scripts or results) are not prototypes.
    """
    prototypes = root / ".okf" / "prototypes"
    if not prototypes.is_dir():
        return []
    return [
        Finding(
            "prototype", _rel(root, folder), None, "prototype folder has no README.md"
        )
        for folder in sorted(prototypes.iterdir())
        if folder.is_dir()
        and not folder.name.startswith(".")
        and not (folder / "README.md").is_file()
    ]


def _links(page: Path, skip_entries: bool = False) -> list[tuple[int, str]]:
    """The (line, target) of each markdown link outside code, with URLs and bare anchors left out.

    With ``skip_entries``, the one link per index entry that the index check
    already reports (see ``_entries``) is left out; every other link is kept.
    """
    found = []
    entries = (
        {number: target for number, target, _ in _entries(page)} if skip_entries else {}
    )
    for number, text in _prose_lines(_read(page)):
        skip = entries.get(number)
        prose = _CODE_SPAN.sub("", text)
        definition = _REF_DEF.match(prose)
        raws = _LINK.findall(prose) + ([definition.group(1)] if definition else [])
        for raw in raws:
            target = _target(raw)
            if skip is not None and target == skip:
                skip = None  # only the entry's own link belongs to the index check
                continue
            if target and "://" not in target and not target.startswith("mailto:"):
                found.append((number, target))
    return found


def check_links(root: Path) -> list[Finding]:
    """Check the links the okf validator does not: every link in docs/, and .okf/ links that leave it.

    In docs/ a relative link resolves from the page's folder and a ``/`` link
    from the repository root, as GitHub renders them. In .okf/ a ``/`` link
    resolves from the bundle root (OKF section 6.1) and stays in it, so only
    relative links that leave the bundle are checked here.
    """
    findings = []
    for folder in (root / "docs", root / ".okf"):
        if not folder.is_dir():
            continue
        bundle = folder.name == ".okf"
        for page in sorted(p for p in folder.rglob("*.md") if _visible(folder, p)):
            try:
                links = _links(page, skip_entries=page == folder / "README.md")
            except _Unreadable:
                continue  # the index check reports unreadable files
            for line, target in links:
                if target.startswith("/"):
                    if bundle:
                        continue
                    resolved = (root / target.lstrip("/")).resolve()
                else:
                    resolved = (page.parent / target).resolve()
                    if bundle and resolved.is_relative_to(folder.resolve()):
                        continue
                if not resolved.exists():
                    findings.append(
                        Finding(
                            "link",
                            _rel(root, page),
                            line,
                            f"link to {target} does not exist",
                        )
                    )
    return findings


def check_summary(root: Path) -> list[Finding]:
    """Check the bundle summary: its body fits ``WORD_LIMIT``, and whether it is behind its concepts.

    A body over the limit fails. A summary behind its concepts is a warning,
    never a failure: it is a report, as in kmctl review due (ADR 0027).
    """
    path = root / SUMMARY
    if not path.is_file():
        return []
    try:
        words = body_words(_read(path))
    except _Unreadable:
        return [Finding("summary", SUMMARY, None, "summary is not UTF-8 text")]
    findings = []
    if words > WORD_LIMIT:
        findings.append(
            Finding(
                "summary",
                SUMMARY,
                None,
                f"body has {words} words, over the limit of {WORD_LIMIT}; "
                "cut it, and link down to the concepts for the detail",
            )
        )
    changed = changed_concepts(root)
    if changed:
        findings.append(
            Finding(
                "summary",
                SUMMARY,
                None,
                f"summary is behind: {summary_reason(changed)}; update it, or run "
                "kmctl summary ack when it is still right",
                "warning",
            )
        )
    return findings


def run_checks(root: Path) -> list[Finding]:
    """Run every knowledge check on the repository at ``root``.

    Parameters
    ----------
    root : Path
        The repository root, holding docs/ and .okf/.

    Returns
    -------
    list[Finding]
        Every finding, errors, warnings and skipped parts alike, in check order.
    """
    return (
        check_docs(root)
        + check_okf(root)
        + check_prototypes(root)
        + check_summary(root)
        + check_links(root)
    )
