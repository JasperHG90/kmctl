"""Which concepts in .okf/ and pages in docs/ are due for review, and why (ADR 0006, ADR 0022).

A concept is due when its ``stale_after`` has passed, when it has no
``verified`` entry, or when a tracked file in its ``sources`` changed in git
after its last verified date. Handoffs are short-lived notes, never verified,
so they are left out of those checks and listed only once expired. The
bundle summary, ``.okf/summary.md``, is never verified either: it is due
only when concepts changed after it (``kmctl.summary``, ADR 0027), with the
reason ``concepts changed: ID, ...``.

A docs/ page is due when its ``stale_after`` has passed, or when a tracked
file in its ``sources`` changed after its last verified date or, with none,
after the page's own last commit. A docs page without ``verified`` is not due
for that alone. Its id is its path without ``.md``, such as
``docs/how-to/install``, so it cannot clash with a concept id. README.md
files in docs/ are indexes and are left out.
"""

import dataclasses
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from kmctl.okf import (
    BadFrontMatter,
    as_datetime,
    field,
    front_matter,
    has_passed,
    source_candidates,
)
from kmctl.summary import SUMMARY_ID, changed_concepts
from kmctl.summary import reason as summary_reason

RESERVED = {"index.md", "log.md"}


@dataclass(frozen=True)
class Due:
    """A concept due for review, with every reason that applies."""

    id: str
    path: str
    reasons: list[str]


@dataclass(frozen=True)
class Notice:
    """Something kmctl could not check, which is not by itself a reason to review."""

    id: str
    path: str
    resource: str
    message: str


@dataclass(frozen=True)
class ExpiredHandoff:
    """A handoff whose stale_after has passed."""

    id: str
    path: str
    title: str


@dataclass
class ReviewDue:
    """The result of ``review_due``: what is due, what could not be checked, expired handoffs.

    ``history_skipped`` says why the source-changed reason was not checked
    (a shallow clone, or no git repository), or is None when it was.
    """

    due: list[Due] = dataclasses.field(default_factory=list)
    notices: list[Notice] = dataclasses.field(default_factory=list)
    expired_handoffs: list[ExpiredHandoff] = dataclasses.field(default_factory=list)
    history_skipped: str | None = None


def _git(root: Path, *args: str) -> str | None:
    proc = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
    )
    return proc.stdout.strip() if proc.returncode == 0 else None


def _history_skipped(root: Path) -> str | None:
    shallow = _git(root, "rev-parse", "--is-shallow-repository")
    if shallow is None:
        return "not a git repository, so source history was not checked"
    if shallow == "true":
        return "shallow clone, so source history was not checked; fetch full history"
    return None


def _concepts(okf: Path) -> list[Path]:
    found = []
    for path in sorted(okf.rglob("*.md")):
        parts = path.relative_to(okf).parts
        if path.name in RESERVED or any(p.startswith(".") for p in parts):
            continue
        if parts[0] == "prototypes" and (len(parts) != 3 or path.name != "README.md"):
            continue
        found.append(path)
    return found


def _resolve(
    root: Path, okf: Path, concept: Path, resource: str, tracked: set[str]
) -> str | None:
    """The tracked file or folder a source names, by OKF §6.2, or None.

    A folder counts when git tracks a file under it; ``git log -- folder``
    then gives its last change.
    """
    for rel in source_candidates(root, okf, concept, resource):
        if rel in tracked or any(t.startswith(rel + "/") for t in tracked):
            return rel
    return None


def _last_verified(dates: list[object]) -> datetime | None:
    parsed = [as_datetime(d) for d in dates]
    found = [d for d in parsed if d is not None]
    return max(found) if found else None


def _sources(resources: list[object]) -> list[str]:
    return [r.strip() for r in resources if isinstance(r, str) and r.strip()]


def _docs_pages(docs: Path) -> list[Path]:
    return sorted(
        p
        for p in docs.rglob("*.md")
        if p.name != "README.md"
        and not any(part.startswith(".") for part in p.relative_to(docs).parts)
    )


def _docs_due(
    root: Path, docs: Path, now: datetime, tracked: set[str], result: ReviewDue
) -> None:
    """Add each docs/ page that is due to ``result``, by the rules in the module docstring.

    A source resolves from the page's folder, then the repository root; a
    leading ``/`` is from the repository root.
    """
    for path in _docs_pages(docs):
        rel = path.relative_to(root).as_posix()
        pid = path.relative_to(root).with_suffix("").as_posix()
        try:
            meta = front_matter(path)
        except BadFrontMatter as error:
            result.notices.append(
                Notice(pid, rel, "", f"front matter unreadable: {error}")
            )
            continue
        reasons = []
        if has_passed(field(meta, "stale_after"), now):
            reasons.append("stale_after passed")
        resources = [
            r for r in _sources(field(meta, "sources[].resource")) if "://" not in r
        ]
        if resources and result.history_skipped is None:
            baseline = _last_verified(field(meta, "verified[].at")) or as_datetime(
                _git(root, "log", "-1", "--format=%cI", "--", rel)
            )
            for resource in resources:
                source = _resolve(root, root, path, resource, tracked)
                if source is None:
                    result.notices.append(
                        Notice(pid, rel, resource, "source not resolved")
                    )
                    continue
                changed = as_datetime(
                    _git(root, "log", "-1", "--format=%cI", "--", source)
                )
                if baseline is not None and changed is not None and changed > baseline:
                    reasons.append(f"source changed: {resource}")
        if reasons:
            result.due.append(Due(pid, rel, reasons))


def review_due(root: Path, now: datetime | None = None) -> ReviewDue:
    """List what in ``root``'s .okf/ bundle and docs/ pages is due for review.

    Parameters
    ----------
    root : Path
        The repository root, holding .okf/.
    now : datetime | None
        The time to compare stale_after with; the current UTC time when omitted.

    Returns
    -------
    ReviewDue
        Due concepts with their reasons, notices, expired handoffs, and why
        the history check was skipped, if it was.
    """
    result = ReviewDue()
    okf = root / ".okf"
    docs = root / "docs"
    if not okf.is_dir() and not docs.is_dir():
        return result
    now = now or datetime.now(UTC)
    result.history_skipped = _history_skipped(root)
    # -z keeps paths unquoted, so non-ASCII names match.
    listed = _git(root, "ls-files", "-z") if result.history_skipped is None else None
    tracked = set(filter(None, listed.split("\0"))) if listed else set()
    if docs.is_dir():
        _docs_due(root, docs, now, tracked, result)
    if not okf.is_dir():
        return result
    for path in _concepts(okf):
        cid = path.relative_to(okf).with_suffix("").as_posix()
        rel = path.relative_to(root).as_posix()
        try:
            meta = front_matter(path)
        except BadFrontMatter as error:
            result.notices.append(
                Notice(cid, rel, "", f"front matter unreadable: {error}")
            )
            continue
        if cid.startswith("handoffs/"):
            if has_passed(field(meta, "stale_after"), now):
                result.expired_handoffs.append(
                    ExpiredHandoff(cid, rel, str(field(meta, "title", cid)))
                )
            continue
        if cid == SUMMARY_ID:
            changed = changed_concepts(root)
            if changed:
                result.due.append(Due(cid, rel, [summary_reason(changed)]))
            continue
        reasons = []
        if has_passed(field(meta, "stale_after"), now):
            reasons.append("stale_after passed")
        verified_at = _last_verified(field(meta, "verified[].at"))
        if verified_at is None:
            reasons.append("unverified")
        for resource in _sources(field(meta, "sources[].resource")):
            if "://" in resource:
                continue
            if result.history_skipped is not None:
                continue
            source = _resolve(root, okf, path, resource, tracked)
            if source is None:
                result.notices.append(Notice(cid, rel, resource, "source not resolved"))
                continue
            changed = as_datetime(_git(root, "log", "-1", "--format=%cI", "--", source))
            if (
                verified_at is not None
                and changed is not None
                and changed > verified_at
            ):
                reasons.append(f"source changed: {resource}")
        if reasons:
            result.due.append(Due(cid, rel, reasons))
    return result
