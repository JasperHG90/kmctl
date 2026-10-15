"""Deterministic knowledge checks: indexes, prototype READMEs, and links that must resolve.

The index format, which every kmctl verb that writes an index follows:

- docs/README.md indexes every page under docs/; each .okf/ section's
  index.md indexes the concepts in that section; .okf/index.md indexes the
  sections and any concept at the bundle root.
- An entry is a markdown list item, outside a code fence, whose first link is
  a relative link to a page in that folder or below. In .okf/prototypes/ the
  concept is each prototype's README.md. External links, anchors and links
  that leave the folder are not entries.
- A target is read without <angle brackets>, #anchor or ?query, and
  percent-decoded, as GitHub renders it. Reference-style definitions
  (``[ref]: path``) are links, but never index entries.
- Hidden files and folders (a name starting with ".") are not pages.
- Every folder directly under .okf/prototypes/ is a prototype and needs a
  README.md (check name ``prototype``).
- Every link in docs/, and every .okf/ link that leaves the bundle, must
  resolve (check name ``link``); links inside .okf/ are the okf validator's.
- No concept counts are written or checked.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import unquote

RESERVED = {"index.md", "log.md"}
_TARGET = r"(<[^>\n]*>|[^)\s]+)(?:\s+(?:\"[^\"]*\"|'[^']*'))?"
_ENTRY = re.compile(r"^\s*[-*+]\s+.*?\[[^\]]*\]\(" + _TARGET + r"\)")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_LINK = re.compile(r"!?\[[^\]]*\]\(" + _TARGET + r"\)")
# A footnote definition ([^1]: text) is not a link.
_REF_DEF = re.compile(r"^ {0,3}\[(?!\^)[^\]]+\]:\s*(<[^>\n]*>|\S+)")
_CODE_SPAN = re.compile(r"`[^`]*`")


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
    level : Literal["error", "skipped"]
        ``error`` for a failure; ``skipped`` for a part of the repository a
        check had nothing to look at.
    """

    check: str
    file: str
    line: int | None
    message: str
    level: Literal["error", "skipped"] = "error"


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


def _entries(index: Path) -> list[tuple[int, str]]:
    """The (line, target) of each entry in ``index``, by the format in the module docstring.

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
        target = _target(match.group(1))
        if not target or target.startswith(("/", "mailto:")) or "://" in target:
            continue
        if not (index.parent / target).resolve().is_relative_to(folder):
            continue
        found.append((number, target))
    return found


def _rel(root: Path, path: Path) -> str:
    """``path`` relative to ``root``, with forward slashes, as findings name files."""
    return path.relative_to(root).as_posix()


def _visible(folder: Path, path: Path) -> bool:
    """True when no part of ``path`` below ``folder`` is hidden."""
    return not any(part.startswith(".") for part in path.relative_to(folder).parts)


def _check_index(root: Path, index: Path, members: list[Path]) -> list[Finding]:
    """Findings for one index: members it does not list, and entries with no file."""
    try:
        entries = _entries(index)
    except _Unreadable:
        return [Finding("index", _rel(root, index), None, "index is not UTF-8 text")]
    findings = []
    listed = set()
    for line, target in entries:
        path = (index.parent / target).resolve()
        listed.add(path)
        if not path.exists():
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


def check_docs(root: Path) -> list[Finding]:
    """Check that docs/README.md lists every visible page under docs/ and nothing missing."""
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
    pages = [p for p in docs.rglob("*.md") if p != index and _visible(docs, p)]
    return _check_index(root, index, sorted(pages))


def check_okf(root: Path) -> list[Finding]:
    """Check the root index lists every section and root concept, and each section its concepts."""
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
            (okf / t).resolve() for _, t in _entries(root_index)
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
        {number: target for number, target in _entries(page)} if skip_entries else {}
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


def run_checks(root: Path) -> list[Finding]:
    """Run every knowledge check on the repository at ``root``.

    Parameters
    ----------
    root : Path
        The repository root, holding docs/ and .okf/.

    Returns
    -------
    list[Finding]
        Every finding, errors and skipped parts alike, in check order.
    """
    return (
        check_docs(root) + check_okf(root) + check_prototypes(root) + check_links(root)
    )
