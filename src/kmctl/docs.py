"""Create one docs/ page in its Diataxis folder, with a skeleton, front matter and its folder index entry."""

import json
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from kmctl.checks import links_folder
from kmctl.concepts import ConceptError, one_line, slug, stale_after_time
from kmctl.docs_index import FOLDER_TITLES, GENERATED, folder_index, is_generated
from kmctl.kinds import skeleton

__all__ = ["GENERATED", "DocType", "NewDoc", "new_doc"]

DocType = Literal["tutorial", "how-to", "reference", "explanation"]

FOLDERS: dict[str, str] = {
    "tutorial": "tutorials",
    "how-to": "how-to",
    "reference": "reference",
    "explanation": "explanation",
}

#: How far ahead ``kmctl new doc`` sets a page's stale_after.
STALE_AFTER = "3m"


@dataclass(frozen=True)
class NewDoc:
    """What ``new_doc`` wrote, and what it left for the user to finish."""

    path: str
    created_folder: bool
    warnings: list[str] = dataclass_field(default_factory=list)


def new_doc(
    root: Path,
    doc_type: DocType,
    title: str,
    description: str = "",
    now: datetime | None = None,
) -> NewDoc:
    """Write a docs/ page of ``doc_type`` and list it in its folder's index.

    The page gets front matter: ``description`` when given, ``stale_after``
    ``STALE_AFTER`` ahead and an empty ``sources``; never ``verified``. Its
    folder's generated README.md is written again, and docs/README.md gets a
    link to the folder when it has none.

    Parameters
    ----------
    root : Path
        The repository root, holding docs/README.md from ``kmctl init``.
    doc_type : DocType
        The Diataxis type, which picks the folder and the skeleton.
    title : str
        The page title; its kebab-case form names the file.
    description : str
        An optional line for the front matter and the index entry.
    now : datetime | None
        The time stale_after counts from; the current UTC time when omitted.

    Returns
    -------
    NewDoc
        The page's path from the repository root, whether its folder was
        created, and a warning when the folder's index is hand-written.

    Raises
    ------
    ConceptError
        When docs/README.md is missing or the page already exists. Nothing is written.
    """
    title = one_line(title)
    now = now or datetime.now(UTC)
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
    front = ["---"]
    if description.strip():
        front.append(f"description: {json.dumps(one_line(description))}")
    stale = stale_after_time(STALE_AFTER, now).date().isoformat()
    front += [f"stale_after: {stale}", "sources: []", "---", ""]
    body = "\n\n".join(f"## {h}" for h in skeleton(doc_type))
    page.write_text("\n".join(front) + f"\n# {title}\n\n{body}\n", encoding="utf-8")
    warnings = []
    folder_readme = folder / "README.md"
    if folder_readme.exists() and not is_generated(folder_readme):
        warnings.append(
            f"{folder_readme.relative_to(root).as_posix()} is hand-written, so kmctl "
            "did not list the page there; add its entry by hand"
        )
    else:
        folder_readme.write_text(folder_index(folder), encoding="utf-8")
    if not links_folder(index, folder):
        entry = f"- [{FOLDER_TITLES[folder.name]}]({folder.name}/README.md)"
        text = index.read_text(encoding="utf-8")
        index.write_text(text.rstrip("\n") + "\n" + entry + "\n", encoding="utf-8")
    return NewDoc(
        path=page.relative_to(root).as_posix(),
        created_folder=created_folder,
        warnings=warnings,
    )
