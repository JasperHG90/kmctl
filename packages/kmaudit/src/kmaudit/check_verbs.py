"""What the ``kmaudit checks`` verbs do, callable without the CLI: todo, try, submit, run and list."""

import json
import re
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from kmaudit import AuditError
from kmaudit.anchors import (
    SPAN,
    Anchor,
    Evidence,
    claim_commands,
    located,
    resolve,
)
from kmaudit.check_instructions import INSTRUCTIONS
from kmaudit.check_store import (
    ANSWER_ADAPTER,
    Answer,
    CheckAnswer,
    StoredCheck,
    cache,
    cached,
    check,
    check_ids,
    prune,
    quality_key,
    save_answer,
    save_quality,
    save_run,
)
from kmaudit.feedback import (
    FEEDBACK_INSTRUCTIONS,
    FeedbackOut,
    HumanVerdict,
    current,
    disagrees,
    is_open,
    latest,
    liked,
    take_in_checks,
    wants_check,
)
from kmaudit.lines import LineFinder
from kmaudit.models import Claim
from kmaudit.mutate import TEXT_ONLY, Quality, measure
from kmaudit.sections import Target, resolve_target
from kmaudit.steps import (
    INSTALL,
    NEEDS_EXTRA,
    MissingExtra,
    Repository,
    StepResult,
    extra,
    reads,
    reads_key,
    run_check,
)
from kmaudit.store import Store

#: The claim kinds a check can settle; subjective and external claims never get one.
CHECKABLE = ("point", "structural", "broad")
SHOWN_SURVIVORS = 5
#: The most characters of lines ``todo`` shows per claim; the agent reads more itself.
LINES_SHOWN = 1500
# A sentence longer than this, usually a table, is cut to the lines its claim is about.
SENTENCE_SHOWN = 800
_WORD = re.compile(r"[a-z0-9]{3,}")
Status = Literal[
    "holds",
    "not measured",
    "weak",
    "fails",
    "drift",
    "skipped",
    "reason",
    "stale reason",
    "no check",
    "not run",
]
_ITEMS = TypeAdapter(list[object])


class LinesOut(BaseModel):
    """The lines shown for one claim and where they came from."""

    source: str = Field(description="anchors, commands, area, everywhere or nothing.")
    files: list[str]
    text: str


class AnchorOut(BaseModel):
    """One backticked span of a claim and what it resolved to."""

    text: str
    kind: str = Field(description="path, command, flag or name.")
    status: str = Field(
        description="present, gone, never, found, missing, defined, mentioned, tests only or absent."
    )
    where: list[str]


class TodoClaim(BaseModel):
    """A claim with no current check or reason, as ``todo`` hands it out."""

    id: str
    concept: str
    section: str
    kind: str
    quantifier: str
    claim: str
    sentence: str
    how_to_check: str
    anchors: list[AnchorOut]
    lines: LinesOut
    feedback: list[FeedbackOut] = Field(
        default_factory=list,
        description="What a person said about this claim's last answer; read it first, their verdict outranks yours.",
    )


class PendingConcept(BaseModel):
    """A concept with claims to check, so a caller can split the work by concept."""

    concept: str
    path: str = Field(description="The concept file, relative to the repository root.")
    claims: int


class CheckCounts(BaseModel):
    """How the checkable claims stand."""

    claims: int = Field(
        description="Checkable claims (point, structural, broad) in scope."
    )
    checks: int = Field(description="Claims with a stored check.")
    reasons: int = Field(description="Claims with a stored reason that still holds.")
    pending: int = Field(description="Claims with no check and no current reason.")
    pruned: int = Field(
        description="Stored answers dropped because their claim is gone."
    )
    carried: int = Field(
        default=0,
        description="Stored answers moved to the reworded claim of the same sentence.",
    )


class ChecksTodo(BaseModel):
    """What ``kmaudit checks todo`` hands out."""

    instructions: str | None = Field(
        default=None, description="How to write checks; left out with brief."
    )
    answer_schema: dict[str, Any] | None = Field(
        default=None,
        description="The JSON Schema of one answer: a check or a reason; left out with brief.",
    )
    counts: CheckCounts
    concepts: list[PendingConcept]
    claims: list[TodoClaim]
    feedback_instructions: str | None = Field(
        default=None,
        description="How to read feedback and examples; only when the output carries either.",
    )
    examples: list[FeedbackOut] = Field(
        default_factory=list,
        description="Checks and reasons people marked good, with their notes, to learn what works.",
    )
    next: str


class TriedStep(BaseModel):
    """One step of a tried or stored check, and what it saw."""

    holds: bool
    detail: str
    skipped: bool = False


class Tried(BaseModel):
    """What ``try`` found for one draft."""

    claim: str
    kind: Literal["check", "reason", "invalid"]
    holds: bool | None = None
    steps: list[TriedStep] = Field(default_factory=list)
    weak: bool | None = None
    mutants: int | None = None
    killed: int | None = None
    missed: list[str] = Field(
        default_factory=list, description="Changes the check did not notice."
    )
    error: str | None = None


class Stored(BaseModel):
    """One answer ``submit`` stored."""

    claim: str
    kind: Literal["check", "reason"]
    status: Status
    mutants: int | None = None
    killed: int | None = None


class Refused(BaseModel):
    """One answer ``submit`` refused, with the fix."""

    claim: str | None
    reason: str


class SubmitChecks(BaseModel):
    """What ``kmaudit checks submit`` stored and refused."""

    stored: list[Stored] = Field(default_factory=list)
    refused: list[Refused] = Field(default_factory=list)


class RunRow(BaseModel):
    """One claim's status after ``run``."""

    claim: str
    concept: str
    status: Status
    rerun: bool = Field(description="Whether its steps ran this time.")
    measured: bool = Field(
        description="Whether its mutation score was measured this time."
    )
    detail: str = ""


class RunResult(BaseModel):
    """What ``kmaudit checks run`` found."""

    counts: dict[str, int]
    rerun: int
    measured: int
    claims: list[RunRow]


class ListRow(BaseModel):
    """One claim's stored check status, as ``list`` shows it."""

    claim: str
    concept: str
    text: str
    status: Status
    strength: str | None = None
    why: str | None = None
    drift: str | None = None
    reason: str | None = None
    quality: str | None = Field(
        default=None, description="killed/mutants, or not measured."
    )
    human: HumanVerdict | None = Field(
        default=None,
        description="A person's verdict on the claim, while the files the judged answer read are unchanged.",
    )
    disagrees: bool = Field(
        default=False,
        description="Whether the status says the opposite of the person's verdict.",
    )


class ListChecks(BaseModel):
    """What ``kmaudit checks list`` reads."""

    counts: dict[str, int]
    claims: list[ListRow]


def _checkable(store: Store, target: Target) -> list[Claim]:
    """The checkable claims in the target's scope, one per id."""
    seen: dict[str, Claim] = {}
    for c in store.claims(target.concepts):
        if c.kind in CHECKABLE and c.id not in seen:
            seen[c.id] = c
    return list(seen.values())


def _evidence(repo: Repository, store: Store) -> Evidence:
    """The repository's evidence for anchors, with the CLI help walk cached in the store."""
    return Evidence(
        repo, cache=(lambda k: cached(store, k), lambda k, v: cache(store, k, v))
    )


def _concept_text(target: Target, concept: str) -> str:
    """A concept file's text, or empty when it is gone."""
    try:
        return (target.bundle / f"{concept}.md").read_text(encoding="utf-8")
    except OSError:
        return ""


def _words(text: str) -> set[str]:
    """The lower-case words of three or more characters in ``text``, a trailing s dropped."""
    return {w.removesuffix("s") for w in _WORD.findall(text.lower())}


def _focus(claim: Claim) -> str:
    """The part of a claim's sentence the claim is about.

    A sentence up to ``SENTENCE_SHOWN`` characters comes back whole. A longer
    one, usually a markdown table the splitter keeps as one sentence, is cut
    to its first line (a table's header, with the separator after it) and the
    lines sharing the most words with the claim, so a claim from one row does
    not carry the whole table and every span in it.
    """
    sentence = claim.sentence
    if len(sentence) <= SENTENCE_SHOWN:
        return sentence
    lines = sentence.splitlines()
    words = _words(claim.claim)
    scores = [len(words & _words(line)) for line in lines]
    best = max(scores, default=0)
    if best == 0:
        return sentence[:SENTENCE_SHOWN] + " ..."
    keep = {0} | {i for i, score in enumerate(scores) if score == best}
    if len(lines) > 1 and set(lines[1].strip()) <= set("|-: "):
        keep.add(1)
    return "\n".join(lines[i] for i in sorted(keep)[:5])


def _anchors(evidence: Evidence, claim: Claim) -> list[Anchor]:
    """Resolve each backticked span of a claim, or of the part of its sentence it is about when it has none."""
    spans = SPAN.findall(claim.claim) or SPAN.findall(_focus(claim))
    commands = claim_commands(evidence, spans)
    return [resolve(evidence, s, commands) for s in spans]


def _lines(
    finder: "LineFinder",
    target: Target,
    claim: Claim,
    anchors: list[Anchor],
    siblings: list[str],
) -> LinesOut:
    """The lines shown for one claim, found with one ``LineFinder`` per verb so its keyword index is built once."""
    found = finder.find(
        claim.claim,
        _focus(claim),
        anchors,
        _concept_text(target, claim.concept),
        siblings,
    )
    return LinesOut(source=found.source, files=found.files, text=found.text)


def _reason_reads(repo: Repository, lines: LinesOut) -> dict[str, str]:
    """The files a reason goes stale on: those the claim's anchors named, not keyword-search windows.

    A reason found by keyword search would go stale on every edit to any file
    a window came from; only the files the claim names are kept, so the
    reason stays until its claim, or a file it names, changes.
    """
    if lines.source != "anchors":
        return {}
    return {p: repo.sha(p) for p in lines.files}


def _reason_status(stored: StoredCheck, repo: Repository) -> Status:
    """``reason``, or ``stale reason`` when a file its lines came from changed, so ``todo`` hands it out again."""
    return (
        "reason"
        if all(repo.sha(p) == s for p, s in stored.reads.items())
        else "stale reason"
    )


def _reason_current(store: Store, repo: Repository, claim_id: str) -> bool:
    """Whether a stored reason still holds: the files its lines came from are unchanged."""
    stored = check(store, claim_id)
    return stored is not None and all(repo.sha(p) == s for p, s in stored.reads.items())


def todo(path: Path, limit: int | None = None, brief: bool = False) -> ChecksTodo:
    """List the checkable claims with no current check or reason, each with its anchors and lines.

    With ``brief``, the instructions and answer schema are left out, for a
    caller that already has them from an earlier round.

    Raises
    ------
    AuditError
        If ``path`` names no bundle.
    """
    target = resolve_target(path)
    repo = Repository(target.root)
    with Store(target.root) as store:
        pruned = prune(store)
        claims = _checkable(store, target)
        kinds = {
            cid: (s.kind if (s := check(store, cid)) else None)
            for cid in check_ids(store)
        }
        said = {
            cid: f
            for (cid, on), f in latest(store, [c.id for c in claims]).items()
            if on == "check"
        }
        asked = {
            c.id
            for c in claims
            if c.id in said
            and wants_check(
                said[c.id],
                status_row(store, repo, c).status,
                current(repo, said[c.id]),
            )
        }
        pending = [c for c in claims if c.id in asked] + [
            c
            for c in claims
            if c.id not in asked
            and (
                kinds.get(c.id) is None
                or (kinds[c.id] == "reason" and not _reason_current(store, repo, c.id))
            )
        ]
        shown = pending if limit is None else pending[:limit]
        examples = liked(store, "check")
        evidence = _evidence(repo, store) if shown else None
    out: list[TodoClaim] = []
    if evidence is not None:
        finder = LineFinder(repo, limit=LINES_SHOWN)
        by_concept: dict[str, list[str]] = {}
        resolved = {c.id: _anchors(evidence, c) for c in shown}
        for c in shown:
            by_concept.setdefault(c.concept, []).extend(located(resolved[c.id], repo))
        for c in shown:
            siblings = [
                f
                for f in by_concept[c.concept]
                if f not in located(resolved[c.id], repo)
            ]
            anchors = resolved[c.id]
            lines = _lines(finder, target, c, anchors, siblings)
            out.append(
                TodoClaim(
                    id=c.id,
                    concept=c.concept,
                    section=c.section,
                    kind=c.kind,
                    quantifier=c.quantifier,
                    claim=c.claim,
                    sentence=_focus(c),
                    how_to_check=c.how_to_check,
                    anchors=[AnchorOut(**asdict(a)) for a in anchors],
                    lines=lines,
                    feedback=[said[c.id].out()]
                    if c.id in said and is_open(said[c.id])
                    else [],
                )
            )
    per = Counter(c.concept for c in pending)
    root = target.root.resolve()
    return ChecksTodo(
        instructions=None if brief else INSTRUCTIONS,
        answer_schema=None if brief else ANSWER_ADAPTER.json_schema(),
        counts=CheckCounts(
            claims=len(claims),
            checks=sum(1 for c in claims if kinds.get(c.id) == "check"),
            reasons=sum(1 for c in claims if kinds.get(c.id) == "reason")
            - sum(1 for c in pending if kinds.get(c.id) == "reason"),
            pending=len(pending),
            pruned=pruned.dropped,
            carried=pruned.carried,
        ),
        concepts=[
            PendingConcept(
                concept=concept,
                path=(target.bundle.resolve() / f"{concept}.md")
                .relative_to(root)
                .as_posix(),
                claims=n,
            )
            for concept, n in per.items()
        ],
        claims=out,
        feedback_instructions=FEEDBACK_INSTRUCTIONS
        if examples or any(c.feedback for c in out)
        else None,
        examples=examples,
        next="kmaudit checks try -, then kmaudit checks submit -",
    )


def _first_error(error: ValidationError) -> str:
    """The first validation error as 'field: message'."""
    first = error.errors()[0]
    where = ".".join(str(p) for p in first["loc"]) or "answer"
    return f"{where}: {first['msg']}"


def _parse(text: str, verb: str) -> list[object]:
    """The answers in ``text``: one JSON object or a list of them.

    Raises
    ------
    AuditError
        If ``text`` is not JSON, or holds no answer.
    """
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise AuditError(
            f"the answer is not JSON ({error.msg} at line {error.lineno}); "
            f"pipe a list of answers to kmaudit checks {verb} -, as kmaudit checks todo --json describes"
        ) from error
    items = _ITEMS.validate_python(data if isinstance(data, list) else [data])
    if not items:
        raise AuditError(
            f"the answer list is empty; pipe the answers to kmaudit checks {verb} -"
        )
    return items


def _label(item: object) -> str | None:
    """The claim id an answer names, if it names one."""
    value = item.get("claim") if isinstance(item, dict) else None
    return value if isinstance(value, str) else None


def _missing_extra(answer: CheckAnswer) -> str | None:
    """The refusal for a check whose code or query steps need the extra that is not installed, else None."""
    for step in answer.steps:
        if isinstance(step, NEEDS_EXTRA):
            try:
                extra("ast_grep_py" if step.op == "code" else "jmespath")
            except MissingExtra:
                return (
                    f"claim {answer.claim}: a {step.op} step needs kmaudit, which is not installed, "
                    f"so its changes cannot be measured; {INSTALL}, or use other steps"
                )
    return None


def _survivors(quality: Quality) -> str:
    """The changes a weak check missed, for its refusal."""
    if TEXT_ONLY in quality.survived:
        return "it matched only comments or docstrings"
    missed = [s for s in quality.survived if s != TEXT_ONLY]
    more = (
        f" and {len(missed) - SHOWN_SURVIVORS} more"
        if len(missed) > SHOWN_SURVIVORS
        else ""
    )
    return f"it noticed none of {quality.mutants} changes, such as {'; '.join(missed[:SHOWN_SURVIVORS])}{more}"


def try_answers(path: Path, text: str) -> list[Tried]:
    """Run each draft and measure the ones that hold; writes nothing, not even the store.

    Raises
    ------
    AuditError
        If ``text`` is not JSON, or ``path`` names no bundle.
    """
    target = resolve_target(path)
    repo = Repository(target.root)
    out: list[Tried] = []
    for item in _parse(text, "try"):
        label = _label(item) or "?"
        try:
            answer = ANSWER_ADAPTER.validate_python(item)
        except ValidationError as error:
            out.append(Tried(claim=label, kind="invalid", error=_first_error(error)))
            continue
        if not isinstance(answer, CheckAnswer):
            out.append(Tried(claim=answer.claim, kind="reason"))
            continue
        holds, results = run_check(repo, answer.steps)
        tried = Tried(
            claim=answer.claim,
            kind="check",
            holds=holds,
            steps=[TriedStep(**r.model_dump()) for r in results],
        )
        if holds:
            quality = measure(repo, answer.steps, [r.detail for r in results])
            tried.weak = quality.weak
            tried.mutants, tried.killed = quality.mutants, quality.killed
            tried.missed = quality.survived[:10]
        out.append(tried)
    return out


def submit(path: Path, text: str, by: str = "agent") -> SubmitChecks:
    """Validate, run and measure each answer, and store the ones that pass; refusals keep the rest.

    It refuses a weak check, a failing check without ``drift``, a check that
    holds with ``drift``, an unknown claim id, a code or query step without
    the extra, and a malformed answer.

    Raises
    ------
    AuditError
        If ``text`` is not JSON, or ``path`` names no bundle.
    """
    target = resolve_target(path)
    repo = Repository(target.root)
    result = SubmitChecks()
    items = _parse(text, "submit")
    with Store(target.root) as store:
        known = {c.id: c for c in store.claims() if c.kind in CHECKABLE}
        evidence: Evidence | None = None
        finder: LineFinder | None = None
        for item in items:
            label = _label(item)
            try:
                answer: Answer = ANSWER_ADAPTER.validate_python(item)
            except ValidationError as error:
                result.refused.append(
                    Refused(
                        claim=label,
                        reason=f"malformed answer for claim {label or '?'}: {_first_error(error)}; "
                        "fix it to the answer_schema kmaudit checks todo --json gives and submit again",
                    )
                )
                continue
            claim = known.get(answer.claim)
            if claim is None:
                result.refused.append(
                    Refused(
                        claim=answer.claim,
                        reason=f"unknown or stale claim id {answer.claim!r} (its text changed or it is not "
                        "checkable); run kmaudit checks todo for the current ids",
                    )
                )
                continue
            if not isinstance(answer, CheckAnswer):
                evidence = evidence or _evidence(repo, store)
                finder = finder or LineFinder(repo, limit=LINES_SHOWN)
                lines = _lines(finder, target, claim, _anchors(evidence, claim), [])
                save_answer(store, answer, _reason_reads(repo, lines), by, claim)
                result.stored.append(
                    Stored(claim=answer.claim, kind="reason", status="reason")
                )
                continue
            if (refusal := _missing_extra(answer)) is not None:
                result.refused.append(Refused(claim=answer.claim, reason=refusal))
                continue
            refusal, stored = _store_check(store, repo, answer, by, claim)
            if refusal is not None:
                result.refused.append(Refused(claim=answer.claim, reason=refusal))
            elif stored is not None:
                result.stored.append(stored)
        take_in_checks(store, [s.claim for s in result.stored])
    return result


def _store_check(
    store: Store, repo: Repository, answer: CheckAnswer, by: str, claim: Claim
) -> tuple[str | None, Stored | None]:
    """Run and measure one check; store it, or return the refusal naming the fix."""
    holds, results = run_check(repo, answer.steps)
    if not holds and answer.drift is None:
        failing = next((r for r in results if not r.holds), None)
        detail = failing.detail[:200] if failing else "no step held"
        return (
            (
                f"claim {answer.claim}: the check fails ({detail}); fix the steps with kmaudit checks try, "
                "or set drift to what the code does if the claim is wrong"
            ),
            None,
        )
    if not holds and any(r.detail.startswith("could not run") for r in results):
        broken = next(r for r in results if r.detail.startswith("could not run"))
        return (
            (
                f"claim {answer.claim}: a step {broken.detail[:200]}, so the check cannot show drift; "
                "fix the step with kmaudit checks try"
            ),
            None,
        )
    if holds and answer.drift is not None:
        return (
            (
                f"claim {answer.claim}: drift is set but the check holds; drop drift, or fix the steps so they "
                "test the claim"
            ),
            None,
        )
    quality: Quality | None = None
    if holds:
        quality = measure(repo, answer.steps, [r.detail for r in results])
        if quality.weak:
            return (
                (
                    f"claim {answer.claim}: weak check, {_survivors(quality)}; pin a step to the code that does "
                    "what the claim says, test it with kmaudit checks try, or give a reason"
                ),
                None,
            )
    now = reads(repo, answer.steps)
    key = reads_key(now)
    save_answer(store, answer, now, by, claim)
    save_run(store, answer.claim, now, key, holds, results)
    if quality is not None:
        save_quality(store, answer.claim, quality_key(answer.steps, key), quality)
    return None, Stored(
        claim=answer.claim,
        kind="check",
        status=_status(holds, False, answer.drift, quality),
        mutants=None if quality is None else quality.mutants,
        killed=None if quality is None else quality.killed,
    )


def _status(
    holds: bool | None, skipped: bool, drift: str | None, quality: Quality | None
) -> Status:
    """A stored check's status from its last run and score."""
    if holds is None:
        return "not run"
    if skipped:
        return "skipped"
    if holds:
        if quality is not None and quality.weak:
            return "weak"
        return (
            "not measured" if quality is not None and quality.mutants == 0 else "holds"
        )
    return "drift" if drift is not None else "fails"


def run(path: Path, everything: bool = False) -> RunResult:
    """Rerun the stored checks whose reads changed (every one with ``everything``) and re-measure where the key moved.

    Raises
    ------
    AuditError
        If ``path`` names no bundle.
    """
    target = resolve_target(path)
    repo = Repository(target.root)
    rows: list[RunRow] = []
    with Store(target.root) as store:
        prune(store)
        for claim in _checkable(store, target):
            stored = check(store, claim.id)
            if stored is None:
                rows.append(
                    RunRow(
                        claim=claim.id,
                        concept=claim.concept,
                        status="no check",
                        rerun=False,
                        measured=False,
                    )
                )
                continue
            if stored.kind == "reason":
                rows.append(
                    RunRow(
                        claim=claim.id,
                        concept=claim.concept,
                        status=_reason_status(stored, repo),
                        rerun=False,
                        measured=False,
                    )
                )
                continue
            now = reads(repo, stored.steps)
            key = reads_key(now)
            rerun = everything or stored.skipped or stored.reads_key != key
            holds, skipped, results = stored.holds, stored.skipped, stored.results
            if rerun:
                holds, results = run_check(repo, stored.steps)
                skipped = any(r.skipped for r in results)
                save_run(store, claim.id, now, key, holds, results)
            measured = False
            quality = stored.quality
            if holds and not skipped:
                qkey = quality_key(stored.steps, key)
                if qkey != stored.quality_key:
                    quality = measure(repo, stored.steps, [r.detail for r in results])
                    save_quality(store, claim.id, qkey, quality)
                    measured = True
            status = _status(holds, skipped, stored.drift, quality)
            detail = _detail(status, results, quality)
            rows.append(
                RunRow(
                    claim=claim.id,
                    concept=claim.concept,
                    status=status,
                    rerun=rerun,
                    measured=measured,
                    detail=detail,
                )
            )
    return RunResult(
        counts=dict(Counter(r.status for r in rows)),
        rerun=sum(r.rerun for r in rows),
        measured=sum(r.measured for r in rows),
        claims=rows,
    )


def _detail(status: Status, results: list[StepResult], quality: Quality | None) -> str:
    """One line on why a check has its status."""
    if status in ("fails", "drift", "skipped"):
        failing = next((r for r in results if not r.holds), None)
        return failing.detail[:200] if failing else ""
    if status == "weak" and quality is not None:
        return _survivors(quality)
    return ""


def list_checks(path: Path, status: str | None = None) -> ListChecks:
    """Each checkable claim's stored status, strength and why, from the last run; ``status`` filters.

    Raises
    ------
    AuditError
        If ``path`` names no bundle.
    """
    target = resolve_target(path)
    repo = Repository(target.root)
    with Store(target.root) as store:
        rows = [status_row(store, repo, claim) for claim in _checkable(store, target)]
    shown = [r for r in rows if status is None or r.status == status]
    return ListChecks(counts=dict(Counter(r.status for r in rows)), claims=shown)


def status_row(store: Store, repo: Repository, claim: Claim) -> ListRow:
    """One checkable claim's stored status, strength and why, with a person's verdict while it still applies."""
    stored = check(store, claim.id)
    said = latest(store, [claim.id]).get((claim.id, "check"))
    human = said.verdict if said is not None and current(repo, said) else None
    if stored is None:
        row = ListRow(
            claim=claim.id, concept=claim.concept, text=claim.claim, status="no check"
        )
    elif stored.kind == "reason":
        row = ListRow(
            claim=claim.id,
            concept=claim.concept,
            text=claim.claim,
            status=_reason_status(stored, repo),
            reason=stored.reason,
        )
    else:
        q = stored.quality
        row = ListRow(
            claim=claim.id,
            concept=claim.concept,
            text=claim.claim,
            status=_status(stored.holds, stored.skipped, stored.drift, q),
            strength=stored.strength,
            why=stored.why,
            drift=stored.drift,
            quality=None
            if q is None
            else (f"{q.killed}/{q.mutants}" if q.mutants else "not measured"),
        )
    row.human = human
    row.disagrees = disagrees(human, row.status)
    return row


def claim_row(path: Path, claim_id: str) -> ListRow | None:
    """One claim's row as ``list`` shows it, or None when the claim is not stored or not checkable."""
    target = resolve_target(path)
    repo = Repository(target.root)
    with Store(target.root) as store:
        found = store.claim(claim_id)
        if found is None or found.kind not in CHECKABLE:
            return None
        return status_row(store, repo, found)


def claim_lines(path: Path, claim_id: str) -> str:
    """The lines ``todo`` would show for one claim, for a decision model to judge it on.

    Raises
    ------
    AuditError
        If ``path`` names no bundle, or the store has no such claim.
    """
    target = resolve_target(path)
    repo = Repository(target.root)
    with Store(target.root) as store:
        found = store.claim(claim_id)
        if found is None:
            raise AuditError(
                f"no stored claim {claim_id!r}; list them with kmaudit claims list --claims"
            )
        return lines_for(store, repo, target, [found])[claim_id].text


def lines_for(
    store: Store, repo: Repository, target: Target, claims: list[Claim]
) -> dict[str, LinesOut]:
    """The lines ``todo`` would show for each claim and the files they came from, by claim id, with one keyword index."""
    if not claims:
        return {}
    evidence = _evidence(repo, store)
    finder = LineFinder(repo, limit=LINES_SHOWN)
    return {c.id: _lines(finder, target, c, _anchors(evidence, c), []) for c in claims}
