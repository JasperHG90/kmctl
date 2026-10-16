"""Create one docs/ page in its Diataxis folder, with a skeleton and its docs/README.md entry."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from kmctl.concepts import ConceptError, link_text, one_line, slug
from kmctl.kinds import skeleton

DocType = Literal["tutorial", "how-to", "reference", "explanation"]

FOLDERS: dict[str, str] = {
    "tutorial": "tutorials",
    "how-to": "how-to",
    "reference": "reference",
    "explanation": "explanation",
}


@dataclass(frozen=True)
class NewDoc:
    """What ``new_doc`` wrote."""

    path: str
    created_folder: bool


def new_doc(root: Path, doc_type: DocType, title: str, description: str = "") -> NewDoc:
    """Write a docs/ page of ``doc_type`` and add it to docs/README.md.

    Parameters
    ----------
    root : Path
        The repository root, holding docs/README.md from ``kmctl init``.
    doc_type : DocType
        The Diataxis type, which picks the folder and the skeleton.
    title : str
        The page title; its kebab-case form names the file.
    description : str
        An optional line for the index entry.

    Returns
    -------
    NewDoc
        The page's path from the repository root, and whether its folder was created.

    Raises
    ------
    ConceptError
        When docs/README.md is missing or the page already exists. Nothing is written.
    """
    title = one_line(title)
    index = root / "docs" / "README.md"
    if not index.is_file():
        raise ConceptError(f"{index} does not exist; run kmctl init first")
    folder = root / "docs" / FOLDERS[doc_type]
    page = folder / f"{slug(title)}.md"
    if page.exists():
        raise ConceptError(
            f"{page.relative_to(root)} already exists; pick another title"
        )
    created_folder = not folder.is_dir()
    folder.mkdir(exist_ok=True)
    body = "\n\n".join(f"## {h}" for h in skeleton(doc_type))
    page.write_text(f"# {title}\n\n{body}\n", encoding="utf-8")
    rel = page.relative_to(root / "docs").as_posix()
    entry = f"- [{link_text(title)}]({rel})" + (
        f": {one_line(description)}" if description.strip() else ""
    )
    text = index.read_text(encoding="utf-8")
    index.write_text(text.rstrip("\n") + "\n" + entry + "\n", encoding="utf-8")
    return NewDoc(path=page.relative_to(root).as_posix(), created_folder=created_folder)
