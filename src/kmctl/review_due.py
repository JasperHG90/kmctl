"""Which concepts in .okf/ and pages in docs/ are due for review, and why (ADR 0006, ADR 0022, ADR 0032).

A concept is due when its ``stale_after`` has passed, when it has no
``verified`` entry, when a tracked file in its ``sources`` changed in a
commit after its verification commit (``source changed``), or when the
concept itself did, outside ``verified`` and ``stale_after``, the fields
``kmctl verify`` writes (``edited after verification``). Commit order, not
dates, decides (ADR 0032): the verification commit is the oldest commit in
the file's history whose front matter holds its newest ``verified[].at``, so
a squash or rebase merge carries it along. While that entry is not
committed, nothing counts as changed after it. Handoffs are short-lived notes, never verified,
so they are left out of those checks and listed only once expired. The
bundle summary, ``.okf/summary.md``, is never verified either: it is due
only when concepts changed after it (``kmctl.summary``, ADR 0027), with the
reason ``concepts changed: ID, ...``.

A docs/ page is due when its ``stale_after`` has passed, or by the same two
history rules as a concept. A page without ``verified`` is not due for that
alone, and its sources are compared with the page's own last commit. Its id is its path without ``.md``, such as
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
    split_front_matter,
    without,
)
from kmctl.summary import SUMMARY_ID, changed_concepts
from kmctl.summary import reason as summary_reason

RESERVED = {"index.md", "log.md"}
#: The front matter fields ``kmctl verify`` writes, which an edit after verification ignores.
VERIFY_FIELDS = {"verified", "stale_after"}


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

    ``history_skipped`` says why the reasons that need git history, source
    changed and edited after verification, were not checked (a shallow
    clone, or no git repository), or is None when they were.
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

    A folder counts when git tracks a file under it; ``git diff -- folder``
    then sees a change to any file under it.
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


@dataclass
class _Check:
    """A concept or docs page whose git history decides some of its reasons.

    ``newest`` is its newest ``verified`` time in the working tree, or None for
    a docs page without one, which is checked against its own last commit.
    ``sources`` pairs each source as written with the tracked path it names.
    Reasons are added to ``reasons``, the list its ``Due`` entry holds.
    """

    rel: str
    newest: datetime | None
    sources: list[tuple[str, str]]
    reasons: list[str]


def _parsed(text: str) -> tuple[dict[str, object], str] | None:
    """A file's front matter and the text after it, or None when it does not parse."""
    try:
        return split_front_matter(text)
    except BadFrontMatter:
        return None


def _verified_at(text: str) -> list[datetime | None]:
    """The ``verified[].at`` times in a file's ``text``; none when its front matter does not parse."""
    parsed = _parsed(text)
    return [as_datetime(d) for d in field(parsed[0], "verified[].at")] if parsed else []


def _outside_verify(text: str | None) -> tuple[object, str] | None:
    """``text`` without the fields kmctl verify writes, to compare two versions by."""
    if text is None:
        return None
    parsed = _parsed(text)
    if parsed is None:
        return None, text
    return without(parsed[0], VERIFY_FIELDS), parsed[1]


def _show(root: Path, specs: list[str]) -> list[str | None]:
    """The text of each ``REV:./PATH`` in ``specs`` from one ``git cat-file --batch``; None when missing."""
    if not specs:
        return []
    proc = subprocess.run(
        ["git", "-C", str(root), "cat-file", "--batch"],
        input="".join(spec + "\n" for spec in specs).encode(),
        capture_output=True,
        check=False,
    )
    data, out, i = proc.stdout, [], 0
    for _ in specs:
        nl = data.find(b"\n", i)
        header = data[i:nl]
        i = nl + 1
        # "SPEC missing" (or "SPEC ambiguous") echoes the spec, which may hold
        # spaces, so it is told apart by its end, not by counting fields.
        if nl == -1 or header.endswith((b" missing", b" ambiguous")):
            out.append(None)
            continue
        size = int(header.split()[2])
        out.append(data[i : i + size].decode("utf-8", errors="replace"))
        i += size + 1
    return out


def _history(root: Path, rels: list[str]) -> dict[str, list[str]]:
    """The commits that changed each of ``rels``, newest first, from one ``git log``.

    ``--cc`` lists a merge for a file that differs from every parent, as a
    ``git log`` of that file alone does. One walk can still follow a
    different side of a merge than that file's own log would, when the same
    change reached both sides (a cherry-pick); both sides then hold the
    entry (ADR 0032).
    """
    listed = _git(
        root,
        *("log", "--cc", "--name-only", "-z", "--relative", "--format=@%H", "--"),
        *rels,
    )
    history: dict[str, list[str]] = {rel: [] for rel in rels}
    commit = ""
    for item in (listed or "").split("\0"):
        item = item.lstrip("\n")
        if item in history:
            history[item].append(commit)
        elif item.startswith("@"):
            commit = item[1:]
    return history


def verification_commits(root: Path, newest: dict[str, datetime]) -> dict[str, str]:
    """The verification commit of each file in ``newest``, by one history walk for all of them.

    Parameters
    ----------
    root : Path
        The repository root.
    newest : dict[str, datetime]
        Each file's path from ``root``, with its newest ``verified`` time in
        the working tree.

    Returns
    -------
    dict[str, str]
        For each file whose newest entry is committed, the oldest commit in
        its history whose front matter holds that time. A file whose entry
        is not committed yet is left out.
    """
    history = _history(root, list(newest)) if newest else {}
    specs = [(rel, commit) for rel, commits in history.items() for commit in commits]
    texts = _show(root, [f"{commit}:./{rel}" for rel, commit in specs])
    found = {}
    # The log is newest first, so the last commit that holds the entry is the oldest.
    for (rel, commit), text in zip(specs, texts, strict=True):
        if text is not None and newest[rel] in _verified_at(text):
            found[rel] = commit
    return found


def _changed(root: Path, base: str, source: str) -> bool:
    """True when ``source`` differs between commit ``base`` and HEAD."""
    proc = subprocess.run(
        ["git", "-C", str(root), "diff", "--quiet", base, "HEAD", "--", source],
        capture_output=True,
        check=False,
    )
    return proc.returncode == 1


def _check_history(root: Path, checks: list[_Check]) -> None:
    """Add ``source changed`` and ``edited after verification`` reasons, by commit order.

    The baseline is the file's verification commit or, for a docs page
    without ``verified``, its own last commit. A source is changed when it
    differs between the baseline and HEAD. A verified file is edited when it
    differs between its verification commit and HEAD outside the fields
    kmctl verify writes. A file with no baseline gets neither reason.
    """
    commits = verification_commits(
        root, {c.rel: c.newest for c in checks if c.newest is not None}
    )
    edits = [c for c in checks if c.rel in commits]
    texts = _show(
        root,
        [
            spec
            for c in edits
            for spec in (f"{commits[c.rel]}:./{c.rel}", f"HEAD:./{c.rel}")
        ],
    )
    edited = {
        c.rel
        for c, verified, head in zip(edits, texts[::2], texts[1::2], strict=True)
        if _outside_verify(verified) != _outside_verify(head)
    }
    for c in checks:
        if c.newest is not None:
            base = commits.get(c.rel)
        else:
            base = _git(root, "log", "-1", "--format=%H", "--", c.rel) or None
        if base is None:
            continue
        for resource, source in c.sources:
            if _changed(root, base, source):
                c.reasons.append(f"source changed: {resource}")
        if c.rel in edited:
            c.reasons.append("edited after verification")


def _docs_due(
    root: Path,
    docs: Path,
    now: datetime,
    tracked: set[str],
    result: ReviewDue,
    checks: list[_Check],
) -> list[Due]:
    """Each docs/ page with the reasons known so far, by the rules in the module docstring.

    A page whose history decides more reasons is added to ``checks``. A
    source resolves from the page's folder, then the repository root; a
    leading ``/`` is from the repository root.
    """
    entries = []
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
        entry = Due(pid, rel, [])
        entries.append(entry)
        if has_passed(field(meta, "stale_after"), now):
            entry.reasons.append("stale_after passed")
        if result.history_skipped is not None:
            continue
        newest = _last_verified(field(meta, "verified[].at"))
        sources = []
        for resource in _sources(field(meta, "sources[].resource")):
            if "://" in resource:
                continue
            source = _resolve(root, root, path, resource, tracked)
            if source is None:
                result.notices.append(Notice(pid, rel, resource, "source not resolved"))
                continue
            sources.append((resource, source))
        if newest is not None or sources:
            checks.append(_Check(rel, newest, sources, entry.reasons))
    return entries


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
    checks: list[_Check] = []
    entries = (
        _docs_due(root, docs, now, tracked, result, checks) if docs.is_dir() else []
    )
    for path in _concepts(okf) if okf.is_dir() else []:
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
                entries.append(Due(cid, rel, [summary_reason(changed)]))
            continue
        entry = Due(cid, rel, [])
        entries.append(entry)
        if has_passed(field(meta, "stale_after"), now):
            entry.reasons.append("stale_after passed")
        verified_at = _last_verified(field(meta, "verified[].at"))
        if verified_at is None:
            entry.reasons.append("unverified")
        if result.history_skipped is not None:
            continue
        sources = []
        for resource in _sources(field(meta, "sources[].resource")):
            if "://" in resource:
                continue
            source = _resolve(root, okf, path, resource, tracked)
            if source is None:
                result.notices.append(Notice(cid, rel, resource, "source not resolved"))
                continue
            sources.append((resource, source))
        if verified_at is not None:
            checks.append(_Check(rel, verified_at, sources, entry.reasons))
    _check_history(root, checks)
    result.due = [d for d in entries if d.reasons]
    return result
