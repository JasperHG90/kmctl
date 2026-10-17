"""Generate each Diataxis folder's README.md index under docs/ (ADR 0022).

A folder index is a ``GENERATED`` marker line, a heading, then one entry per
page: the page's ``#`` title as link text and its ``description`` front
matter after it. kmctl rewrites a folder index only when it is missing or
carries the marker, so a hand-written one is never lost. docs/README.md
stays hand-written and links each folder.
"""

from pathlib import Path

from kmctl.concepts import link_text, one_line
from kmctl.okf import BadFrontMatter, field, front_matter

#: Each Diataxis folder's heading in its generated index and its docs/README.md link.
FOLDER_TITLES: dict[str, str] = {
    "tutorials": "Tutorials",
    "how-to": "How-to guides",
    "reference": "Reference",
    "explanation": "Explanation",
}

#: The first line of a folder index kmctl writes; without it kmctl leaves the file alone.
GENERATED = (
    "<!-- kmctl writes this index from the pages in this folder: "
    "run kmctl check --fix to update it, do not edit it by hand. -->"
)


def _title(page: Path) -> str:
    """The page's first ``#`` heading after its front matter, or its file name."""
    text = page.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        text = text[end + 4 :] if end != -1 else text
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return page.stem


def _description(page: Path) -> str:
    """The page's ``description`` front matter as one line, or "" when it has none."""
    try:
        value = field(front_matter(page), "description", "")
    except BadFrontMatter:
        return ""
    return one_line(value) if isinstance(value, str) else ""


def folder_pages(folder: Path) -> list[Path]:
    """The visible pages a folder index lists: every .md below it but its own README.md."""
    return sorted(
        p
        for p in folder.rglob("*.md")
        if p != folder / "README.md"
        and not any(part.startswith(".") for part in p.relative_to(folder).parts)
    )


def folder_index(folder: Path) -> str:
    """The text kmctl generates for ``folder``'s README.md index."""
    lines = [GENERATED, f"# {FOLDER_TITLES[folder.name]}", ""]
    for page in folder_pages(folder):
        entry = f"- [{link_text(_title(page))}]({page.relative_to(folder).as_posix()})"
        description = _description(page)
        lines.append(entry + (f": {description}" if description else ""))
    return "\n".join(lines).rstrip("\n") + "\n"


def is_generated(index: Path) -> bool:
    """True when ``index`` starts with kmctl's ``GENERATED`` marker."""
    try:
        text = index.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False
    return text.splitlines()[:1] == [GENERATED]


def diataxis_folders(root: Path) -> list[Path]:
    """The Diataxis folders that exist under ``root``'s docs/."""
    docs = root / "docs"
    return [docs / name for name in FOLDER_TITLES if (docs / name).is_dir()]


def fix_folder_indexes(root: Path) -> tuple[list[str], list[str]]:
    """Write each Diataxis folder's README.md that is missing, or generated and out of date.

    Returns
    -------
    tuple[list[str], list[str]]
        The indexes created and the indexes rewritten, relative to ``root``.
    """
    created, updated = [], []
    for folder in diataxis_folders(root):
        index = folder / "README.md"
        text = folder_index(folder)
        rel = index.relative_to(root).as_posix()
        if not index.exists():
            created.append(rel)
        elif is_generated(index) and index.read_text(encoding="utf-8") != text:
            updated.append(rel)
        else:
            continue
        index.write_text(text, encoding="utf-8")
    return created, updated
