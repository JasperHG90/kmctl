"""List the live handoffs in .okf/handoffs/, newest first."""

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from kmctl.okf import BadFrontMatter, as_datetime, field, front_matter, has_passed

_OLDEST = datetime.min.replace(tzinfo=UTC)


@dataclass(frozen=True)
class Handoff:
    """One live handoff, with what /continue needs to offer and load it."""

    id: str
    path: str
    title: str
    description: str
    date: str


def live_handoffs(
    root: Path, now: datetime | None = None, warnings: list[str] | None = None
) -> list[Handoff]:
    """The handoffs whose stale_after has not passed, newest first by generated.at.

    Parameters
    ----------
    root : Path
        The repository root, holding .okf/.
    now : datetime | None
        The time to compare stale_after with; the current UTC time when omitted.
    warnings : list[str] | None
        When given, a line is appended for each handoff skipped because its
        front matter cannot be read, so one bad file never hides the others.

    Returns
    -------
    list[Handoff]
        Live handoffs, newest first; ties on generated.at are ordered by file name.
    """
    folder = root / ".okf" / "handoffs"
    if not folder.is_dir():
        return []
    now = now or datetime.now(UTC)
    found = []
    for path in sorted(folder.glob("*.md")):
        if path.name == "index.md":
            continue
        try:
            meta = front_matter(path)
        except BadFrontMatter as error:
            if warnings is not None:
                warnings.append(f"skipped {error}; fix its front matter")
            continue
        if has_passed(field(meta, "stale_after"), now):
            continue
        at = field(meta, "generated.at")
        title = str(field(meta, "title", path.stem))
        description = str(field(meta, "description", ""))
        found.append((as_datetime(at) or _OLDEST, path, title, description, at))
    found.sort(key=lambda item: item[1].name)
    found.sort(key=lambda item: item[0], reverse=True)
    return [
        Handoff(
            id=path.relative_to(root / ".okf").with_suffix("").as_posix(),
            path=path.relative_to(root).as_posix(),
            title=title,
            description=description,
            date=_date_text(at),
        )
        for _, path, title, description, at in found
    ]


def _date_text(at: object) -> str:
    when = as_datetime(at)
    if when is None:
        return ""
    return when.strftime("%Y-%m-%dT%H:%M:%SZ")
