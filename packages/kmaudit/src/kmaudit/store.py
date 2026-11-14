"""The audit stores: one git-ignored SQLite file per namespace under .kmaudit/ in the repository.

Its schema moves by the ordered SQL steps in ``STEPS``, tracked in ``PRAGMA
user_version``, so later tickets add tables by appending a step. WAL mode and
a busy timeout let parallel agents submit at once.
"""

import json
import os
import sqlite3
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from typing import Self

from kmaudit import namespaces
from kmaudit.models import Claim
from kmaudit.sections import Section, previous_keys

BUSY_TIMEOUT_MS = 30_000

#: The schema steps, in order; step i brings a database to user_version i + 1.
STEPS: list[str] = [
    """
    CREATE TABLE sections (
        id TEXT PRIMARY KEY,
        concept TEXT NOT NULL,
        key TEXT NOT NULL,
        title TEXT NOT NULL,
        section TEXT NOT NULL,
        sentences TEXT NOT NULL,
        earlier_ids TEXT NOT NULL
    );
    CREATE INDEX sections_concept ON sections (concept);
    CREATE TABLE extractions (
        section_id TEXT PRIMARY KEY REFERENCES sections (id) ON DELETE CASCADE,
        key TEXT NOT NULL,
        submitted_by TEXT NOT NULL,
        submitted_at TEXT NOT NULL
    );
    CREATE TABLE verdicts (
        section_id TEXT NOT NULL REFERENCES sections (id) ON DELETE CASCADE,
        n INTEGER NOT NULL,
        kind TEXT NOT NULL,
        how_to_check TEXT NOT NULL,
        reason TEXT NOT NULL,
        PRIMARY KEY (section_id, n)
    );
    CREATE TABLE claims (
        id TEXT NOT NULL,
        section_id TEXT NOT NULL REFERENCES sections (id) ON DELETE CASCADE,
        concept TEXT NOT NULL,
        n INTEGER NOT NULL,
        kind TEXT NOT NULL,
        claim TEXT NOT NULL,
        quantifier TEXT NOT NULL,
        how_to_check TEXT NOT NULL,
        reason TEXT NOT NULL,
        refers_to TEXT NOT NULL,
        PRIMARY KEY (section_id, id)
    );
    CREATE INDEX claims_id ON claims (id);
    """,
    # agent-audit-checks: a check or a reason per claim, the files it read,
    # its last run and its mutation score, and a cache of the CLI help walk.
    """
    CREATE TABLE checks (
        claim_id TEXT PRIMARY KEY,
        kind TEXT NOT NULL,
        steps TEXT NOT NULL,
        strength TEXT NOT NULL,
        why TEXT NOT NULL,
        drift TEXT,
        reason TEXT NOT NULL,
        submitted_by TEXT NOT NULL,
        submitted_at TEXT NOT NULL
    );
    CREATE TABLE check_reads (
        claim_id TEXT NOT NULL REFERENCES checks (claim_id) ON DELETE CASCADE,
        path TEXT NOT NULL,
        sha TEXT NOT NULL,
        PRIMARY KEY (claim_id, path)
    );
    CREATE TABLE check_runs (
        claim_id TEXT PRIMARY KEY REFERENCES checks (claim_id) ON DELETE CASCADE,
        reads_key TEXT NOT NULL,
        holds INTEGER NOT NULL,
        skipped INTEGER NOT NULL,
        results TEXT NOT NULL,
        ran_at TEXT NOT NULL
    );
    CREATE TABLE check_quality (
        claim_id TEXT PRIMARY KEY REFERENCES checks (claim_id) ON DELETE CASCADE,
        key TEXT NOT NULL,
        mutants INTEGER NOT NULL,
        killed INTEGER NOT NULL,
        survived TEXT NOT NULL
    );
    CREATE TABLE cache (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    """,
    # agent-audit-decide: each decision model answer under its asked key.
    """
    CREATE TABLE decisions (
        asked_key TEXT PRIMARY KEY,
        question TEXT NOT NULL,
        subject TEXT NOT NULL,
        model TEXT NOT NULL,
        answers TEXT NOT NULL,
        asked_at TEXT NOT NULL
    );
    """,
    # Each answer's concept and sentence, so an answer can follow its claim
    # when re-extraction rewords it (ADR 0040).
    """
    ALTER TABLE checks ADD COLUMN concept TEXT NOT NULL DEFAULT '';
    ALTER TABLE checks ADD COLUMN section TEXT NOT NULL DEFAULT '';
    ALTER TABLE checks ADD COLUMN sentence TEXT NOT NULL DEFAULT '';
    """,
    # A person's thumbs, note and verdict on a claim or its check, appended
    # so the history stays; answered_at is set once an agent's next answer
    # has taken it in (ADR 0041).
    """
    CREATE TABLE feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        claim_id TEXT NOT NULL,
        target TEXT NOT NULL,
        vote TEXT,
        verdict TEXT,
        note TEXT NOT NULL,
        concept TEXT NOT NULL,
        section TEXT NOT NULL,
        sentence TEXT NOT NULL,
        claim TEXT NOT NULL,
        answer TEXT NOT NULL,
        reads TEXT NOT NULL,
        submitted_by TEXT NOT NULL,
        submitted_at TEXT NOT NULL,
        answered_at TEXT
    );
    CREATE INDEX feedback_claim ON feedback (claim_id, target);
    """,
    # The namespace a store belongs to and the folder it audits (ADR 0043).
    """
    CREATE TABLE meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    """,
]


def _copy(source: Path, target: Path) -> None:
    """Copy the SQLite database at ``source`` to ``target`` with SQLite's backup API, rows in its WAL included.

    ``source`` is opened read-only, so it is not changed. The copy is written
    to a temporary file of its own and linked into place only when
    ``target`` does not exist yet, so processes opening the store at once
    never overwrite one another's copy or a store already in use.
    """
    handle, name = tempfile.mkstemp(dir=target.parent, suffix=".partial")
    os.close(handle)
    partial = Path(name)
    try:
        src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
        try:
            dst = sqlite3.connect(partial)
            try:
                src.backup(dst)
            finally:
                dst.close()
        finally:
            src.close()
        try:
            os.link(partial, target)
        except FileExistsError:
            pass  # another process copied it first; use theirs
    finally:
        partial.unlink(missing_ok=True)


class StaleSection(Exception):
    """A section that is gone, or whose key moved, by the time its answer is saved."""


@dataclass(frozen=True)
class Refresh:
    """What refreshing the store's sections found.

    Attributes
    ----------
    new, changed, removed : list[str]
        Section ids first seen, whose key moved (their claims dropped), and gone (their claims dropped).
    """

    new: list[str]
    changed: list[str]
    removed: list[str]


@dataclass(frozen=True)
class Verdict:
    """A stored sentence verdict, the row behind one sentence of a submitted section."""

    n: int
    kind: str
    how_to_check: str
    reason: str


def _now() -> str:
    """The current UTC time as ISO 8601 seconds."""
    return datetime.now(UTC).isoformat(timespec="seconds")


class Store:
    """The audit store of one namespace, opened at the newest schema step.

    Parameters
    ----------
    root :
        The repository root; the store is ``root/.kmaudit/<namespace>.sqlite``.
        kmaudit creates ``.kmaudit/`` with a ``.gitignore`` holding ``*``, so
        the folder ignores itself and the user's own ``.gitignore`` is never
        edited.
    namespace :
        The audited folder's path below ``root``. The ``.okf`` namespace
        starts as a copy of the store the audit kept while it was part of
        kmctl, ``.kmctl/audit.sqlite``, when there is one; that file is left
        as it was.
    """

    def __init__(
        self, root: Path, namespace: str = namespaces.LEGACY_NAMESPACE
    ) -> None:
        self.path = namespaces.store_file(root, namespace)
        folder = self.path.parent
        folder.mkdir(parents=True, exist_ok=True)
        ignore = folder / ".gitignore"
        if not ignore.exists():
            ignore.write_text("*\n", encoding="utf-8")
        legacy = root / namespaces.LEGACY_STORE
        if (
            namespace == namespaces.LEGACY_NAMESPACE
            and not self.path.exists()
            and legacy.is_file()
        ):
            _copy(legacy, self.path)
        self.db = sqlite3.connect(
            self.path, timeout=BUSY_TIMEOUT_MS / 1000, isolation_level=None
        )
        self.db.row_factory = sqlite3.Row
        self.db.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
        self.db.execute("PRAGMA journal_mode = WAL")
        self.db.execute("PRAGMA foreign_keys = ON")
        self._migrate()
        self.db.execute(
            "INSERT OR IGNORE INTO meta (key, value) VALUES ('namespace', ?)",
            (namespace,),
        )

    def _migrate(self) -> None:
        """Apply every schema step the database has not had yet, each in its own transaction."""
        self.db.execute("BEGIN IMMEDIATE")
        try:
            version = self.db.execute("PRAGMA user_version").fetchone()[0]
            for number, step in enumerate(STEPS[version:], version + 1):
                for statement in step.split(";"):
                    if statement.strip():
                        self.db.execute(statement)
                self.db.execute(f"PRAGMA user_version = {number}")
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    @property
    def version(self) -> int:
        """The schema step the database is at."""
        return int(self.db.execute("PRAGMA user_version").fetchone()[0])

    def __enter__(self) -> Self:
        """Return the open store."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Close the connection."""
        self.db.close()

    def refresh(
        self, sections: Iterable[Section], concepts: set[str] | None
    ) -> Refresh:
        """Bring the stored sections in line with the bundle's, dropping the claims of changed and removed ones.

        Parameters
        ----------
        sections :
            The current sections of the concepts in scope.
        concepts :
            The concept ids in scope, or None for the whole bundle; stored
            sections outside the scope are left alone.
        """
        current = {s.id: s for s in sections}
        new: list[str] = []
        changed: list[str] = []
        self.db.execute("BEGIN IMMEDIATE")
        try:
            stored = {
                row["id"]: (row["key"], row["concept"])
                for row in self.db.execute("SELECT id, key, concept FROM sections")
            }
            removed = [
                sid
                for sid, (_, concept) in stored.items()
                if sid not in current and (concepts is None or concept in concepts)
            ]
            for sid in removed:
                self.db.execute("DELETE FROM sections WHERE id = ?", (sid,))
            for section in current.values():
                row = (
                    section.concept,
                    section.key,
                    section.title,
                    section.section,
                    json.dumps(section.sentences),
                    json.dumps(section.earlier_ids),
                    section.id,
                )
                if section.id not in stored:
                    new.append(section.id)
                    self.db.execute(
                        "INSERT INTO sections (concept, key, title, section, sentences, earlier_ids, id) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        row,
                    )
                elif stored[section.id][0] in previous_keys(section):
                    # Same text and guidance; only the way answers are
                    # submitted changed, so the answer carries over.
                    self.db.execute(
                        "UPDATE extractions SET key = ? WHERE section_id = ? AND key = ?",
                        (section.key, section.id, stored[section.id][0]),
                    )
                    self.db.execute(
                        "UPDATE sections SET key = ? WHERE id = ?",
                        (section.key, section.id),
                    )
                elif stored[section.id][0] != section.key:
                    changed.append(section.id)
                    self._drop_extraction(section.id)
                    self.db.execute(
                        "UPDATE sections SET concept = ?, key = ?, title = ?, section = ?, "
                        "sentences = ?, earlier_ids = ? WHERE id = ?",
                        row,
                    )
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        return Refresh(new=new, changed=changed, removed=removed)

    def _drop_extraction(self, section_id: str) -> None:
        """Delete a section's extraction, verdicts and claims; the caller holds a transaction."""
        for table, column in (
            ("extractions", "section_id"),
            ("verdicts", "section_id"),
            ("claims", "section_id"),
        ):
            self.db.execute(f"DELETE FROM {table} WHERE {column} = ?", (section_id,))

    def extracted(self) -> dict[str, str]:
        """Each extracted section's id, with the key it was extracted at."""
        return {
            row["section_id"]: row["key"]
            for row in self.db.execute("SELECT section_id, key FROM extractions")
        }

    def section(self, section_id: str) -> sqlite3.Row | None:
        """The stored row of one section, or None when the store has no such section."""
        return self.db.execute(
            "SELECT * FROM sections WHERE id = ?", (section_id,)
        ).fetchone()

    def save(
        self,
        section_id: str,
        key: str,
        verdicts: list[Verdict],
        claims: list[Claim],
        by: str,
    ) -> int:
        """Replace one section's extraction with these verdicts and claims, in one transaction.

        Returns
        -------
        int
            The claims stored; two claims of one section with the same text are one.

        Raises
        ------
        StaleSection
            When the section is gone or its key is no longer ``key``, checked
            inside the transaction so a parallel ``todo`` cannot slip between.
        """
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                "SELECT key FROM sections WHERE id = ?", (section_id,)
            ).fetchone()
            if row is None or row["key"] != key:
                raise StaleSection(section_id)
            self._drop_extraction(section_id)
            self.db.execute(
                "INSERT INTO extractions (section_id, key, submitted_by, submitted_at) VALUES (?, ?, ?, ?)",
                (section_id, key, by, _now()),
            )
            self.db.executemany(
                "INSERT INTO verdicts (section_id, n, kind, how_to_check, reason) VALUES (?, ?, ?, ?, ?)",
                [(section_id, v.n, v.kind, v.how_to_check, v.reason) for v in verdicts],
            )
            self.db.executemany(
                "INSERT OR IGNORE INTO claims (id, section_id, concept, n, kind, claim, quantifier, "
                "how_to_check, reason, refers_to) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        c.id,
                        section_id,
                        c.concept,
                        c.n,
                        c.kind,
                        c.claim,
                        c.quantifier,
                        c.how_to_check,
                        c.reason,
                        json.dumps(c.refers_to),
                    )
                    for c in claims
                ],
            )
            stored = self.db.execute(
                "SELECT COUNT(*) FROM claims WHERE section_id = ?", (section_id,)
            ).fetchone()[0]
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        return int(stored)

    def claim(self, claim_id: str) -> Claim | None:
        """The stored claim with this id (its first section when two share it), or None."""
        found = self._claims("WHERE c.id = ?", (claim_id,), one=True)
        return found[0] if found else None

    def claims(self, concepts: set[str] | None = None) -> list[Claim]:
        """The stored claims, in concept, section and sentence order; only ``concepts`` when given."""
        return [
            c for c in self._claims("", ()) if concepts is None or c.concept in concepts
        ]

    def _claims(
        self, where: str, args: tuple[str, ...], one: bool = False
    ) -> list[Claim]:
        """The stored claims matching a SQL ``where`` clause on ``claims c``, in concept, section and sentence order."""
        rows = self.db.execute(
            "SELECT c.*, s.sentences FROM claims c JOIN sections s ON s.id = c.section_id "
            f"{where} ORDER BY c.concept, c.section_id, c.n, c.rowid{' LIMIT 1' if one else ''}",
            args,
        ).fetchall()
        return [
            Claim(
                id=row["id"],
                section=row["section_id"],
                concept=row["concept"],
                n=row["n"],
                sentence=_sentence(row["sentences"], row["n"]),
                kind=row["kind"],
                claim=row["claim"],
                quantifier=row["quantifier"],
                how_to_check=row["how_to_check"],
                reason=row["reason"],
                refers_to=json.loads(row["refers_to"]),
            )
            for row in rows
        ]

    def pending_sections(self) -> set[str]:
        """The stored sections with no extraction at their current key."""
        rows = self.db.execute(
            "SELECT s.id FROM sections s LEFT JOIN extractions e ON e.section_id = s.id "
            "WHERE e.key IS NULL OR e.key != s.key"
        )
        return {row[0] for row in rows}

    def pending(self) -> int:
        """How many stored sections have no extraction at their current key."""
        row = self.db.execute(
            "SELECT COUNT(*) FROM sections s LEFT JOIN extractions e ON e.section_id = s.id "
            "WHERE e.key IS NULL OR e.key != s.key"
        ).fetchone()
        return int(row[0])

    def documents(self) -> dict[str, tuple[int, int]]:
        """Each stored concept mapped to (its sections, those extracted at their current key)."""
        rows = self.db.execute(
            "SELECT s.concept, COUNT(*) AS sections, "
            "SUM(CASE WHEN e.key = s.key THEN 1 ELSE 0 END) AS extracted "
            "FROM sections s LEFT JOIN extractions e ON e.section_id = s.id "
            "GROUP BY s.concept ORDER BY s.concept"
        )
        return {
            row["concept"]: (row["sections"], row["extracted"] or 0) for row in rows
        }


def _sentence(sentences: str, n: int) -> str:
    """Sentence ``n`` of a stored JSON list of sentences, or empty when out of range."""
    items = json.loads(sentences)
    return items[n - 1] if 1 <= n <= len(items) else ""
