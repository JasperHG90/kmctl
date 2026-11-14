"""What people say about claims and checks: thumbs, notes and their own verdict, kept in the audit store.

A person judges one claim at a time, either the claim itself (was it worth
extracting, and worded right) or its check (does the check test the claim,
and does the claim hold). Each save appends a row, so the latest row for a
claim and target is the current judgment and the earlier ones are history.

Feedback that asks for a new answer (a thumbs down, or a verdict the check
disagrees with) stays open until an agent's next answer for that claim or
section takes it in; ``kmaudit claims todo`` and ``kmaudit checks
todo`` hand it out with the work, and submitting marks it answered (ADR 0041).
"""

import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from kmaudit import AuditError
from kmaudit.check_store import STEPS_ADAPTER, check
from kmaudit.steps import Repository
from kmaudit.store import Store

Target = Literal["claim", "check"]
Vote = Literal["up", "down"]
HumanVerdict = Literal["holds", "false"]
#: Check statuses that say the claim holds, and those that say it does not.
SAYS_HOLDS = ("holds", "not measured", "weak")
SAYS_FALSE = ("drift", "fails")
#: Statuses with no check deciding the claim; a person's "false" there asks for one.
UNSETTLED = ("no check", "reason", "stale reason")
#: How many answers people liked ``todo`` shows as examples.
EXAMPLES = 3
NOTE_MAX = 4000


#: How an agent reads people's feedback in ``todo``. Kept apart from the
#: extraction instructions, which every section key covers.
FEEDBACK_INSTRUCTIONS = """
People review claims and checks on the audit page (kmaudit ui).
Their judgment comes with the work:

- feedback on an item: what a person said about the last answer for it.
  on: claim means the extracted claim (extract the section again and fix
  that claim, or drop it); on: check means its check or reason, shown in
  answer. vote down asks you to redo it. verdict is whether the person
  found the claim holds or is false: it outranks your reading. If they say
  false and the check holds, the check missed the drift: test what the claim
  says so it fails, and set drift. If they say holds and the check fails,
  the check is wrong. note is their reason; act on it.
- examples: answers people marked good, with their notes. Learn from them;
  do not copy them.

Submitting an answer for the item marks its feedback answered. If you still
disagree with the person, submit your answer anyway and say why in why or
reason; the page shows them both.
""".strip()


class FeedbackIn(BaseModel):
    """One person's judgment of a claim or its check, as the audit page sends it."""

    model_config = ConfigDict(extra="forbid")

    claim: str = Field(min_length=1, description="The claim id.")
    target: Target = Field(
        description="claim: the extracted claim itself. check: its check or reason."
    )
    vote: Vote | None = Field(
        default=None, description="up: good work. down: redo it. None: no vote."
    )
    verdict: HumanVerdict | None = Field(
        default=None,
        description="Only on a check: whether the person found the claim holds or is false.",
    )
    note: str = Field(
        default="",
        max_length=NOTE_MAX,
        description="What the person thinks, free text.",
    )

    @model_validator(mode="after")
    def _verdict_on_check(self) -> "FeedbackIn":
        """Refuse a verdict on the claim target: whether a claim holds is said about its check."""
        if self.verdict is not None and self.target != "check":
            raise ValueError("a verdict goes on the check target, not the claim")
        return self


class FeedbackOut(BaseModel):
    """A person's judgment as an agent reads it in ``todo``: what they judged and what they said."""

    on: Target = Field(description="claim or check.")
    claim: str = Field(description="The claim text the person judged.")
    vote: Vote | None = None
    verdict: HumanVerdict | None = Field(
        default=None,
        description="Whether the person found the claim holds or is false.",
    )
    note: str = ""
    answer: dict[str, object] | None = Field(
        default=None,
        description="The check or reason the person judged, when the feedback is on a check.",
    )


@dataclass(frozen=True)
class Feedback:
    """The latest stored judgment of one claim and target.

    Attributes
    ----------
    answer : dict[str, object] | None
        The check or reason judged, as it was then; None on a claim, or when there was none.
    reads : dict[str, str]
        The files that answer read then, with their hashes, so a verdict goes stale when they change.
    answered_at : str | None
        When an agent's next answer took the feedback in; None while it is open.
    """

    claim_id: str
    target: Target
    vote: Vote | None
    verdict: HumanVerdict | None
    note: str
    claim: str
    section: str
    answer: dict[str, object] | None
    reads: dict[str, str]
    by: str
    at: str
    answered_at: str | None

    def out(self) -> FeedbackOut:
        """This judgment in the shape ``todo`` hands an agent."""
        return FeedbackOut(
            on=self.target,
            claim=self.claim,
            vote=self.vote,
            verdict=self.verdict,
            note=self.note,
            answer=self.answer,
        )


def _now() -> str:
    """The current UTC time as ISO 8601 seconds."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def _answer(
    store: Store, claim_id: str
) -> tuple[dict[str, object] | None, dict[str, str]]:
    """The claim's stored check or reason as plain data, with the files it read; (None, {}) when it has none."""
    stored = check(store, claim_id)
    if stored is None:
        return None, {}
    if stored.kind == "reason":
        return {"kind": "reason", "reason": stored.reason}, dict(stored.reads)
    return (
        {
            "kind": "check",
            "steps": STEPS_ADAPTER.dump_python(stored.steps, mode="json"),
            "strength": stored.strength,
            "why": stored.why,
            "drift": stored.drift,
            "holds": stored.holds,
            "saw": [r.detail for r in stored.results],
        },
        dict(stored.reads),
    )


def record(
    store: Store,
    given: FeedbackIn,
    by: str,
    lines_read: dict[str, str] | None = None,
) -> Feedback:
    """Store a person's judgment of a claim or its check, keeping what was judged with it.

    Parameters
    ----------
    store :
        The open audit store.
    given :
        The judgment.
    by :
        Who gave it, kept with the row.
    lines_read :
        The files behind the lines the claim is about, with their hashes,
        kept when its answer read no files (no check yet, or a reason found
        by keyword), so a verdict on it still goes stale when they change.

    Returns
    -------
    Feedback
        The judgment as stored, now the latest for its claim and target.

    Raises
    ------
    AuditError
        When the store has no claim with that id.
    """
    found = store.claim(given.claim)
    if found is None:
        raise AuditError(
            f"no stored claim {given.claim!r}; it was re-extracted or removed, so reload the page"
        )
    answer, reads = (
        _answer(store, given.claim) if given.target == "check" else (None, {})
    )
    if given.target == "check" and not reads:
        reads = dict(lines_read or {})
    store.db.execute(
        "INSERT INTO feedback (claim_id, target, vote, verdict, note, concept, section, sentence, claim, "
        "answer, reads, submitted_by, submitted_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            given.claim,
            given.target,
            given.vote,
            given.verdict,
            given.note.strip(),
            found.concept,
            found.section,
            found.sentence,
            found.claim,
            "" if answer is None else json.dumps(answer),
            json.dumps(reads),
            by,
            _now(),
        ),
    )
    return latest(store, [given.claim])[(given.claim, given.target)]


def latest(
    store: Store, claim_ids: Iterable[str] | None = None
) -> dict[tuple[str, Target], Feedback]:
    """The latest judgment per (claim id, target); only those claims when ``claim_ids`` is given."""
    ids = None if claim_ids is None else list(claim_ids)
    where = "" if ids is None else f"WHERE claim_id IN ({','.join('?' * len(ids))})"
    rows = store.db.execute(
        f"SELECT * FROM feedback {where} ORDER BY id", tuple(ids or ())
    ).fetchall()
    found: dict[tuple[str, Target], Feedback] = {}
    for row in rows:
        found[(row["claim_id"], row["target"])] = Feedback(
            claim_id=row["claim_id"],
            target=row["target"],
            vote=row["vote"],
            verdict=row["verdict"],
            note=row["note"],
            claim=row["claim"],
            section=row["section"],
            answer=json.loads(row["answer"]) if row["answer"] else None,
            reads=json.loads(row["reads"]),
            by=row["submitted_by"],
            at=row["submitted_at"],
            answered_at=row["answered_at"],
        )
    return found


def disagrees(verdict: HumanVerdict | None, status: str) -> bool:
    """Whether a check's status says the opposite of a person's verdict on its claim."""
    return (verdict == "holds" and status in SAYS_FALSE) or (
        verdict == "false" and status in SAYS_HOLDS
    )


def current(repo: Repository, feedback: Feedback) -> bool:
    """Whether the files the judged answer read are unchanged, so the person's verdict still applies."""
    return all(repo.sha(path) == sha for path, sha in feedback.reads.items())


def is_open(feedback: Feedback) -> bool:
    """Whether feedback says something no agent's answer has taken in yet: a vote, a verdict or a note.

    Open feedback rides along whenever ``todo`` hands its item out, and the
    next answer for that item marks it answered.
    """
    return feedback.answered_at is None and bool(
        feedback.vote or feedback.verdict or feedback.note
    )


def wants_check(feedback: Feedback, status: str, fresh: bool) -> bool:
    """Whether open feedback on a check sends the claim back to ``checks todo``.

    A thumbs down always does. A verdict does while it is ``fresh`` (the
    files it was given on are unchanged) and the check says the opposite,
    or when the person says false and no check decides the claim yet.
    A note alone does not; it waits for the next time the claim is handed out.
    """
    if feedback.answered_at is not None:
        return False
    if feedback.vote == "down":
        return True
    if not fresh or feedback.verdict is None:
        return False
    return disagrees(feedback.verdict, status) or (
        feedback.verdict == "false" and status in UNSETTLED
    )


def wants_extraction(feedback: Feedback) -> bool:
    """Whether open feedback on a claim sends its section back to ``claims todo``: a thumbs down."""
    return feedback.answered_at is None and feedback.vote == "down"


def take_in_checks(store: Store, claim_ids: Iterable[str]) -> None:
    """Mark the open check feedback of these claims answered, once a new answer for each is stored."""
    store.db.executemany(
        "UPDATE feedback SET answered_at = ? WHERE claim_id = ? AND target = 'check' AND answered_at IS NULL",
        [(_now(), cid) for cid in claim_ids],
    )


def take_in_section(store: Store, section_id: str) -> None:
    """Mark the open claim feedback of one section answered, once its new extraction is stored."""
    store.db.execute(
        "UPDATE feedback SET answered_at = ? WHERE section = ? AND target = 'claim' AND answered_at IS NULL",
        (_now(), section_id),
    )


def liked(store: Store, target: Target, limit: int = EXAMPLES) -> list[FeedbackOut]:
    """The newest answers people gave a thumbs up on this target, for ``todo`` to show as examples."""
    ups = [
        f
        for f in latest(store).values()
        if f.target == target and f.vote == "up" and (target == "claim" or f.answer)
    ]
    ups.sort(key=lambda f: (bool(f.note), f.at), reverse=True)
    return [f.out() for f in ups[:limit]]
