"""The check answer schema, and reading and writing checks in the audit store.

A claim has at most one stored answer: a check (steps that run with no
model) or a reason no check fits. Its check id is its claim id. Later
tickets read a check's claim, steps and last run through ``check``, never by
parsing command output.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from kmaudit.models import Claim
from kmaudit.mutate import VERSION as MUTATION_VERSION
from kmaudit.mutate import Quality
from kmaudit.steps import AnyStep, Step, StepResult
from kmaudit.store import Store

STEPS_ADAPTER: TypeAdapter[list[AnyStep]] = TypeAdapter(list[Step])
RESULTS_ADAPTER: TypeAdapter[list[StepResult]] = TypeAdapter(list[StepResult])


class CheckAnswer(BaseModel):
    """A check for one claim: steps kmaudit reruns with no model."""

    model_config = ConfigDict(extra="forbid")

    claim: str = Field(description="The claim id that checks_todo gave.")
    steps: list[Step] = Field(
        min_length=1, description="At least one step; with none, give a reason instead."
    )
    strength: Literal["exact", "proxy"] = Field(
        description="exact: the steps decide the claim. proxy: they show the code exists; behaviour must still be read."
    )
    why: str = Field(
        min_length=1,
        description="One sentence: why these steps hold exactly when the claim does.",
    )
    drift: str | None = Field(
        default=None,
        description="Only when the check fails because the claim is wrong: one sentence on what the code does instead.",
    )


class ReasonAnswer(BaseModel):
    """A reason no check fits a claim."""

    model_config = ConfigDict(extra="forbid")

    claim: str = Field(description="The claim id that checks_todo gave.")
    reason: str = Field(
        min_length=1, description="One sentence: why no step can test the claim."
    )


Answer = CheckAnswer | ReasonAnswer
ANSWER_ADAPTER: TypeAdapter[Answer] = TypeAdapter(Answer)


@dataclass(frozen=True)
class StoredCheck:
    """One stored answer with its last run and mutation score, read back by claim id.

    Attributes
    ----------
    kind : str
        ``check`` or ``reason``.
    reads : dict[str, str]
        The files the check read (or a reason's lines came from) with their hashes, when stored or last run.
    """

    claim_id: str
    kind: str
    steps: list[AnyStep]
    strength: str
    why: str
    drift: str | None
    reason: str
    submitted_by: str
    reads: dict[str, str]
    reads_key: str | None
    holds: bool | None
    skipped: bool
    results: list[StepResult]
    quality_key: str | None
    quality: Quality | None


def quality_key(steps: list[AnyStep], key: str) -> str:
    """The key a mutation score is kept under: the steps, the reads key and the mutation version."""
    content = [STEPS_ADAPTER.dump_python(steps, mode="json"), key, MUTATION_VERSION]
    return hashlib.sha256(json.dumps(content).encode()).hexdigest()[:16]


def _now() -> str:
    """The current UTC time as ISO 8601 seconds."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def save_answer(
    store: Store, answer: Answer, reads: dict[str, str], by: str, claim: Claim
) -> None:
    """Replace a claim's stored answer, and the files it read, in one transaction.

    The claim's concept and sentence are kept with the answer, so ``prune``
    can move it to the claim re-extraction makes of the same sentence.
    """
    is_check = isinstance(answer, CheckAnswer)
    row = (
        answer.claim,
        "check" if is_check else "reason",
        json.dumps(STEPS_ADAPTER.dump_python(answer.steps, mode="json"))
        if is_check
        else "[]",
        answer.strength if is_check else "",
        answer.why if is_check else "",
        answer.drift if is_check else None,
        "" if is_check else answer.reason,
        by,
        _now(),
        claim.concept,
        claim.section,
        claim.sentence,
    )
    db = store.db
    db.execute("BEGIN IMMEDIATE")
    try:
        db.execute("DELETE FROM checks WHERE claim_id = ?", (answer.claim,))
        db.execute(
            "INSERT INTO checks (claim_id, kind, steps, strength, why, drift, reason, submitted_by, "
            "submitted_at, concept, section, sentence) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            row,
        )
        db.executemany(
            "INSERT INTO check_reads (claim_id, path, sha) VALUES (?, ?, ?)",
            [(answer.claim, p, s) for p, s in reads.items()],
        )
        db.execute("COMMIT")
    except BaseException:
        db.execute("ROLLBACK")
        raise


def save_run(
    store: Store,
    claim_id: str,
    reads: dict[str, str],
    key: str,
    holds: bool,
    results: list[StepResult],
) -> None:
    """Record a check's run: what it read, and each step's result."""
    db = store.db
    db.execute("BEGIN IMMEDIATE")
    try:
        db.execute("DELETE FROM check_reads WHERE claim_id = ?", (claim_id,))
        db.executemany(
            "INSERT INTO check_reads (claim_id, path, sha) VALUES (?, ?, ?)",
            [(claim_id, p, s) for p, s in reads.items()],
        )
        db.execute(
            "INSERT OR REPLACE INTO check_runs (claim_id, reads_key, holds, skipped, results, ran_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                claim_id,
                key,
                int(holds),
                int(any(r.skipped for r in results)),
                RESULTS_ADAPTER.dump_json(results).decode(),
                _now(),
            ),
        )
        db.execute("COMMIT")
    except BaseException:
        db.execute("ROLLBACK")
        raise


def save_quality(store: Store, claim_id: str, key: str, quality: Quality) -> None:
    """Record a check's mutation score under its key."""
    store.db.execute(
        "INSERT OR REPLACE INTO check_quality (claim_id, key, mutants, killed, survived) VALUES (?, ?, ?, ?, ?)",
        (claim_id, key, quality.mutants, quality.killed, json.dumps(quality.survived)),
    )


def check(store: Store, claim_id: str) -> StoredCheck | None:
    """The stored answer for one claim, with its reads, last run and mutation score; None when there is none."""
    row = store.db.execute(
        "SELECT * FROM checks WHERE claim_id = ?", (claim_id,)
    ).fetchone()
    if row is None:
        return None
    reads = {
        r["path"]: r["sha"]
        for r in store.db.execute(
            "SELECT path, sha FROM check_reads WHERE claim_id = ? ORDER BY path",
            (claim_id,),
        )
    }
    run = store.db.execute(
        "SELECT * FROM check_runs WHERE claim_id = ?", (claim_id,)
    ).fetchone()
    q = store.db.execute(
        "SELECT * FROM check_quality WHERE claim_id = ?", (claim_id,)
    ).fetchone()
    return StoredCheck(
        claim_id=claim_id,
        kind=row["kind"],
        steps=STEPS_ADAPTER.validate_json(row["steps"]),
        strength=row["strength"],
        why=row["why"],
        drift=row["drift"],
        reason=row["reason"],
        submitted_by=row["submitted_by"],
        reads=reads,
        reads_key=None if run is None else run["reads_key"],
        holds=None if run is None else bool(run["holds"]),
        skipped=False if run is None else bool(run["skipped"]),
        results=[] if run is None else RESULTS_ADAPTER.validate_json(run["results"]),
        quality_key=None if q is None else q["key"],
        quality=None
        if q is None
        else Quality(
            mutants=q["mutants"], killed=q["killed"], survived=json.loads(q["survived"])
        ),
    )


def check_ids(store: Store) -> list[str]:
    """The claim id of every stored answer."""
    return [
        r[0] for r in store.db.execute("SELECT claim_id FROM checks ORDER BY claim_id")
    ]


def claim(store: Store, claim_id: str) -> Claim | None:
    """The stored claim with this id (its first section when two share it), or None."""
    return store.claim(claim_id)


@dataclass(frozen=True)
class Pruned:
    """What ``prune`` did with the answers whose claim is gone.

    Attributes
    ----------
    carried : int
        Answers moved to the claim re-extraction made of the same sentence.
    dropped : int
        Answers deleted: no claim, or more than one, came from that sentence.
    """

    carried: int
    dropped: int


_ANSWER_TABLES = ("checks", "check_reads", "check_runs", "check_quality")


def prune(store: Store) -> Pruned:
    """Carry or drop the answers whose claim is gone, leaving those of concepts still waiting for extraction.

    Re-extraction often rewords a claim, which gives it a new id. An answer
    whose claim is gone moves to the one unanswered claim of the same concept
    made from the same sentence; its last run is cleared, so ``run`` checks it
    again against the new claim. People's feedback moves the same way, on
    answered and unanswered claims alike. With no such claim, or more than one, the
    answer is deleted. An answer whose section waits for extraction is left
    alone, since its claim may still come back.
    """
    claims = store.claims()
    live = {c.id for c in claims}
    waiting = store.pending_sections()
    rows = store.db.execute(
        "SELECT claim_id, concept, section, sentence FROM checks"
    ).fetchall()
    answered = {row["claim_id"] for row in rows}
    carried = dropped = 0
    store.db.execute("BEGIN IMMEDIATE")
    try:
        store.db.execute("PRAGMA defer_foreign_keys = ON")
        for row in rows:
            old = row["claim_id"]
            if (
                old in live
                or row["section"] in waiting
                or (not row["section"] and waiting)
            ):
                continue  # an answer stored before sections were kept waits for every section
            fits = [
                c.id
                for c in claims
                if row["concept"] and c.concept == row["concept"] and c.sentence == row["sentence"]
                and c.id not in answered
            ]  # fmt: skip
            if len(fits) == 1:
                for table in _ANSWER_TABLES:
                    store.db.execute(
                        f"UPDATE {table} SET claim_id = ? WHERE claim_id = ?",
                        (fits[0], old),
                    )
                store.db.execute(
                    "UPDATE feedback SET claim_id = ? WHERE claim_id = ?",
                    (fits[0], old),
                )
                store.db.execute(
                    "DELETE FROM check_runs WHERE claim_id = ?", (fits[0],)
                )
                answered.add(fits[0])
                carried += 1
            else:
                store.db.execute("DELETE FROM checks WHERE claim_id = ?", (old,))
                dropped += 1
        _carry_feedback(store, claims, live, waiting)
        store.db.execute("COMMIT")
    except BaseException:
        store.db.execute("ROLLBACK")
        raise
    return Pruned(carried=carried, dropped=dropped)


def _carry_feedback(
    store: Store, claims: list[Claim], live: set[str], waiting: set[str]
) -> None:
    """Move feedback whose claim is gone to the one claim made from the same sentence; the caller holds a transaction.

    Feedback on an answered claim already moved with its answer. With no such
    claim, or more than one, the feedback stays under the old id as history.
    """
    rows = store.db.execute(
        "SELECT DISTINCT claim_id, concept, section, sentence FROM feedback"
    ).fetchall()
    for row in rows:
        if row["claim_id"] in live or row["section"] in waiting:
            continue
        fits = [
            c.id
            for c in claims
            if c.concept == row["concept"] and c.sentence == row["sentence"]
        ]
        if len(fits) == 1:
            store.db.execute(
                "UPDATE feedback SET claim_id = ? WHERE claim_id = ?",
                (fits[0], row["claim_id"]),
            )


def cached(store: Store, key: str) -> object | None:
    """A cached JSON value, or None."""
    row = store.db.execute("SELECT value FROM cache WHERE key = ?", (key,)).fetchone()
    return None if row is None else json.loads(row[0])


def cache(store: Store, key: str, value: object) -> None:
    """Keep a JSON value under ``key``."""
    store.db.execute(
        "INSERT OR REPLACE INTO cache (key, value) VALUES (?, ?)",
        (key, json.dumps(value)),
    )
