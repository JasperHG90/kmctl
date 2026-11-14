"""Cut a folder of markdown docs into sections, one per header section of each live page, with numbered sentences and change keys."""

import hashlib
import json
import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from kmaudit import AuditError, instructions, namespaces
from kmaudit.frontmatter import BadFrontMatter, split_front_matter
from kmaudit.frontmatter import field as okf_field

HEADER_LEVELS = 3
CORRECTION_PREFIXES = ("Correction", "Amended")
EARLIER_SENTENCES = 40
SKIP_NAMES = frozenset({"index.md", "log.md"})
SKIP_DIRS = frozenset({"prototypes"})

_HEADER = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_FENCE_LINE = re.compile(r"^\s*(```|~~~)")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z`\[(*\"'/])")
_FENCE = re.compile(r"(```.*?```|~~~.*?~~~)", re.DOTALL)
_BULLET = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_BLANK_LINE = re.compile(r"\n\s*\n")
_NOT_SLUG = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class Target:
    """What a path given to a ``kmaudit`` verb names: one namespace, maybe narrowed to some of its files.

    Attributes
    ----------
    bundle : Path
        The audited folder, an OKF bundle or any folder of markdown; concept ids are paths relative to it.
    files : list[Path] | None
        The files to cut, or None for the whole folder.
    root : Path
        The repository that holds the folder (git's top level, else the folder's parent); the stores live here.
    """

    bundle: Path
    files: list[Path] | None
    root: Path

    def concept(self, path: Path) -> str:
        """The concept id of a file in the bundle: its path below the bundle root, without .md."""
        return path.resolve().relative_to(self.bundle).with_suffix("").as_posix()

    @property
    def namespace(self) -> str:
        """The namespace: the audited folder's path below the repository root."""
        return namespaces.name_of(self.root, self.bundle)

    @property
    def concepts(self) -> set[str] | None:
        """The concept ids in scope, or None for the whole bundle."""
        return None if self.files is None else {self.concept(f) for f in self.files}


@dataclass(frozen=True)
class Section:
    """One header section of one concept, as an extraction agent sees it.

    Attributes
    ----------
    id : str
        The concept id plus the slug of its header path, like ``manifesto#parts``.
    key : str
        A hash of everything the extraction depends on: text, context, ids, title, status and the instructions.
    """

    id: str
    concept: str
    type: str
    status: str | None
    title: str
    section: str
    sentences: list[str]
    corrections: str
    earlier: str
    earlier_ids: list[str] = field(default_factory=list)
    is_correction: bool = False
    key: str = ""


def _read(path: Path) -> tuple[dict, str]:
    """The front matter and body of a concept file; refuses one that is not readable."""
    try:
        return split_front_matter(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, BadFrontMatter) as error:
        raise AuditError(
            f"{path}: front matter does not read ({error}); fix it, then run the verb again"
        ) from error


def _is_bundle_root(folder: Path) -> bool:
    """Whether the folder holds an index.md whose front matter carries okf_version."""
    index = folder / "index.md"
    if not index.is_file():
        return False
    try:
        meta, _ = split_front_matter(index.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, BadFrontMatter):
        return False
    return okf_field(meta, "okf_version") is not None


def is_okf_bundle(folder: Path) -> bool:
    """Whether ``folder`` is an OKF bundle: an ``index.md`` with ``okf_version``, or a folder named ``.okf``."""
    return folder.name == ".okf" or _is_bundle_root(folder)


def resolve_target(path: Path) -> Target:
    """The namespace ``path`` names, narrowed to the files under it when it is not the namespace's own folder.

    A path inside an existing namespace narrows that namespace and never opens
    a store of its own. Otherwise a path inside an OKF bundle means the
    bundle, and a folder with no namespace above it opens one, unless a
    namespace already sits inside it. The repository root holding ``.okf/``
    means ``.okf``.

    Raises
    ------
    AuditError
        If the path does not exist, is not markdown, holds no page in scope,
        is a file with no namespace or bundle above it, or would overlap an
        existing namespace.
    """
    path = path.resolve()
    if not path.exists():
        raise AuditError(
            f"{path} does not exist; give a folder of markdown docs or a page in one"
        )
    if path.is_file() and path.suffix != ".md":
        raise AuditError(
            f"{path} is not a markdown file; give a folder of markdown docs or a page in one"
        )
    start = path if path.is_dir() else path.parent
    root = namespaces.repository_root(start)
    if path == root:
        if not (root / ".okf").is_dir():
            raise AuditError(
                f"{root} is the repository root, which holds no .okf/; give the folder of "
                "markdown docs to audit, such as docs, so it gets a namespace of its own"
            )
        path = root / ".okf"
    taken = namespaces.existing(root)
    owner = next(
        (
            folder
            for folder in sorted(
                taken.values(), key=lambda f: len(f.parts), reverse=True
            )
            if path == folder or folder in path.parents
        ),
        None,
    )
    if owner is None:
        owner = next(
            (
                f
                for f in [path, *path.parents]
                if f.is_dir() and f.is_relative_to(root) and is_okf_bundle(f)
            ),
            None,
        )
    if owner is None:
        if path.is_file():
            hint = start.relative_to(root) if start.is_relative_to(root) else start
            raise AuditError(
                f"{path} is in no audited folder yet; give the folder first, as in "
                f"kmaudit claims todo {hint}"
            )
        inside = sorted(n for n, f in taken.items() if path in f.parents)
        if inside:
            raise AuditError(
                f"{path} holds the namespace(s) {', '.join(inside)}, which would overlap it; audit "
                f"those folders instead, or delete their stores under {namespaces.STORE_DIR}/ "
                "to start over at this folder"
            )
        if not any(path.rglob("*.md")):
            raise AuditError(
                f"{path} holds no markdown pages; give a folder of markdown docs, such as docs or .okf"
            )
        owner = path
    if path == owner:
        return Target(bundle=owner, files=None, root=root)
    pages = concept_paths(owner)
    if path.is_file():
        if path not in pages:
            raise AuditError(
                f"{path} is not a page kmaudit audits (an OKF bundle's index.md, log.md and "
                "prototypes/ are skipped); give a page of the folder"
            )
        return Target(bundle=owner, files=[path], root=root)
    files = [p for p in pages if path in p.parents]
    if not files:
        raise AuditError(
            f"{path} holds no page kmaudit audits; give a folder with markdown pages"
        )
    return Target(bundle=owner, files=files, root=root)


def split_sentences(text: str) -> list[str]:
    """Split a section's text into the units a claim can cite.

    A code block or table is one unit, a list item is split by sentence, and a
    fragment of two words or fewer (a list number, a bold label) joins the
    sentence after it.
    """
    units: list[str] = []
    for index, part in enumerate(_FENCE.split(text)):
        if index % 2 == 1:
            units.append(part.strip())
        else:
            units.extend(_split_prose(part))
    return [unit for unit in units if unit]


def _split_prose(text: str) -> list[str]:
    """Split text outside code blocks into units, block by block."""
    units: list[str] = []
    for block in _BLANK_LINE.split(text.strip()):
        tables, items = _tables_and_items(block.splitlines())
        units.extend(tables)
        for item in items:
            units.extend(_split_item(item))
    return units


def _tables_and_items(lines: list[str]) -> tuple[list[str], list[str]]:
    """Group a block's lines into tables and list items; a line that starts no item continues the last one."""
    tables: list[str] = []
    items: list[str] = []
    table: list[str] = []
    for line in lines:
        if line.lstrip().startswith("|"):
            table.append(line.strip())
            continue
        if table:
            tables.append("\n".join(table))
            table = []
        if _BULLET.match(line) or not items:
            items.append(line.strip())
        else:
            items[-1] += " " + line.strip()
    if table:
        tables.append("\n".join(table))
    return tables, items


def _split_item(item: str) -> list[str]:
    """Split one list item into sentences, joining short fragments to the next one."""
    units: list[str] = []
    pending = ""
    parts = _SENTENCE_END.split(item)
    for part in parts:
        sentence = (pending + " " + part).strip() if pending else part.strip()
        if len(sentence.split()) <= 2 and len(parts) > 1:
            pending = sentence
            continue
        pending = ""
        if sentence:
            units.append(sentence)
    if pending:
        units.append(pending)
    return units


def split_headers(body: str) -> list[tuple[str, str]]:
    """Split a concept's body into (header path, text) pairs at its ``#`` to ``###`` headers.

    A ``#`` inside a fenced code block is not a header. Text before the first
    header has an empty path. Deeper headers stay in the text.
    """
    sections: list[tuple[str, str]] = []
    path: list[str | None] = [None] * HEADER_LEVELS
    lines: list[str] = []
    in_fence = False

    def flush() -> None:
        text = "\n".join(lines).strip()
        if text:
            sections.append((" > ".join(h for h in path if h), text))
        lines.clear()

    for line in body.splitlines():
        if _FENCE_LINE.match(line):
            in_fence = not in_fence
        match = None if in_fence else _HEADER.match(line)
        if match and len(match.group(1)) <= HEADER_LEVELS:
            flush()
            level = len(match.group(1))
            path[level - 1] = match.group(2)
            for deeper in range(level, HEADER_LEVELS):
                path[deeper] = None
            continue
        lines.append(line)
    flush()
    return sections


def _slug(name: str, seen: dict[str, int]) -> str:
    """The slug of a header path below its top header; a repeat gets ``-2``, ``-3``."""
    below_top = name.split(" > ", 1)[-1]
    slug = _NOT_SLUG.sub("-", below_top.lower()).strip("-") or "top"
    seen[slug] = seen.get(slug, 0) + 1
    return f"{slug}-{seen[slug]}" if seen[slug] > 1 else slug


def _earlier(earlier: list[tuple[str, list[str]]]) -> str:
    """The earlier sections' sentences, labelled [s.n], keeping the last ``EARLIER_SENTENCES``."""
    lines: list[str] = []
    for s, (name, sentences) in enumerate(earlier, 1):
        lines.append(f"{name or '(top)'}:")
        lines.extend(f"[{s}.{n}] {sentence}" for n, sentence in enumerate(sentences, 1))
    labelled = [line for line in lines if line.startswith("[")]
    kept = set(labelled[-EARLIER_SENTENCES:])
    return "\n".join(line for line in lines if not line.startswith("[") or line in kept)


def _key(section: Section, guidance: str | None = None) -> str:
    """Hash everything an extraction of ``section`` depends on, the guidance included.

    Parameters
    ----------
    section :
        The section to key.
    guidance :
        The guidance hash to key it with; the current one when None.
    """
    content = [
        section.section,
        section.sentences,
        section.corrections,
        section.type,
        section.earlier,
        section.id,
        section.concept,
        section.title,
        section.status,
        section.earlier_ids,
        instructions.instructions_hash() if guidance is None else guidance,
    ]
    return hashlib.sha256(json.dumps(content).encode()).hexdigest()[:16]


def previous_keys(section: Section) -> set[str]:
    """The keys ``section`` had under earlier guidance whose answers still stand (``PREVIOUS_HASHES``)."""
    return {_key(section, h) for h in instructions.PREVIOUS_HASHES}


def concept_paths(bundle: Path) -> list[Path]:
    """The folder's pages in sorted order: every ``.md`` file, less an OKF bundle's reserved names and skipped folders."""
    bundle = bundle.resolve()
    pages = sorted(bundle.rglob("*.md"))
    if not is_okf_bundle(bundle):
        return pages
    return [
        p
        for p in pages
        if p.name not in SKIP_NAMES and not SKIP_DIRS & set(p.relative_to(bundle).parts)
    ]


def concept_sections(bundle: Path, path: Path) -> list[Section]:
    """The sections of one concept that hold a sentence; none for a deprecated concept."""
    meta, body = _read(path)
    if okf_field(meta, "status") == "deprecated":
        return []
    concept = path.resolve().relative_to(bundle.resolve()).with_suffix("").as_posix()
    parts = split_headers(body.removeprefix("\n---").lstrip("\n"))
    # A correction may overturn an earlier one, so each correction section sees
    # the corrections after it; every other section sees them all.
    fixes = [
        (i, f"{name}\n{text}")
        for i, (name, text) in enumerate(parts)
        if name.rsplit(" > ", 1)[-1].startswith(CORRECTION_PREFIXES)
    ]
    status = okf_field(meta, "status")
    out: list[Section] = []
    seen: dict[str, int] = {}
    earlier: list[tuple[str, list[str]]] = []
    earlier_ids: list[str] = []
    for i, (name, text) in enumerate(parts):
        sentences = split_sentences(text)
        if not sentences:
            continue
        is_correction = name.rsplit(" > ", 1)[-1].startswith(CORRECTION_PREFIXES)
        section = Section(
            id=f"{concept}#{_slug(name, seen)}",
            concept=concept,
            type=str(okf_field(meta, "type", "")),
            status=None if status is None else str(status),
            title=str(okf_field(meta, "title", "")),
            section=name,
            sentences=sentences,
            corrections="\n\n".join(
                fix for at, fix in fixes if not is_correction or at > i
            ),
            earlier=_earlier(earlier),
            earlier_ids=list(earlier_ids),
            is_correction=is_correction,
        )
        out.append(_with_key(section))
        if not is_correction:
            earlier.append((name, sentences))
            earlier_ids.append(section.id)
    return out


def _with_key(section: Section) -> Section:
    """``section`` with its key filled in."""
    return Section(**{**section.__dict__, "key": _key(section)})


def cut(target: Target) -> Iterator[Section]:
    """Yield every section of the target's concepts, in path order."""
    paths: Iterable[Path] = (
        sorted(p.resolve() for p in target.files)
        if target.files is not None
        else concept_paths(target.bundle)
    )
    for path in paths:
        yield from concept_sections(target.bundle, path)
