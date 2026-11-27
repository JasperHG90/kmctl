"""The files kmctl review due and kmctl verify treat as pages.

Both verbs read the page set from here, so an id one of them prints is one
the other takes.
"""

from pathlib import Path

#: File names in .okf/ that are never concepts.
RESERVED = {"index.md", "log.md"}


def concept_files(okf: Path) -> list[Path]:
    """The concept files under ``okf``, sorted.

    Reserved names, anything under a dot folder, and every prototype file
    but a prototype folder's own ``README.md`` are left out.
    """
    found = []
    for path in sorted(okf.rglob("*.md")):
        parts = path.relative_to(okf).parts
        if path.name in RESERVED or any(p.startswith(".") for p in parts):
            continue
        if parts[0] == "prototypes" and (len(parts) != 3 or path.name != "README.md"):
            continue
        found.append(path)
    return found


def docs_pages(docs: Path) -> list[Path]:
    """The docs pages under ``docs``, sorted; ``README.md`` indexes and dot folders are left out."""
    return sorted(
        p
        for p in docs.rglob("*.md")
        if p.name != "README.md"
        and not any(part.startswith(".") for part in p.relative_to(docs).parts)
    )
