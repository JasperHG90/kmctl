"""Read OKF concepts: front matter, the one rule for when a stale_after date has passed, and where a source points."""

from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import yaml


class BadFrontMatter(Exception):
    """A concept whose front matter is not readable YAML, or not UTF-8 text."""


def front_matter(path: Path) -> dict[str, Any]:
    """The YAML front matter of the concept at ``path``, or an empty dict when it has none.

    Raises
    ------
    BadFrontMatter
        When the file is not UTF-8 or its front matter does not parse.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise BadFrontMatter(f"{path}: not UTF-8 text") from error
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    try:
        data = yaml.safe_load(text[4:end])
    except yaml.YAMLError as error:
        raise BadFrontMatter(
            f"{path}: front matter does not parse ({error.__class__.__name__})"
        ) from error
    return data if isinstance(data, dict) else {}


#: The front matter keys kmctl writes or reads (invariant I4), with where each comes
#: from. Nested keys are paths: ``a.b`` for a mapping, ``a[].b`` for a list of them.
ALLOWED_FIELDS: dict[str, str] = {
    "okf_version": "OKF v0.2 sections 8 and 12, bundle root index",
    "type": "OKF v0.2 section 4.1, required",
    "title": "OKF v0.2 section 4.1",
    "description": "OKF v0.2 section 4.1",
    "tags": "OKF v0.2 section 4.1",
    "generated": "OKF v0.2 section 5.2",
    "generated.by": "OKF v0.2 section 5.2",
    "generated.at": "OKF v0.2 section 5.2",
    "verified": "OKF v0.2 section 5.2",
    "verified[].by": "OKF v0.2 section 5.2",
    "verified[].at": "OKF v0.2 section 5.2",
    "sources": "OKF v0.2 section 5.1",
    "sources[].id": "OKF v0.2 section 5.1",
    "sources[].resource": "OKF v0.2 section 5.1",
    "status": "OKF v0.2 section 5.4",
    "stale_after": "OKF v0.2 section 5.5",
    "handoff_key": "kmctl extension, ADR 0009",
}

#: List fields whose items may be plain strings (the resource itself) instead of mappings.
_STRING_ITEMS = {"sources"}
#: List fields that may also be written as one mapping instead of a list of them.
_SINGLE_MAPPING = {"verified"}


def field(meta: dict[str, Any], path: str, default: Any = None) -> Any:
    """Read one front matter key by its allowed path; the only way kmctl reads front matter.

    ``a`` reads a key, ``a.b`` a key of a mapping, and ``a[].b`` returns a list with
    ``b`` of each item; ``verified`` may also be one mapping, and in ``sources``
    a plain string item is its own resource. Any other non-list reads as ``[]``. Missing values give ``default`` (or
    ``[]`` for a list path).

    Raises
    ------
    KeyError
        When ``path`` is not in ``ALLOWED_FIELDS`` (invariant I4).
    """
    if path not in ALLOWED_FIELDS:
        raise KeyError(
            f"{path!r} is not an allowed OKF field; add it to ALLOWED_FIELDS with an ADR"
        )
    if "[]." in path:
        head, sub = path.split("[].", 1)
        value = meta.get(head)
        if isinstance(value, list):
            items = value
        elif isinstance(value, dict) and head in _SINGLE_MAPPING:
            items = [value]
        else:
            items = []  # a malformed value reads as nothing, as before
        out = []
        for item in items:
            if isinstance(item, dict) and item.get(sub) is not None:
                out.append(item[sub])
            elif isinstance(item, str) and head in _STRING_ITEMS:
                out.append(item)
        return out
    if "." in path:
        head, sub = path.split(".", 1)
        value = meta.get(head)
        return value.get(sub, default) if isinstance(value, dict) else default
    return meta.get(path, default)


def as_datetime(value: object) -> datetime | None:
    """A front matter date or datetime as an aware UTC datetime; a bare date is its midnight."""
    if isinstance(value, datetime):
        try:
            return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
        except OverflowError:
            return None  # a timestamp at the edge of the range has no UTC value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=UTC)
    if isinstance(value, str):
        try:
            return as_datetime(datetime.fromisoformat(value))
        except ValueError:
            return None
    return None


def has_passed(stale_after: object, now: datetime) -> bool:
    """True when ``now`` is at or after ``stale_after`` (OKF §5.5). A missing or unreadable value never passes.

    review-due and handoffs-list both use this, so a handoff is always in
    exactly one of their lists.
    """
    when = as_datetime(stale_after)
    return when is not None and now >= when


def source_candidates(root: Path, okf: Path, concept: Path, resource: str) -> list[str]:
    """The repository-relative paths a source may name, in OKF §6.2 lookup order.

    A leading ``/`` makes ``resource`` bundle-relative. Otherwise it is tried
    from the concept's folder, then the bundle root (a concept id), then the
    repository root. Each place is tried as given and with ``.md`` added. Paths
    outside ``root``, and ``root`` itself, are left out. Callers pick the first
    candidate that exists in the sense they need: on disk, or tracked by git.
    """
    if resource.startswith("/"):
        places = [okf / resource.lstrip("/")]
    else:
        places = [concept.parent / resource, okf / resource, root / resource]
    found = []
    for place in places:
        for path in (place, place.with_name(place.name + ".md")):
            try:
                rel = path.resolve().relative_to(root.resolve()).as_posix()
            except ValueError:
                continue
            if rel != ".":
                found.append(rel)
    return found
