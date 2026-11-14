"""``kmaudit briefing``: each namespace's audit state in a few lines, read-only, for a session-start hook.

It never opens a store through ``Store``, whose constructor creates
``.kmaudit/``, copies the old store, migrates and writes. It reads each
store file with SQLite's read-only mode into memory and migrates only that
copy, so a store at any schema step reads like a current one and the file
is not changed; SQLite may still create its ``-wal`` and ``-shm``
sidecars, which hold nothing new. Pending sections come from cutting the pages and
comparing keys, as ``claims todo`` would, without its refresh.
"""

import sqlite3
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from kmaudit import namespaces
from kmaudit.check_verbs import CHECKABLE, status_row
from kmaudit.feedback import is_open, latest
from kmaudit.sections import Target, cut, previous_keys
from kmaudit.steps import Repository
from kmaudit.store import Store

#: The statuses whose claims still want an answer from the check writer.
UNANSWERED = ("no check", "stale reason", "not run")
#: The statuses a person should look at on the review page.
TO_REVIEW = ("drift", "fails", "weak")


@dataclass(frozen=True)
class NamespaceBrief:
    """One namespace's audit state.

    Attributes
    ----------
    namespace : str
        The audited folder's path below the repository root.
    sections : int
        Sections in the store, as ``kmaudit claims list`` counts them.
    pending : int
        Sections of the pages as they are now that ``claims todo`` would hand out.
    claims : int
        Claims in the store.
    checks : dict[str, int]
        Checkable claims per status, as ``kmaudit checks list`` reports them.
    feedback : int
        Open feedback from people, not yet taken in by an agent's answer.
    next : str
        The one thing to do next, or empty when the namespace is up to date.
    """

    namespace: str
    sections: int
    pending: int
    claims: int
    checks: dict[str, int] = field(default_factory=dict)
    feedback: int = 0
    next: str = ""


def _read_only(path: Path) -> Store:
    """A ``Store`` over an in-memory copy of the file at ``path``, migrated to the newest step.

    The file is opened read-only and copied with SQLite's backup API, so a
    store at an older schema step, missing tables or columns the readers
    use, reads like a current one, and the file itself is never written.
    """
    source = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        memory = sqlite3.connect(":memory:", isolation_level=None)
        source.backup(memory)
    finally:
        source.close()
    memory.row_factory = sqlite3.Row
    store = object.__new__(Store)
    store.path = path
    store.db = memory
    store._migrate()
    return store


def _count(store: Store, sql: str) -> int:
    """One count, or 0 when the store's schema step has no such table yet."""
    try:
        return int(store.db.execute(sql).fetchone()[0])
    except sqlite3.OperationalError:
        return 0


def _next(name: str, pending: int, checks: Counter[str], feedback: int) -> str:
    """The one next step for a namespace, most urgent first."""
    if pending:
        return f"/extract-claims {name}: {pending} sections to extract"
    unanswered = sum(checks[s] for s in UNANSWERED)
    if unanswered:
        return f"/write-checks {name}: {unanswered} claims without a current answer"
    review = sum(checks[s] for s in TO_REVIEW)
    if review or feedback:
        return f"kmaudit ui {name}: {review} checks and {feedback} notes to look at"
    return ""


def brief_one(root: Path, name: str, folder: Path) -> NamespaceBrief:
    """The state of one namespace, read without changing any store."""
    path = namespaces.store_file(root, name)
    if not path.is_file():
        path = root / namespaces.LEGACY_STORE
    target = Target(bundle=folder, files=None, root=root)
    store = _read_only(path)
    try:
        extracted = store.extracted()
        pending = sum(
            1
            for s in cut(target)
            if extracted.get(s.id) != s.key
            and extracted.get(s.id) not in previous_keys(s)
        )
        repo = Repository(root, folder)
        checkable = {c.id: c for c in store.claims() if c.kind in CHECKABLE}
        statuses = Counter(
            status_row(store, repo, c).status for c in checkable.values()
        )
        feedback = sum(1 for f in latest(store).values() if is_open(f))
        brief = NamespaceBrief(
            namespace=name,
            sections=_count(store, "SELECT count(*) FROM sections"),
            pending=pending,
            claims=len(store.claims()),
            checks=dict(statuses),
            feedback=feedback,
            next=_next(name, pending, statuses, feedback),
        )
    finally:
        store.db.close()
    return brief


def brief(path: Path) -> list[NamespaceBrief]:
    """Each namespace of the repository holding ``path``, sorted by name."""
    root = namespaces.repository_root(path)
    return [brief_one(root, n, f) for n, f in sorted(namespaces.existing(root).items())]


def render(briefs: list[NamespaceBrief]) -> str:
    """The briefing as a few plain lines per namespace; empty when there is none."""
    lines: list[str] = []
    for b in briefs:
        checks = ", ".join(f"{n} {s}" for s, n in sorted(b.checks.items()))
        lines.append(
            f"kmaudit {b.namespace}: {b.sections} sections ({b.pending} pending), "
            f"{b.claims} claims, {b.feedback} open notes"
        )
        if checks:
            lines.append(f"  checks: {checks}")
        if b.next:
            lines.append(f"  Next: {b.next}")
    return "\n".join(lines)
