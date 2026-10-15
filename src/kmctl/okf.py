"""Read OKF concepts: front matter, and the one rule for when a stale_after date has passed."""

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
