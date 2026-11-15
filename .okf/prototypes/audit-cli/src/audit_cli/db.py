"""The project's SQLite database: one file per project, shared by every stage of the audit.

Each stage owns its tables. The schema grows by Alembic revisions in
``migrations/versions/``; opening a database upgrades it to the newest, and
the ``alembic_version`` table records where it stands, so a revision never
runs twice.
"""

import datetime as dt
import json
import pathlib as plb
import sqlite3
from collections.abc import Callable, Iterable
from types import TracebackType
from typing import Any, Literal, Self

import alembic.command
import alembic.config
import sqlalchemy
from pydantic import BaseModel, Field
from sqlalchemy.pool import StaticPool

from audit_cli.claims.models import ChunkResult, Claim, CorrectionLink, SentenceNote, TokenCounts
from audit_cli.processing.chunker import Chunk

MIGRATIONS = plb.Path(__file__).parent / "migrations"  # Alembic revisions, one file per schema change


class FileRow(BaseModel):
    """One file as the database stores it."""

    path: str = Field(description="The path relative to the repository root.")
    sha256: str
    size: int
    lang: str
    description: str
    is_text: bool
    score: float


class StoredClaim(BaseModel):
    """One merged claim with the chunk and sentence it came from."""

    chunk_id: str
    position: int = Field(description="The claim's order within its chunk.")
    claim_id: str
    concept: str
    sentence_n: int
    sentence: str
    claim_type: str
    claim: str
    how_to_check: str
    quantifier: str
    refers_to: list[str]
    run: str
    reason: str = Field(default="", description="The model's reason for the claim's kind.")


class StoredCheck(BaseModel):
    """One claim's check, reason or settled verdict, with the files it read and their content hashes."""

    claim_id: str
    kind: Literal["check", "reason", "settled"]
    steps: list[dict[str, Any]] = Field(default_factory=list, description="The check's steps, as written.")
    strength: str | None = Field(default=None, description="exact or proxy, for a check.")
    why: str = Field(default="", description="Why the steps test the claim, or why no step can.")
    settled: bool | None = Field(default=None, description="The verdict, for a claim settled with no model.")
    writer: str = Field(description="What wrote it: settle, twocall:<model> or agent:<model>.")
    prompt_hash: str = ""
    expectation_changed: bool = Field(
        default=False, description="The fix call changed what the check expects: a person should look."
    )
    tokens: int = Field(default=0, description="Its share of the tokens of the calls that wrote it.")
    commit_sha: str = Field(default="", description="The commit it was written at.")
    reads: dict[str, str] = Field(default_factory=dict, description="Each file it read, with its content hash.")


class CheckResult(BaseModel):
    """A check's last run."""

    claim_id: str
    holds: bool
    results: list[dict[str, Any]] = Field(description="What each step saw.")
    reads_key: str = Field(description="A hash of the files and content hashes it ran against.")
    commit_sha: str = ""
    ran_at: str = ""


class Triage(BaseModel):
    """A decision model's answer about one claim."""

    claim_id: str
    question: Literal["failure", "judge"]
    asked_key: str = Field(description="A hash of what was asked, so the same question is not asked twice.")
    model: str
    score: float = Field(description="failure: chance the claim is false. judge: chance the lines show it true.")
    verdict: str = Field(description="failure: claim_false, check_wrong or unclear. judge: true, false or not_shown.")
    answers: dict[str, Any]


class CheckQuality(BaseModel):
    """How far a check can be trusted: mutants of its code it noticed, and whether it tests what its claim says."""

    claim_id: str
    mutants: int | None = Field(default=None, description="Changes to its code tried; None when not measured.")
    killed: int | None = Field(default=None, description="Of those, the ones the check noticed.")
    survived: list[str] = Field(default_factory=list, description="The changes it did not notice, a few.")
    mutant_key: str = ""
    link_score: float | None = Field(default=None, description="0 to 1: does the check test what the claim says.")
    link_verdict: str | None = Field(default=None, description="unrelated, keyword, nearby or the claim itself.")
    link_key: str = ""
    accepted_by: str = Field(
        default="", description="Who accepted a weak check as the best there is: a person or auto."
    )
    accepted_note: str = Field(default="", description="Why it was accepted.")
    strengthen_key: str = Field(default="", description="The check and code the last rewrite attempt was made on.")


class Counts(BaseModel):
    """How many rows the main tables hold."""

    files: int
    chunks: int
    claim_extractions: int
    claims: int
    claims_by_type: dict[str, int]


def _quality_row(row: Any) -> CheckQuality:
    """Build a check's quality from a check_quality row read in column order."""
    return CheckQuality(
        claim_id=row[0],
        mutants=row[1],
        killed=row[2],
        survived=json.loads(row[3]),
        mutant_key=row[4],
        link_score=row[5],
        link_verdict=row[6],
        link_key=row[7],
        accepted_by=row[8],
        accepted_note=row[9],
        strengthen_key=row[10],
    )


def _now() -> str:
    """Return the current UTC time to the second, ISO formatted."""
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


class Store:
    """Read and write the audit database; use it as a context manager so it closes.

    Parameters
    ----------
    path :
        The SQLite file; its folder is created when missing. None opens an empty database in memory, for reading
        a project that has none yet without creating its file.
    """

    def __init__(self, path: plb.Path | None) -> None:
        if path is None:
            self._db = sqlite3.connect(":memory:")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            self._db = sqlite3.connect(path)
        self._db.execute("PRAGMA foreign_keys = ON")
        self._migrate()

    def _migrate(self) -> None:
        """Bring the schema up to Alembic's head on this connection; a revision that has run never runs again."""
        engine = sqlalchemy.create_engine("sqlite://", creator=lambda: self._db, poolclass=StaticPool)
        config = alembic.config.Config()
        config.set_main_option("script_location", str(MIGRATIONS))
        with engine.begin() as connection:
            config.attributes["connection"] = connection
            alembic.command.upgrade(config, "head")

    def record_project(self, key: str, root: plb.Path) -> None:
        """Record which repository this database belongs to."""
        with self._db:
            self._db.execute("INSERT OR REPLACE INTO project VALUES (?, ?, ?)", (key, str(root), _now()))

    def __enter__(self) -> Self:
        """Return the open store."""
        return self

    def __exit__(
        self, kind: type[BaseException] | None, error: BaseException | None, trace: TracebackType | None
    ) -> None:
        """Close the connection."""
        self._db.close()

    def replace_files(self, files: Iterable[FileRow]) -> int:
        """Replace the files table with ``files`` and return how many were stored."""
        rows = [(f.path, f.sha256, f.size, f.lang, f.description, int(f.is_text), f.score, _now()) for f in files]
        with self._db:
            self._db.execute("DELETE FROM files")
            self._db.executemany("INSERT INTO files VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rows)
        return len(rows)

    def replace_chunks(self, chunks: list[Chunk], concepts: set[str] | None = None) -> None:
        """Store ``chunks`` as the current chunks of their concepts; a chunk that is gone or changed loses its claims.

        Parameters
        ----------
        chunks :
            The concepts' chunks, in order within each concept.
        concepts :
            The concepts these chunks replace: their other stored chunks are dropped. None replaces every chunk,
            for a whole bundle.
        """
        order: dict[str, int] = {}
        positions = []
        for c in chunks:
            positions.append(order.get(c.concept, 0))
            order[c.concept] = positions[-1] + 1
        rows = [
            (
                c.id,
                i,
                c.concept,
                c.type,
                c.status,
                c.title,
                c.section,
                json.dumps(c.sentences),
                c.corrections,
                c.key,
                c.extraction_key,
                c.earlier,
                json.dumps(c.earlier_ids),
                _now(),
                int(c.is_correction),
            )
            for i, c in zip(positions, chunks, strict=True)
        ]
        with self._db:
            self._db.execute("CREATE TEMP TABLE IF NOT EXISTS keep (id TEXT PRIMARY KEY)")
            self._db.execute("DELETE FROM keep")
            self._db.executemany("INSERT INTO keep VALUES (?)", [(c.id,) for c in chunks])
            if concepts is None:
                self._db.execute("DELETE FROM chunks WHERE id NOT IN (SELECT id FROM keep)")
            else:
                self._db.executemany(
                    "DELETE FROM chunks WHERE concept = ? AND id NOT IN (SELECT id FROM keep)", [(c,) for c in concepts]
                )
            # A chunk whose text changed keeps no claims from its old text; the next extraction writes new ones.
            stored = dict(self._db.execute("SELECT id, extraction_key FROM chunks").fetchall())
            changed = [(c.id,) for c in chunks if c.id in stored and stored[c.id] != c.extraction_key]
            self._db.executemany("DELETE FROM claims WHERE chunk_id = ?", changed)
            self._db.executemany("DELETE FROM sentence_verdicts WHERE chunk_id = ?", changed)
            # Links from or to changed text no longer hold; the corrections pass judges them again.
            self._db.executemany("DELETE FROM correction_judgements WHERE correction_chunk_id = ?", changed)
            self._db.executemany("DELETE FROM correction_links WHERE target_chunk_id = ?", changed)
            self._db.executemany(
                "INSERT INTO chunks (id, position, concept, type, status, title, section, sentences, corrections, key, "
                "extraction_key, earlier, earlier_ids, chunked_at, is_correction) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET "
                "position=excluded.position, concept=excluded.concept, type=excluded.type, status=excluded.status, "
                "title=excluded.title, section=excluded.section, sentences=excluded.sentences, "
                "corrections=excluded.corrections, key=excluded.key, extraction_key=excluded.extraction_key, "
                "earlier=excluded.earlier, earlier_ids=excluded.earlier_ids, chunked_at=excluded.chunked_at, "
                "is_correction=excluded.is_correction",
                rows,
            )

    def chunks(self, concepts: set[str] | None = None) -> list[Chunk]:
        """Return the stored chunks of ``concepts`` (all when None), ordered by concept, then section."""
        cursor = self._db.execute(
            "SELECT id, concept, type, status, title, section, sentences, corrections, key, earlier, earlier_ids, "
            "is_correction FROM chunks ORDER BY concept, position"
        )
        return [
            Chunk(
                id=r[0],
                concept=r[1],
                type=r[2],
                status=r[3],
                title=r[4],
                section=r[5],
                sentences=json.loads(r[6]),
                corrections=r[7],
                key=r[8],
                earlier=r[9],
                earlier_ids=json.loads(r[10]),
                is_correction=bool(r[11]),
            )
            for r in cursor
            if concepts is None or r[1] in concepts
        ]

    def extraction(self, chunk: Chunk, model: str, prompt_hash: str, salt: str) -> ChunkResult | None:
        """Return the stored result of one run on this chunk's content, or None when the run has not been made.

        A result that lacks a verdict for some sentence, stored before such answers counted as failed, is treated as
        not made, so the run is asked again.
        """
        row = self._db.execute(
            "SELECT claims, error, tokens_in, tokens_out, verdicts FROM claim_extractions "
            "WHERE extraction_key = ? AND model = ? AND prompt_hash = ? AND salt = ?",
            (chunk.extraction_key, model, prompt_hash, salt),
        ).fetchone()
        if row is None:
            return None
        claims = [Claim.model_validate(c) for c in json.loads(row[0])]
        verdicts = [SentenceNote.model_validate(v) for v in json.loads(row[4])]
        if not {v.n for v in verdicts} >= set(range(1, len(chunk.sentences) + 1)):
            return None
        return ChunkResult(
            id=chunk.id,
            key=chunk.extraction_key,
            claims=claims,
            verdicts=verdicts,
            error=row[1],
            tokens=TokenCounts(input=row[2], output=row[3]),
            cached=True,
        )

    def save_extraction(self, result: ChunkResult, model: str, prompt_hash: str, salt: str) -> None:
        """Store one run's result, replacing an earlier one for the same content and run."""
        claims = json.dumps([c.model_dump(mode="json") for c in result.claims])
        with self._db:
            self._db.execute(
                "INSERT OR REPLACE INTO claim_extractions (extraction_key, model, prompt_hash, salt, chunk_id, claims, "
                "error, tokens_in, tokens_out, created_at, verdicts) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    result.key,
                    model,
                    prompt_hash,
                    salt,
                    result.id,
                    claims,
                    result.error,
                    result.tokens.input,
                    result.tokens.output,
                    _now(),
                    json.dumps([v.model_dump(mode="json") for v in result.verdicts]),
                ),
            )

    def replace_claims(self, chunk_id: str, claims: list[StoredClaim]) -> None:
        """Replace one chunk's claims."""
        rows = [
            (
                c.chunk_id,
                c.position,
                c.claim_id,
                c.concept,
                c.sentence_n,
                c.sentence,
                c.claim_type,
                c.claim,
                c.how_to_check,
                c.quantifier,
                json.dumps(c.refers_to),
                c.run,
                c.reason,
            )
            for c in claims
        ]
        with self._db:
            self._db.execute("DELETE FROM claims WHERE chunk_id = ?", (chunk_id,))
            self._db.executemany(
                "INSERT INTO claims (chunk_id, position, claim_id, concept, sentence_n, sentence, claim_type, claim, "
                "how_to_check, quantifier, refers_to, run, reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                rows,
            )

    def correction_key(self, correction_chunk_id: str) -> str | None:
        """Return the key a correction section was last judged under, or None when it has not been judged."""
        row = self._db.execute(
            "SELECT judged_key FROM correction_judgements WHERE correction_chunk_id = ?", (correction_chunk_id,)
        ).fetchone()
        return str(row[0]) if row else None

    def save_correction(self, correction_chunk_id: str, key: str, model: str, links: list[CorrectionLink]) -> None:
        """Store one correction section's judgement and links, replacing its earlier ones."""
        with self._db:
            self._db.execute("DELETE FROM correction_judgements WHERE correction_chunk_id = ?", (correction_chunk_id,))
            self._db.execute(
                "INSERT INTO correction_judgements VALUES (?, ?, ?, ?)", (correction_chunk_id, key, model, _now())
            )
            self._db.executemany(
                "INSERT INTO correction_links VALUES (?, ?, ?, ?, ?, ?)",
                [(l.correction_chunk, l.correction_n, l.target_chunk, l.target_n, l.claim_id, l.reason) for l in links],
            )

    def correction_links(self) -> list[CorrectionLink]:
        """Return every stored correction link."""
        cursor = self._db.execute(
            "SELECT correction_chunk_id, correction_n, target_chunk_id, target_n, claim_id, reason FROM correction_links "
            "ORDER BY correction_chunk_id, correction_n, target_chunk_id, target_n"
        )
        return [
            CorrectionLink(
                correction_chunk=r[0], correction_n=r[1], target_chunk=r[2], target_n=r[3], claim_id=r[4], reason=r[5]
            )
            for r in cursor
        ]

    def replace_verdicts(self, chunk_id: str, verdicts: list[SentenceNote]) -> None:
        """Replace one chunk's sentence verdicts."""
        with self._db:
            self._db.execute("DELETE FROM sentence_verdicts WHERE chunk_id = ?", (chunk_id,))
            self._db.executemany(
                "INSERT INTO sentence_verdicts VALUES (?, ?, ?, ?, ?)",
                [(chunk_id, v.n, v.kind, v.reason, v.run) for v in verdicts],
            )

    def verdicts(self, chunk_id: str) -> list[SentenceNote]:
        """Return one chunk's sentence verdicts, in sentence order."""
        cursor = self._db.execute(
            "SELECT sentence_n, kind, reason, run FROM sentence_verdicts WHERE chunk_id = ? ORDER BY sentence_n",
            (chunk_id,),
        )
        return [SentenceNote(n=r[0], kind=r[1], reason=r[2], run=r[3]) for r in cursor]

    def claims(self) -> list[StoredClaim]:
        """Return every stored claim, in bundle order."""
        cursor = self._db.execute(
            "SELECT c.chunk_id, c.position, c.claim_id, c.concept, c.sentence_n, c.sentence, c.claim_type, c.claim, "
            "c.how_to_check, c.quantifier, c.refers_to, c.run, c.reason FROM claims c JOIN chunks k ON k.id = c.chunk_id "
            "ORDER BY k.concept, k.position, c.position"
        )
        names = list(StoredClaim.model_fields)
        return [StoredClaim.model_validate({**dict(zip(names, r)), "refers_to": json.loads(r[10])}) for r in cursor]

    def save_check(self, check: StoredCheck) -> None:
        """Store one claim's check with its reads, replacing the old one and with it its result and triage."""
        with self._db:
            self._db.execute("DELETE FROM checks WHERE claim_id = ?", (check.claim_id,))
            self._db.execute(
                "INSERT INTO checks (claim_id, kind, steps, strength, why, settled, writer, prompt_hash, "
                "expectation_changed, tokens, commit_sha, written_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    check.claim_id,
                    check.kind,
                    json.dumps(check.steps) if check.kind == "check" else None,
                    check.strength,
                    check.why,
                    None if check.settled is None else int(check.settled),
                    check.writer,
                    check.prompt_hash,
                    int(check.expectation_changed),
                    check.tokens,
                    check.commit_sha,
                    _now(),
                ),
            )
            self._db.executemany(
                "INSERT INTO check_reads VALUES (?, ?, ?)", [(check.claim_id, p, h) for p, h in check.reads.items()]
            )

    def set_reads(self, claim_id: str, reads: dict[str, str]) -> None:
        """Replace the files a check read, after a run that read different ones."""
        with self._db:
            self._db.execute("DELETE FROM check_reads WHERE claim_id = ?", (claim_id,))
            self._db.executemany(
                "INSERT INTO check_reads VALUES (?, ?, ?)", [(claim_id, p, h) for p, h in reads.items()]
            )

    def checks(self) -> dict[str, StoredCheck]:
        """Return every stored check, by claim id."""
        reads: dict[str, dict[str, str]] = {}
        for claim_id, path, sha in self._db.execute("SELECT claim_id, path, sha FROM check_reads"):
            reads.setdefault(claim_id, {})[path] = sha
        cursor = self._db.execute(
            "SELECT claim_id, kind, steps, strength, why, settled, writer, prompt_hash, expectation_changed, tokens, "
            "commit_sha FROM checks"
        )
        return {
            r[0]: StoredCheck(
                claim_id=r[0],
                kind=r[1],
                steps=json.loads(r[2]) if r[2] else [],
                strength=r[3],
                why=r[4],
                settled=None if r[5] is None else bool(r[5]),
                writer=r[6],
                prompt_hash=r[7],
                expectation_changed=bool(r[8]),
                tokens=r[9],
                commit_sha=r[10],
                reads=reads.get(r[0], {}),
            )
            for r in cursor
        }

    def delete_check(self, claim_id: str) -> None:
        """Delete one claim's check, with its reads, result and triage."""
        with self._db:
            self._db.execute("DELETE FROM checks WHERE claim_id = ?", (claim_id,))

    def prune_checks(self, keep: set[str]) -> int:
        """Delete the checks of claims not in ``keep`` (changed or removed claims) and return how many went."""
        gone = [r[0] for r in self._db.execute("SELECT claim_id FROM checks") if r[0] not in keep]
        with self._db:
            self._db.executemany("DELETE FROM checks WHERE claim_id = ?", [(g,) for g in gone])
        return len(gone)

    def save_result(self, result: CheckResult) -> None:
        """Store a check's last run, replacing the one before."""
        with self._db:
            self._db.execute(
                "INSERT OR REPLACE INTO check_results VALUES (?, ?, ?, ?, ?, ?)",
                (
                    result.claim_id,
                    int(result.holds),
                    json.dumps(result.results),
                    result.reads_key,
                    result.commit_sha,
                    result.ran_at or _now(),
                ),
            )

    def results(self) -> dict[str, CheckResult]:
        """Return each check's last run, by claim id."""
        cursor = self._db.execute("SELECT claim_id, holds, results, reads_key, commit_sha, ran_at FROM check_results")
        return {
            r[0]: CheckResult(
                claim_id=r[0], holds=bool(r[1]), results=json.loads(r[2]), reads_key=r[3], commit_sha=r[4], ran_at=r[5]
            )
            for r in cursor
        }

    def save_triage(self, triage: Triage) -> None:
        """Store a decision model's answer about a claim, replacing the one before."""
        with self._db:
            self._db.execute(
                "INSERT OR REPLACE INTO check_triage VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    triage.claim_id,
                    triage.question,
                    triage.asked_key,
                    triage.model,
                    triage.score,
                    triage.verdict,
                    json.dumps(triage.answers),
                    _now(),
                ),
            )

    def triage(self) -> dict[str, Triage]:
        """Return each claim's latest decision-model answer, by claim id."""
        cursor = self._db.execute(
            "SELECT claim_id, question, asked_key, model, score, verdict, answers FROM check_triage"
        )
        return {
            r[0]: Triage(
                claim_id=r[0],
                question=r[1],
                asked_key=r[2],
                model=r[3],
                score=r[4],
                verdict=r[5],
                answers=json.loads(r[6]),
            )
            for r in cursor
        }

    def save_mutation(self, claim_id: str, mutants: int, killed: int, survived: list[str], key: str) -> None:
        """Store a check's mutation score, keeping its link score."""
        with self._db:
            self._db.execute(
                "INSERT INTO check_quality (claim_id, mutants, killed, survived, mutant_key) VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT(claim_id) DO UPDATE SET mutants = excluded.mutants, killed = excluded.killed, "
                "survived = excluded.survived, mutant_key = excluded.mutant_key, "
                # an automatic acceptance holds for the code it was made on: once that changes, try again
                "accepted_by = CASE WHEN check_quality.accepted_by = 'auto' AND check_quality.mutant_key != "
                "excluded.mutant_key THEN '' ELSE check_quality.accepted_by END",
                (claim_id, mutants, killed, json.dumps(survived[:5]), key),
            )

    def save_link(self, claim_id: str, score: float, verdict: str, key: str) -> None:
        """Store a check's link score, keeping its mutation score."""
        with self._db:
            self._db.execute(
                "INSERT INTO check_quality (claim_id, link_score, link_verdict, link_key) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(claim_id) DO UPDATE SET link_score = excluded.link_score, "
                "link_verdict = excluded.link_verdict, link_key = excluded.link_key",
                (claim_id, score, verdict, key),
            )

    def set_acceptance(self, claim_id: str, by: str, note: str = "", strengthen_key: str | None = None) -> None:
        """Mark a check accepted (``by`` a person or "auto"), or clear it with ``by=""``; record a rewrite attempt."""
        with self._db:
            self._db.execute(
                "INSERT INTO check_quality (claim_id, accepted_by, accepted_note, strengthen_key) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(claim_id) DO UPDATE SET accepted_by = excluded.accepted_by, "
                "accepted_note = excluded.accepted_note, strengthen_key = CASE WHEN ? IS NULL "
                "THEN check_quality.strengthen_key ELSE excluded.strengthen_key END",
                (claim_id, by, note, strengthen_key or "", strengthen_key),
            )

    def quality_of(self, claim_id: str) -> CheckQuality | None:
        """Return one check's quality, or None when it has none yet."""
        row = self._db.execute(
            "SELECT claim_id, mutants, killed, survived, mutant_key, link_score, link_verdict, link_key, accepted_by, "
            "accepted_note, strengthen_key "
            "FROM check_quality WHERE claim_id = ?",
            (claim_id,),
        ).fetchone()
        if row is None:
            return None
        return _quality_row(row)

    def quality(self) -> dict[str, CheckQuality]:
        """Return each check's quality, by claim id."""
        cursor = self._db.execute(
            "SELECT claim_id, mutants, killed, survived, mutant_key, link_score, link_verdict, link_key, accepted_by, "
            "accepted_note, strengthen_key "
            "FROM check_quality"
        )
        return {r[0]: _quality_row(r) for r in cursor}

    def claim_job(
        self,
        verb: str,
        args: list[str],
        pid: int,
        pid_started: str,
        live: Callable[[int | None, str], bool],
        job_id: int | None = None,
    ) -> tuple[int | None, dict[str, Any] | None]:
        """Take the project's one run slot in a single transaction: return (the new or given job id, None), or
        (None, the job that holds it) when another live job does.

        ``live(pid, pid_started)`` says whether a job's process is still the one that started it; a job whose process
        is gone is marked died on the way. ``job_id`` is a job this process was started to run (a background run).
        """
        self._db.execute("BEGIN IMMEDIATE")  # no other process can claim between the check and the insert
        try:
            for row in self._db.execute(
                "SELECT id, pid, pid_started, stage, done, total FROM jobs WHERE status IN ('running', 'starting')"
            ).fetchall():
                if row[0] == job_id:
                    continue
                if live(row[1], row[2]):
                    self._db.execute("ROLLBACK")
                    names = ["id", "pid", "pid_started", "stage", "done", "total"]
                    return None, dict(zip(names, row, strict=True))
                self._db.execute(
                    "UPDATE jobs SET status = 'died', finished_at = ?, updated_at = ?, "
                    "error = CASE WHEN error = '' THEN 'its process ended without saying how' ELSE error END "
                    "WHERE id = ?",
                    (_now(), _now(), row[0]),
                )
            now = _now()
            if job_id is None:
                cursor = self._db.execute(
                    "INSERT INTO jobs (verb, args, pid, pid_started, status, started_at, updated_at) "
                    "VALUES (?, ?, ?, ?, 'running', ?, ?)",
                    (verb, json.dumps(args), pid, pid_started, now, now),
                )
                job_id = int(cursor.lastrowid or 0)
            else:
                self._db.execute(
                    "UPDATE jobs SET pid = ?, pid_started = ?, status = 'running', updated_at = ? WHERE id = ?",
                    (pid, pid_started, now, job_id),
                )
            self._db.execute("COMMIT")
        except BaseException:
            self._db.execute("ROLLBACK")
            raise
        return job_id, None

    def start_job(self, verb: str, args: list[str], pid: int | None, log_path: str = "") -> int:
        """Record a run starting and return its job id."""
        now = _now()
        with self._db:
            cursor = self._db.execute(
                "INSERT INTO jobs (verb, args, pid, status, started_at, updated_at, log_path) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (verb, json.dumps(args), pid, "running" if pid else "starting", now, now, log_path),
            )
        return int(cursor.lastrowid or 0)

    def update_job(self, job_id: int, **fields: Any) -> None:
        """Set some of a job's fields: pid, status, stage, done, total, summary (a dict), error, log_path."""
        allowed = {"pid", "pid_started", "status", "stage", "done", "total", "summary", "error", "log_path"}
        sets = {k: (json.dumps(v) if k == "summary" else v) for k, v in fields.items() if k in allowed}
        sets["updated_at"] = _now()
        if fields.get("status") in {"done", "failed", "stopped", "died", "refused"}:
            sets["finished_at"] = _now()
        columns = ", ".join(f"{k} = ?" for k in sets)  # names from the allowed set above
        with self._db:
            self._db.execute(f"UPDATE jobs SET {columns} WHERE id = ?", (*sets.values(), job_id))

    def jobs(self, limit: int = 5) -> list[dict[str, Any]]:
        """Return the latest jobs, newest first."""
        cursor = self._db.execute(
            "SELECT id, verb, args, pid, status, stage, done, total, started_at, updated_at, finished_at, log_path, "
            "summary, error, pid_started FROM jobs ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        names = [
            "id",
            "verb",
            "args",
            "pid",
            "status",
            "stage",
            "done",
            "total",
            "started_at",
            "updated_at",
            "finished_at",
            "log_path",
            "summary",
            "error",
            "pid_started",
        ]
        rows = [dict(zip(names, r, strict=True)) for r in cursor]
        for row in rows:
            row["args"], row["summary"] = json.loads(row["args"]), json.loads(row["summary"])
        return rows

    def cached(self, key: str) -> Any:
        """Return a cached value, or None."""
        row = self._db.execute("SELECT value FROM cache WHERE key = ?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def cache(self, key: str, value: Any) -> None:
        """Keep a value under a key, replacing one kept before."""
        with self._db:
            self._db.execute("INSERT OR REPLACE INTO cache VALUES (?, ?, ?)", (key, json.dumps(value), _now()))

    def record_pass(self, verb: str, started_at: str, seconds: float, report: dict[str, Any]) -> None:
        """Record one checks command: what it did and spent."""
        with self._db:
            self._db.execute(
                "INSERT INTO check_passes (verb, started_at, seconds, report) VALUES (?, ?, ?, ?)",
                (verb, started_at, seconds, json.dumps(report)),
            )

    def passes(self) -> list[dict[str, Any]]:
        """Return every recorded checks command, oldest first."""
        cursor = self._db.execute("SELECT verb, started_at, seconds, report FROM check_passes ORDER BY id")
        return [{"verb": r[0], "started_at": r[1], "seconds": r[2], "report": json.loads(r[3])} for r in cursor]

    def counts(self) -> Counts:
        """Return how many rows each table holds, and the claims per type."""

        def count(table: str) -> int:
            """Return one table's row count."""
            return int(self._db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])  # fixed names

        by_type = dict(
            self._db.execute("SELECT claim_type, COUNT(*) FROM claims GROUP BY claim_type ORDER BY 2 DESC").fetchall()
        )
        return Counts(
            files=count("files"),
            chunks=count("chunks"),
            claim_extractions=count("claim_extractions"),
            claims=count("claims"),
            claims_by_type=by_type,
        )
