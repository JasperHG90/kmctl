"""The checks stage: from stored claims to checks that run against the code with no model.

``Checks`` works on one project's database and repository. Each claim ends in one of three kinds:

- settled: the anchors decide it with no model (a file no longer exists, a flag's default);
- check: steps the two-call writer wrote (the searching agent too, when ``[checks] agent`` is on);
- reason: why no step can test it (history, intent, an outside service, nothing to show).

Nothing is written or run twice for nothing. A claim's id follows its text, so a changed claim is a new claim. Each
check records the files its steps read, with their content hashes; a run reuses the last result while those are
unchanged. A check is written again only when it is new, when the decision model said its last failure was the check's
fault, or (for a reason or a settled claim) when a file it was decided from changed.
"""

import asyncio
import hashlib
import json
import pathlib as plb
import subprocess
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

import httpx
import openai
from langchain_core.language_models import BaseChatModel
from langsmith import traceable
from pydantic import TypeAdapter, ValidationError

from audit_cli.checks.anchors import Evidence, Settled, located, settle
from audit_cli.checks.decide import Decider, DecisionError, asked_key
from audit_cli.checks.lines import LineFinder
from audit_cli.checks.mutate import TEXT_ONLY, measure
from audit_cli.checks.mutate import VERSION as MUTATION_VERSION
from audit_cli.checks.steps import Repository, Step, reads, reads_key, run_check
from audit_cli.checks.twocall import PROMPT as TWOCALL_PROMPT
from audit_cli.checks.twocall import Answer, Item, Spent, fix_group, strengthen_group, write_group
from audit_cli.checks.writer import PROMPT_HASH as AGENT_PROMPT_HASH
from audit_cli.checks.writer import Budget, ClaimInput, NoCheck, write_checks
from audit_cli.config import Config
from audit_cli.db import CheckQuality, CheckResult, Store, StoredCheck, StoredClaim, Triage
from audit_cli.logs import get_logger

log = get_logger("checks.pipeline")
STEPS = TypeAdapter(list[Step])
CALL_ERRORS = (openai.OpenAIError, httpx.HTTPError, TimeoutError)  # a model call that failed: 5xx, timeout, network
TWOCALL_HASH = hashlib.sha256(TWOCALL_PROMPT.encode()).hexdigest()[:8]
Status = Literal["new", "unrun", "changed", "failing", "rewrite", "up to date"]
TARGET_KEYS = {
    "file": ("path",),
    "grep": ("paths", "pattern"),
    "code": ("paths", "pattern"),
    "query": ("paths", "query"),
    "definition": ("paths", "name"),
    "imports": ("path", "module"),
    "help": ("command", "pattern"),
}
EXPECT_KEYS = ("expect", "value", "present", "exists", "defined", "imported")


@dataclass
class ClaimState:
    """One claim's place in the stage: its stored check and last result, and what it needs next."""

    claim: StoredClaim
    status: Status
    check: StoredCheck | None = None
    result: CheckResult | None = None
    reads_now: dict[str, str] = field(default_factory=dict)


@dataclass
class Stage:
    """What one stage of a command did and spent."""

    name: str
    claims: int = 0
    calls: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    tokens_cached: int = 0
    seconds: float = 0.0

    @classmethod
    def of(cls, name: str, claims: int, spent: Spent, seconds: float) -> "Stage":
        """Return a stage from what its calls spent."""
        return cls(name, claims, spent.calls, spent.tokens_in, spent.tokens_out, spent.tokens_cached, round(seconds, 1))


def commit_sha(root: plb.Path) -> str:
    """Return the repository's HEAD commit, or "" when it has none."""
    out = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    return out.stdout.strip() if out.returncode == 0 else ""


def answer_keys(question: str, model: str, state: dict[str, Any]) -> set[str]:
    """Return the keys an answer to this question about this state may be stored under: with the model that answered
    (a new model asks again), or without one, as answers stored before the model was part of the key were."""
    return {asked_key(f"{question}:{model}", state), asked_key(question, state)}


def failure_state(claim: StoredClaim, check: StoredCheck, result: CheckResult) -> dict[str, Any]:
    """Return what the decision model is shown about a failed check: the claim, the check's why and what it saw."""
    return {
        "claim": claim.claim,
        "sentence": claim.sentence,
        "check_why": check.why,
        "steps": [
            {"step": step, "held": seen.get("holds"), "saw": str(seen.get("detail", ""))[:300]}
            for step, seen in zip(check.steps, result.results, strict=False)
        ],
    }


def expectation_changed(old: list[dict[str, Any]], saw: list[dict[str, Any]], new: list[dict[str, Any]]) -> bool:
    """Whether a rewritten check expects something else of a step that failed: same op and target, other expectation.

    That is how a fix call bends drift into a pass ("the publish job is skipped" failed on ``if: !cancelled()``, and
    the fix asserted ``!cancelled()``), so such a check is flagged for a person.
    """
    failed = [step for step, seen in zip(old, saw, strict=False) if not seen.get("holds")]
    for before in failed:
        keys = TARGET_KEYS.get(str(before.get("op")), ())
        for after in new:
            same_target = after.get("op") == before.get("op") and all(after.get(k) == before.get(k) for k in keys)
            if same_target and any(after.get(k) != before.get(k) for k in EXPECT_KEYS):
                return True
    return False


class Checks:
    """The checks stage over one project: plan, write, run and triage.

    Parameters
    ----------
    store :
        The project's database, holding its claims.
    repo :
        The repository the claims describe.
    config :
        The settings.
    bundle :
        The bundle folder, to read each concept's text and sources.
    concepts :
        The concepts in scope, or None for every one.
    """

    def __init__(
        self, store: Store, repo: Repository, config: Config, bundle: plb.Path, concepts: set[str] | None = None
    ) -> None:
        self.store = store
        self.repo = repo
        self.config = config
        self.bundle = bundle
        self.concepts = concepts
        self.commit = commit_sha(repo.root)
        self._evidence: Evidence | None = None
        self._finder: LineFinder | None = None
        self.spent: list[Spent] = []  # the write's model calls so far, for a progress report

    @property
    def evidence(self) -> Evidence:
        """The repository's evidence for anchors, built on first use; its CLI walk is cached in the database."""
        if self._evidence is None:
            self._evidence = Evidence(self.repo, cache=(self.store.cached, self.store.cache))
        return self._evidence

    @property
    def finder(self) -> LineFinder:
        """The line finder, built on first use."""
        if self._finder is None:
            self._finder = LineFinder(self.repo, self.config.checks.max_lines_chars)
        return self._finder

    def claims(self) -> list[StoredClaim]:
        """Return the claims in scope, once per claim id, leaving out claims a correction overturned."""
        overturned = {link.claim_id for link in self.store.correction_links() if link.claim_id}
        seen: dict[str, StoredClaim] = {}
        for claim in self.store.claims():
            if self.concepts is not None and claim.concept not in self.concepts:
                continue
            if claim.claim_id in overturned or claim.claim_id in seen:
                continue
            seen[claim.claim_id] = claim
        return list(seen.values())

    def _reads_now(self, check: StoredCheck) -> dict[str, str]:
        """Return the files a stored check reads now: its steps' matches, or for a reason the files it was given."""
        if check.kind == "check":
            try:
                return reads(self.repo, STEPS.validate_python(check.steps))
            except ValidationError:
                return {}
        return {path: self.repo.sha(path) for path in check.reads}

    def plan(self) -> list[ClaimState]:
        """Return every claim in scope with what it needs next. Calls no model and writes nothing."""
        checks, results, triage = self.store.checks(), self.store.results(), self.store.triage()
        states = []
        for claim in self.claims():
            check, result = checks.get(claim.claim_id), results.get(claim.claim_id)
            if check is None:
                states.append(ClaimState(claim, "new"))
                continue
            now = self._reads_now(check)
            status: Status
            if check.kind == "check" and result is None:
                status = "unrun"
            elif now != check.reads:
                status = "changed"
            elif check.kind == "check" and result is not None and not result.holds:
                verdict = triage.get(claim.claim_id)
                keys = answer_keys("failure", verdict.model if verdict else "", failure_state(claim, check, result))
                wrong = verdict is not None and verdict.asked_key in keys and verdict.verdict == "check_wrong"
                status = "rewrite" if wrong else "failing"
            else:
                status = "up to date"
            states.append(ClaimState(claim, status, check, result, now))
        return states

    def prune(self) -> int:
        """Delete the checks of claims no longer stored (changed or removed) and return how many went."""
        return self.store.prune_checks({c.claim_id for c in self.store.claims()})

    def _run(self, claim_id: str, steps: list[dict[str, Any]]) -> CheckResult:
        """Run a check now, store its result and reads, and return the result."""
        parsed = STEPS.validate_python(steps)
        holds, results = run_check(self.repo, parsed)
        files = reads(self.repo, parsed)
        result = CheckResult(
            claim_id=claim_id,
            holds=holds,
            results=[r.model_dump() for r in results],
            reads_key=reads_key(files),
            commit_sha=self.commit,
        )
        self.store.save_result(result)
        self.store.set_reads(claim_id, files)
        self._measure(claim_id, steps, result)
        return result

    def _measure(self, claim_id: str, steps: list[dict[str, Any]], result: CheckResult) -> None:
        """Mutation-test a holding check, unless it was already tested on the same steps and the same code."""
        if not result.holds:
            return
        key = hashlib.sha256(json.dumps([steps, result.reads_key, MUTATION_VERSION]).encode()).hexdigest()[:16]
        old = self.store.quality_of(claim_id)
        if old is not None and old.mutant_key == key:
            return
        quality = measure(self.repo, STEPS.validate_python(steps), [str(r.get("detail", "")) for r in result.results])
        self.store.save_mutation(claim_id, quality.mutants, quality.killed, quality.survived, key)

    def _save_settled(self, claim: StoredClaim, s: Settled) -> CheckResult | None:
        """Store a claim the anchors settle, with its verdict and result; a claim they no longer settle loses its
        settled check, so the next write sends it to a model. Returns the result, or None when it lost its check."""
        if s.verdict is None:
            self.store.delete_check(claim.claim_id)
            return None
        self.store.save_check(
            StoredCheck(
                claim_id=claim.claim_id,
                kind="settled",
                settled=s.verdict,
                why=f"settled by the {s.rule} rule from: " + ", ".join(f"{a.text} ({a.status})" for a in s.anchors),
                writer="settle",
                commit_sha=self.commit,
                reads={p: self.repo.sha(p) for p in located(s.anchors, self.repo)},
            )
        )
        result = CheckResult(
            claim_id=claim.claim_id, holds=s.verdict, results=[], reads_key="settled", commit_sha=self.commit
        )
        self.store.save_result(result)
        return result

    def _settled(self, claims: list[StoredClaim]) -> dict[str, Settled]:
        """Resolve every claim's anchors (the slow part runs once) and return what each settles to."""
        return {c.claim_id: settle(self.evidence, c.claim) for c in claims}

    def _lines(
        self, claim: StoredClaim, settled: dict[str, Settled], claims: list[StoredClaim]
    ) -> tuple[str, list[str]]:
        """Return the lines for a claim and the files they come from."""
        concept = self.bundle / f"{claim.concept}.md"
        text = concept.read_text(errors="replace") if concept.is_file() else ""
        siblings = [
            f
            for other in claims
            if other.concept == claim.concept and other.claim_id != claim.claim_id
            for f in located(settled[other.claim_id].anchors, self.repo)
        ]
        found = self.finder.find(claim.claim, claim.sentence, settled[claim.claim_id].anchors, text, siblings)
        return found.text, found.files

    def _groups(
        self, items: list[tuple[StoredClaim, str, list[str]]]
    ) -> list[list[tuple[StoredClaim, str, list[str]]]]:
        """Group claims by the first file their lines come from, at most ``group_size`` a group."""
        by_file: dict[str, list[tuple[StoredClaim, str, list[str]]]] = {}
        for item in items:
            by_file.setdefault(item[2][0] if item[2] else item[0].claim_id, []).append(item)
        size = self.config.checks.group_size
        return [group[i : i + size] for group in by_file.values() for i in range(0, len(group), size)]

    @traceable(run_type="chain", name="checks write")
    async def write(
        self,
        llm: BaseChatModel,
        rewrite_failing: bool = False,
        only: set[str] | None = None,
        on_group: Callable[[int], object] | None = None,
    ) -> dict[str, Any]:
        """Write checks for the claims that need one and run them; return what was done and spent per stage.

        The claims written: new ones, ones the decision model said have a wrong check, reasons and settled claims whose
        files changed, and with ``rewrite_failing`` every failing check. With ``only``, just the claims whose ids start
        with one of those, whatever their state.
        """
        started = time.monotonic()
        pruned = self.prune()
        plan = self.plan()
        wanted = {"new", "rewrite"} | ({"failing"} if rewrite_failing else set())
        if only:  # claims named by id (or a prefix) are written again whatever their state
            plan = [s for s in plan if any(s.claim.claim_id.startswith(i) for i in only)]
            wanted = {"new", "unrun", "changed", "failing", "rewrite", "up to date"}
        targets = [
            s.claim
            for s in plan
            if s.status in wanted or s.status == "changed" and s.check is not None and s.check.kind != "check"
        ]
        report: dict[str, Any] = {"claims": len(plan), "to_write": len(targets), "pruned": pruned, "stages": []}
        if not targets:
            report["seconds"] = round(time.monotonic() - started, 1)
            return report
        stage_start = time.monotonic()
        everyone = self.claims()
        settled = self._settled(everyone)
        free = [c for c in targets if settled[c.claim_id].verdict is not None]
        for claim in free:
            self._save_settled(claim, settled[claim.claim_id])
            if on_group is not None:
                on_group(1)
        report["stages"].append(asdict(Stage("settle", len(free), seconds=round(time.monotonic() - stage_start, 1))))
        rest = [c for c in targets if settled[c.claim_id].verdict is None]
        stage_start = time.monotonic()
        lined = [(c, *self._lines(c, settled, everyone)) for c in rest]
        report["stages"].append(asdict(Stage("lines", len(lined), seconds=round(time.monotonic() - stage_start, 1))))
        was_failing = {  # a failing check keeps its place against a reason, unless triage called it wrong
            s.claim.claim_id
            for s in plan
            if s.status != "rewrite"
            and s.check is not None
            and s.check.kind == "check"
            and s.result is not None
            and not s.result.holds
        }
        outcome = await self._write_groups(llm, lined, on_group, report, was_failing)
        report["outcome"] = outcome
        report["seconds"] = round(time.monotonic() - started, 1)
        return report

    async def _write_groups(
        self,
        llm: BaseChatModel,
        lined: list[tuple[StoredClaim, str, list[str]]],
        on_group: Callable[[int], object] | None,
        report: dict[str, Any],
        was_failing: set[str] | None = None,
    ) -> dict[str, int]:
        """Write, run and fix the checks of each group, hand what is left to the agent when on, and store them.

        A claim in ``was_failing`` (sent by ``--rewrite-failing``) keeps its failing check if the new answer is a
        reason; a claim triage called wrong ("rewrite") may take a reason.
        """
        was_failing = was_failing or set()
        limit = asyncio.Semaphore(self.config.concurrency.max_model_calls)
        model = str(getattr(llm, "model_name", "") or getattr(llm, "model", ""))
        spent_write, spent_fix = Spent(), Spent()
        self.spent = [spent_write, spent_fix]
        lines_of = {c.claim_id: (text, files) for c, text, files in lined}
        claims_of = {c.claim_id: c for c, _, _ in lined}
        written: dict[str, tuple[Answer, int]] = {}  # claim id: answer, its share of tokens
        refused_reasons: list[str] = []  # claims whose failing check a fix or the agent tried to swap for a reason
        errors: dict[str, str] = {}  # claim id: why its write or fix call failed
        first: dict[str, tuple[dict[str, Any], CheckResult]] = {}  # claim id: the check that failed and its result

        async def one(group: list[tuple[StoredClaim, str, list[str]]]) -> None:
            """Write one group, run its checks, and send its failures back once."""
            items = [Item(f"c{i}", c.claim_id, c.claim, c.sentence, text) for i, (c, text, _) in enumerate(group, 1)]
            try:
                async with limit:
                    answers, tokens = await write_group(llm, items, spent_write)
            except CALL_ERRORS as error:  # a provider error (a 504, a timeout) loses this group only; it is retried
                errors.update({i.claim_id: f"write call failed: {type(error).__name__}: {error}"[:300] for i in items})
                log.warning("write_group_failed", claims=[i.claim_id for i in items], error=str(error)[:300])
                if on_group is not None:
                    on_group(len(group))
                return
            share = tokens // max(sum(i.label in answers for i in items), 1)  # unanswered claims cost nothing stored
            failing: list[Item] = []
            for item in items:
                answer = answers.get(item.label)
                if answer is None:
                    continue
                written[item.claim_id] = (answer, share)
                if item.claim_id in was_failing:
                    if self._replace_failing(item.claim_id, answer, share, model, lines_of, "twocall"):
                        refused_reasons.append(item.claim_id)
                    continue
                is_check = self._store_check(item.claim_id, answer, share, model, lines_of)
                if is_check and answer.check is not None:
                    steps = [s.model_dump(mode="json") for s in answer.check.steps]
                    result = self._run(item.claim_id, steps)
                    if not result.holds:
                        first[item.claim_id] = (answer.check.model_dump(mode="json"), result)
                        failing.append(
                            Item(
                                item.label,
                                item.claim_id,
                                item.claim,
                                item.sentence,
                                item.lines,
                                check=first[item.claim_id][0],
                                saw=result.results,
                            )
                        )
            if failing and self.config.checks.fix:
                try:
                    async with limit:
                        fixed, fix_tokens = await fix_group(llm, failing, spent_fix)
                except CALL_ERRORS as error:  # the failing checks stay as written; triage still sees them
                    errors.update(
                        {i.claim_id: f"fix call failed: {type(error).__name__}: {error}"[:300] for i in failing}
                    )
                    log.warning("fix_group_failed", claims=[i.claim_id for i in failing], error=str(error)[:300])
                    fixed, fix_tokens = {}, 0
                fix_share = fix_tokens // max(len(failing), 1)
                for item in failing:
                    answer = fixed.get(item.label)
                    if answer is None:
                        continue
                    share = written[item.claim_id][1] + fix_share
                    if self._replace_failing(item.claim_id, answer, share, model, lines_of, "twocall"):
                        refused_reasons.append(item.claim_id)
            if on_group is not None:
                on_group(len(group))

        stage_start = time.monotonic()
        await asyncio.gather(*(one(g) for g in self._groups(lined)))
        report["stages"].append(asdict(Stage.of("write", len(lined), spent_write, time.monotonic() - stage_start)))
        report["errors"] = errors
        report["stages"].append(asdict(Stage.of("fix", len(first), spent_fix, 0.0)))
        if self.config.checks.agent:
            refused_reasons += await self._agent(llm, claims_of, lines_of, report)
        results = self.store.results()
        checks = self.store.checks()
        ids = list(claims_of)
        return {
            "holds": sum(1 for i in ids if i in results and results[i].holds and checks[i].kind == "check"),
            "fails": sum(1 for i in ids if i in results and not results[i].holds and checks[i].kind == "check"),
            "reasons": sum(1 for i in ids if i in checks and checks[i].kind == "reason"),
            "unanswered": sum(1 for i in ids if i not in checks),
            "fixed_to_hold": sum(1 for i in first if i in results and results[i].holds),
            "expectation_changed": sum(1 for i in ids if i in checks and checks[i].expectation_changed),
            "reason_refused": len(set(refused_reasons)),
            "errors": len(errors),
        }

    def _replace_failing(
        self,
        claim_id: str,
        answer: Answer,
        tokens: int,
        model: str,
        lines_of: dict[str, tuple[str, list[str]]],
        writer: str,
    ) -> bool:
        """Store a new answer for a claim whose check failed; return True when it was a reason, which is refused.

        A failing check may have found drift, so a reason ("no step can test it") never replaces it: the failing check
        and its result stay for triage. A new check is stored and run, flagged when it expects something else of a
        step that failed.
        """
        old = self.store.checks().get(claim_id)
        old_result = self.store.results().get(claim_id)
        if answer.check is None or not answer.check.steps:
            return answer.no_check is not None
        new_steps = [s.model_dump(mode="json") for s in answer.check.steps]
        changed = (
            old is not None and old_result is not None and expectation_changed(old.steps, old_result.results, new_steps)
        )
        if self._store_check(claim_id, answer, tokens, model, lines_of, changed, writer):
            self._run(claim_id, new_steps)
        return False

    def _store_check(
        self,
        claim_id: str,
        answer: Answer,
        tokens: int,
        model: str,
        lines_of: dict[str, tuple[str, list[str]]],
        changed: bool = False,
        writer: str = "twocall",
    ) -> bool:
        """Store an answer as a check or a reason; return whether it is a check whose steps can be stored."""
        prompt = TWOCALL_HASH if writer == "twocall" else AGENT_PROMPT_HASH
        if answer.check is not None and answer.check.steps:
            self.store.save_check(
                StoredCheck(
                    claim_id=claim_id,
                    kind="check",
                    steps=[s.model_dump(mode="json") for s in answer.check.steps],
                    strength=answer.check.strength,
                    why=answer.check.why,
                    writer=f"{writer}:{model}",
                    prompt_hash=prompt,
                    expectation_changed=changed,
                    tokens=tokens,
                    commit_sha=self.commit,
                )
            )
            return True
        if answer.no_check is not None:
            files = lines_of.get(claim_id, ("", []))[1]
            self.store.save_check(
                StoredCheck(
                    claim_id=claim_id,
                    kind="reason",
                    why=answer.no_check.reason,
                    writer=f"{writer}:{model}",
                    prompt_hash=prompt,
                    tokens=tokens,
                    commit_sha=self.commit,
                    reads={p: self.repo.sha(p) for p in files},
                )
            )
        return False

    async def _agent(
        self,
        llm: BaseChatModel,
        claims_of: dict[str, StoredClaim],
        lines_of: dict[str, tuple[str, list[str]]],
        report: dict[str, Any],
    ) -> list[str]:
        """Hand the claims the two calls left failing or unanswered to the searching agent, in batches.

        Returns the claims whose failing check the agent tried to swap for a reason, which is refused.
        """
        refused: list[str] = []
        results, checks = self.store.results(), self.store.checks()
        left = [
            cid
            for cid in claims_of
            if cid not in checks or checks[cid].kind == "check" and cid in results and not results[cid].holds
        ]
        stage_start = time.monotonic()
        spent = Spent()
        size = self.config.checks.agent_batch
        budget = Budget(
            max_turns=self.config.checks.agent_max_turns, max_tokens=self.config.checks.agent_max_tokens, trim=False
        )
        model = str(getattr(llm, "model_name", "") or getattr(llm, "model", ""))
        for start in range(0, len(left), size):
            batch = left[start : start + size]
            inputs = [
                ClaimInput(f"c{i}", cid, claims_of[cid].claim, lines=lines_of[cid][0]) for i, cid in enumerate(batch, 1)
            ]
            result = await write_checks(llm, self.repo, inputs, budget)
            spent.calls += result.turns
            spent.tokens_in += result.tokens_in
            spent.tokens_out += result.tokens_out
            spent.tokens_cached += result.tokens_cached
            share = (result.tokens_in + result.tokens_out) // max(len(batch), 1)
            for done in result.checks:
                self._replace_failing(
                    done.claim_id, Answer(claim="", check=done.check), share, model, lines_of, "agent"
                )
            for claim_id, reason in result.no_checks.items():
                answer = Answer(claim="", no_check=NoCheck(claim="", reason=reason))
                if claim_id in checks:  # it has a failing check, which a reason never replaces
                    refused.append(claim_id)
                else:
                    self._store_check(claim_id, answer, share, model, lines_of, writer="agent")
        report["stages"].append(asdict(Stage.of("agent", len(left), spent, time.monotonic() - stage_start)))
        return refused

    @traceable(run_type="chain", name="checks strengthen")
    async def strengthen(
        self, llm: BaseChatModel, decider: Decider | None = None, on_group: Callable[[int], object] | None = None
    ) -> dict[str, Any]:
        """Rewrite each weak check once, with what it missed, and keep the rewrite only if it is better.

        Better: it holds on the repository as it is now and notices more changes to its code than the old one. A
        rewrite that does no better (or a reason in its place) leaves the old check, accepted as the best there is,
        with why; it is not tried again until the check or its code changes.
        """
        started = time.monotonic()
        checks, results, quality = self.store.checks(), self.store.results(), self.store.quality()
        rows = [r for r in listing(self) if r["trust"] == "weak"]
        targets = []
        for row in rows:
            cid = row["claim_id"]
            key = hashlib.sha256(json.dumps([checks[cid].steps, results[cid].reads_key]).encode()).hexdigest()[:16]
            if quality.get(cid) is None or quality[cid].strengthen_key != key:
                targets.append((row, key))
        report: dict[str, Any] = {
            "weak": len(rows),
            "tried": len(targets),
            "improved": 0,
            "accepted": 0,
            "unanswered": 0,
            "stages": [],
        }
        if not targets:
            report["seconds"] = round(time.monotonic() - started, 1)
            return report
        everyone = self.claims()
        claims_of = {c.claim_id: c for c in everyone}
        settled = self._settled(everyone)
        lined = [
            (claims_of[row["claim_id"]], *self._lines(claims_of[row["claim_id"]], settled, everyone))
            for row, _ in targets
        ]
        keys = {row["claim_id"]: key for row, key in targets}
        missed = {row["claim_id"]: row for row, _ in targets}
        spent = Spent()
        self.spent = [spent]
        limit = asyncio.Semaphore(self.config.concurrency.max_model_calls)
        model = str(getattr(llm, "model_name", "") or getattr(llm, "model", ""))

        async def one(group: list[tuple[StoredClaim, str, list[str]]]) -> None:
            """Ask for stronger checks for one group and keep the ones that are better."""
            items = []
            for i, (claim, text, _) in enumerate(group, 1):
                row = missed[claim.claim_id]
                saw = [{"detail": f"did not notice: {change}"} for change in row["survived"][:5]]
                if row["link_verdict"]:
                    saw.append({"detail": f"the decision model says it tests: {row['link_verdict']}"})
                items.append(
                    Item(
                        f"c{i}",
                        claim.claim_id,
                        claim.claim,
                        claim.sentence,
                        text,
                        check={"steps": checks[claim.claim_id].steps},
                        saw=saw,
                    )
                )
            try:
                async with limit:
                    answers, tokens = await strengthen_group(llm, items, spent)
            except CALL_ERRORS as error:
                log.warning("strengthen_group_failed", claims=[i.claim_id for i in items], error=str(error)[:300])
                if on_group is not None:
                    on_group(len(group))
                return
            share = tokens // max(len(items), 1)
            for item in items:
                outcome = await self._keep_if_better(
                    claims_of[item.claim_id], answers.get(item.label), share, model, keys[item.claim_id], decider
                )
                report[{"kept": "improved", "accepted": "accepted", "no answer": "unanswered"}[outcome]] += 1
            if on_group is not None:
                on_group(len(group))

        await asyncio.gather(*(one(g) for g in self._groups(lined)))
        report["stages"].append(asdict(Stage.of("strengthen", len(lined), spent, time.monotonic() - started)))
        report["seconds"] = round(time.monotonic() - started, 1)
        return report

    async def _keep_if_better(
        self,
        claim: StoredClaim,
        answer: Answer | None,
        tokens: int,
        model: str,
        key: str,
        decider: Decider | None,
    ) -> str:
        """Keep a rewritten check only if it is better; return "kept", "accepted" or "no answer".

        Better: it holds on the repository as it is, it notices more changes to a value or condition of its code than
        the old check (a deleted line or file breaks any check that matches it, so those do not count), it is not
        only file steps where the old check was not, and, when the link question is on, the decision model scores it
        at least 0.5 and no lower than the old check. A rewrite that is not better leaves the old check, accepted by
        "auto" with why, until its code changes; no answer leaves it to be tried again next run.
        """
        cid = claim.claim_id
        if answer is None:
            return "no answer"
        old = self.store.checks()[cid]
        old_result = self.store.results()[cid]
        old_steps = STEPS.validate_python(old.steps)
        old_quality = measure(self.repo, old_steps, [str(r.get("detail", "")) for r in old_result.results])
        old_link = self.store.quality_of(cid)
        why = ""
        if answer.check is not None and answer.check.steps:
            steps = [s.model_dump(mode="json") for s in answer.check.steps]
            parsed = STEPS.validate_python(steps)
            holds, results = run_check(self.repo, parsed)
            new = measure(self.repo, parsed, [r.detail for r in results]) if holds else None
            files_only = all(st.op == "file" for st in parsed) and not all(st.op == "file" for st in old_steps)
            if new is None:
                why = "a rewrite did not hold on the repository as it is"
            elif files_only:
                why = "a rewrite only tested that files exist"
            elif TEXT_ONLY in new.survived or new.meaningful <= old_quality.meaningful:
                why = f"a rewrite noticed {new.meaningful} changes to a value or condition, no more than the old check"
            else:
                link: tuple[float, str] | None = None
                if decider is not None and decider.asks("link"):
                    question = {"claim": claim.claim, "steps": steps, "why": answer.check.why}
                    try:
                        link = await decider.link(question)
                    except DecisionError as error:
                        log.warning("strengthen_link_failed", claim=cid, error=str(error)[:300])
                        return "no answer"
                    old_score = old_link.link_score if old_link and old_link.link_score is not None else 0.0
                    if link is not None and (link[0] < 0.5 or link[0] < old_score):
                        why = f"a rewrite tests {link[1]} ({link[0]:.2f}), no closer to the claim than the old check"
                if not why:
                    self._store_check(cid, answer, tokens, model, {}, writer="strengthen")
                    self._run(cid, steps)
                    if link is not None:
                        self.store.save_link(
                            cid,
                            link[0],
                            link[1],
                            asked_key(
                                f"link:{decider.model('link') if decider else ''}",
                                {"claim": claim.claim, "steps": steps, "why": answer.check.why},
                            ),
                        )
                    return "kept"
        elif answer.no_check is not None:
            why = f"no stronger check: {answer.no_check.reason}"
        self.store.set_acceptance(cid, "auto", why or "the rewrite was not usable", strengthen_key=key)
        return "accepted"

    @traceable(run_type="chain", name="checks run")
    def run(self, everything: bool = False, on_check: Callable[[int, int], object] | None = None) -> dict[str, Any]:
        """Run every stored check in scope whose files changed since its last run (all with ``everything``).

        ``on_check(done, total)`` is called after each claim, for a progress report: the first run after an upgrade
        mutation-tests every holding check, which takes a while.

        A check whose reads are unchanged keeps its last result; a settled claim whose files changed is settled again.
        Returns counts and, per claim not holding, what failed.
        """
        started = time.monotonic()
        plan = self.plan()
        ran = reused = 0
        rows: list[dict[str, Any]] = []
        for number, state in enumerate(plan, 1):
            if on_check is not None and number > 1:
                on_check(number - 1, len(plan))
            check = state.check
            if check is None:
                rows.append({"claim_id": state.claim.claim_id, "claim": state.claim.claim, "status": "no check"})
                continue
            result = state.result
            if check.kind == "check":
                fresh = result is None or everything or result.reads_key != reads_key(state.reads_now)
                if fresh:
                    result = self._run(check.claim_id, check.steps)
                    ran += 1
                else:
                    reused += 1
                    if result is not None:
                        self._measure(check.claim_id, check.steps, result)  # free; skipped when already measured
            elif check.kind == "settled":
                # Settling costs no model, and what decides it (git's file list and history, CLI flags) is not a set
                # of files to hash, so a settled claim is settled again on every run.
                result = self._save_settled(state.claim, settle(self.evidence, state.claim.claim))
                ran += 1
                if result is None:
                    rows.append({"claim_id": state.claim.claim_id, "claim": state.claim.claim, "status": "no check"})
                    continue
            if check.kind == "reason":
                outcome = "reason"
            else:
                outcome = "holds" if result is not None and result.holds else "fails"
            rows.append(
                {
                    "claim_id": check.claim_id,
                    "claim": state.claim.claim,
                    "concept": state.claim.concept,
                    "status": outcome,
                    "kind": check.kind,
                    "strength": check.strength,
                    "why": check.why,
                    "expectation_changed": check.expectation_changed,
                    "failed_steps": [r for r in (result.results if result else []) if not r.get("holds")][:3],
                }
            )
        if on_check is not None:
            on_check(len(plan), len(plan))
        counts: dict[str, int] = {}
        for row in rows:
            counts[row["status"]] = counts.get(row["status"], 0) + 1
        return {
            "claims": len(rows),
            "ran": ran,
            "reused": reused,
            "counts": counts,
            "rows": rows,
            "seconds": round(time.monotonic() - started, 1),
        }

    @traceable(run_type="chain", name="checks triage")
    async def triage(self, decider: Decider, on_question: Callable[[int, int], object] | None = None) -> dict[str, Any]:
        """Ask each question switched on in ``[decisions]``: why each failing check failed (failure), what the lines
        of each reason-only claim show (judge), and whether each check tests what its claim says (link).

        A question already answered for the same claim, check and result is not asked again. Failures come back ranked
        by the chance the claim is false.
        """
        started = time.monotonic()
        plan = self.plan()
        stored = self.store.triage()
        limit = asyncio.Semaphore(self.config.decisions.max_calls)
        asked = skipped = 0
        everyone = self.claims()
        reasons = [s for s in plan if s.check is not None and s.check.kind == "reason"] if decider.asks("judge") else []
        settled = self._settled(everyone) if reasons else {}

        async def failure(state: ClaimState) -> None:
            """Ask why one check failed, unless already asked."""
            nonlocal asked, skipped
            assert state.check is not None and state.result is not None
            question = failure_state(state.claim, state.check, state.result)
            key = asked_key(f"failure:{decider.model('failure')}", question)
            known = answer_keys("failure", decider.model("failure"), question)
            if (old := stored.get(state.claim.claim_id)) is not None and old.asked_key in known:
                skipped += 1
                return
            async with limit:
                score, verdict, answers = await decider.failure(question)
            asked += 1
            self.store.save_triage(
                Triage(
                    claim_id=state.claim.claim_id,
                    question="failure",
                    asked_key=key,
                    model=decider.model("failure"),
                    score=score,
                    verdict=verdict,
                    answers=answers,
                )
            )

        async def judged(state: ClaimState) -> None:
            """Ask what one reason-only claim's lines show, unless already asked."""
            nonlocal asked, skipped
            text, _ = self._lines(state.claim, settled, everyone)
            question = {"claim": state.claim.claim, "lines": text}
            key = asked_key(f"judge:{decider.model('judge')}", question)
            known = answer_keys("judge", decider.model("judge"), question)
            if (old := stored.get(state.claim.claim_id)) is not None and old.asked_key in known:
                skipped += 1
                return
            async with limit:
                score, verdict, answers = await decider.judge(question)
            asked += 1
            self.store.save_triage(
                Triage(
                    claim_id=state.claim.claim_id,
                    question="judge",
                    asked_key=key,
                    model=decider.model("judge"),
                    score=score,
                    verdict=verdict,
                    answers=answers,
                )
            )

        errors: dict[str, str] = {}

        answered = 0

        async def safely(claim_id: str, ask: Any) -> None:
            """Ask one question and keep its error, so one bad answer does not stop the others; report progress."""
            nonlocal answered
            try:
                await ask
            except DecisionError as error:
                errors[claim_id] = str(error)
            answered += 1
            if on_question is not None:
                on_question(answered, total)

        quality = self.store.quality()

        async def linked(state: ClaimState) -> None:
            """Ask whether one check tests its claim, unless already asked about these steps."""
            nonlocal asked, skipped
            assert state.check is not None
            question = {"claim": state.claim.claim, "steps": state.check.steps, "why": state.check.why}
            key = asked_key(f"link:{decider.model('link')}", question)
            old = quality.get(state.claim.claim_id)
            if old is not None and old.link_key in answer_keys("link", decider.model("link"), question):
                skipped += 1
                return
            async with limit:
                score, verdict = await decider.link(question)
            asked += 1
            self.store.save_link(state.claim.claim_id, score, verdict, key)

        checks_to_link = (
            [s for s in plan if s.check is not None and s.check.kind == "check"] if decider.asks("link") else []
        )

        failing = [
            s
            for s in plan
            if decider.asks("failure")
            and s.check is not None
            and s.check.kind == "check"
            and s.result is not None
            and not s.result.holds
            and s.status != "changed"
        ]
        total = len(failing) + len(reasons) + len(checks_to_link)
        await asyncio.gather(
            *(safely(s.claim.claim_id, failure(s)) for s in failing),
            *(safely(s.claim.claim_id, judged(s)) for s in reasons),
            *(safely(s.claim.claim_id, linked(s)) for s in checks_to_link),
        )
        answers = self.store.triage()
        claims = {c.claim_id: c for c in everyone}
        current = {
            s.claim.claim_id: answer_keys(
                "failure", decider.model("failure"), failure_state(s.claim, s.check, s.result)
            )
            for s in failing
            if s.check is not None and s.result is not None
        }
        ranked: list[dict[str, Any]] = sorted(
            (
                {"claim_id": cid, "claim": claims[cid].claim, "score": round(t.score, 3), "verdict": t.verdict}
                for cid, t in answers.items()
                if t.question == "failure" and t.asked_key in current.get(cid, set())
            ),
            key=lambda r: -float(r["score"]),
        )
        judgements = [
            {"claim_id": cid, "claim": claims[cid].claim, "score": round(t.score, 3), "verdict": t.verdict}
            for cid, t in answers.items()
            if t.question == "judge" and cid in claims and cid in {s.claim.claim_id for s in reasons}
        ]
        settled_false = [
            {"claim_id": s.claim.claim_id, "claim": s.claim.claim, "why": s.check.why}
            for s in plan
            if s.check is not None and s.check.kind == "settled" and s.check.settled is False
        ]
        return {
            "failures": len(failing),
            "judged": len(reasons),
            "asked": asked,
            "already_asked": skipped,
            "decision_calls": decider.calls,
            "decision_tokens_in": decider.tokens_in,
            "ranked_failures": ranked,
            "judgements": sorted(judgements, key=lambda r: r["verdict"]),
            "settled_false": settled_false,
            "errors": errors,
            "linked": len(checks_to_link),
            "links": dict(
                Counter(q.link_verdict for q in self.store.quality().values() if q.link_verdict).most_common()
            ),
            "seconds": round(time.monotonic() - started, 1),
        }


STRONG_LINK = 0.75  # a link score this high says the check tests the claim itself


def trust(status: str, quality: CheckQuality | None) -> str:
    """Return how far a holding check can be trusted: weak, unsure (its two scores disagree), accepted, or "".

    Weak: it noticed no change to its code and the decision model does not say it tests the claim, or the model says
    it tests only a keyword or nothing and no change was noticed either. Unsure: one score says weak and the other
    says strong. Accepted: weak, but a person, or a rewrite that did no better, accepted it as the best there is.
    """
    if status != "holds" or quality is None:
        return ""
    hollow = bool(quality.mutants) and quality.killed == 0 or TEXT_ONLY in quality.survived
    off_claim = quality.link_score is not None and quality.link_score < 0.5
    strong_link = quality.link_score is not None and quality.link_score >= STRONG_LINK
    sensitive = bool(quality.killed)
    if (hollow and strong_link) or (off_claim and sensitive):
        verdict = "unsure"
    elif hollow or off_claim:
        verdict = "weak"
    else:
        return ""
    return "accepted" if quality.accepted_by else verdict


def _quality_fields(status: str, quality: CheckQuality | None) -> dict[str, Any]:
    """Return a listed claim's quality: mutants noticed, link score, and its trust (weak, unsure, accepted)."""
    level = trust(status, quality)
    return {
        "mutants": quality.mutants if quality else None,
        "killed": quality.killed if quality else None,
        "survived": quality.survived if quality else [],
        "link_score": quality.link_score if quality else None,
        "link_verdict": quality.link_verdict if quality else None,
        "trust": level,
        "weak": level == "weak",
        "accepted_by": quality.accepted_by if quality else "",
        "accepted_note": quality.accepted_note if quality else "",
    }


def listing(stage: Checks) -> list[dict[str, Any]]:
    """Return every claim in scope with its stored check, last result and triage: what the database says, no run.

    A claim's status: holds or fails (a check, as of its last run), reason (no step can test it), settled true or
    settled false (decided with no model), or no check (not written yet).
    """
    checks, results, triage = stage.store.checks(), stage.store.results(), stage.store.triage()
    quality = stage.store.quality()
    rows = []
    for claim in stage.claims():
        check, result, answer = checks.get(claim.claim_id), results.get(claim.claim_id), triage.get(claim.claim_id)
        if check is None:
            status = "no check"
        elif check.kind == "reason":
            status = "reason"
        elif check.kind == "settled":
            status = "settled true" if check.settled else "settled false"
        else:
            status = "unrun" if result is None else "holds" if result.holds else "fails"
        rows.append(
            {
                "claim_id": claim.claim_id,
                "concept": claim.concept,
                "section": claim.chunk_id.partition("#")[2],
                "sentence_n": claim.sentence_n,
                "kind": claim.claim_type,
                "claim": claim.claim,
                "status": status,
                "strength": check.strength if check else None,
                "why": check.why if check else "",
                "writer": check.writer if check else "",
                "flagged": bool(check and check.expectation_changed),
                "steps": check.steps if check else [],
                "reads": sorted(check.reads) if check else [],
                "failed_steps": [r for r in (result.results if result else []) if not r.get("holds")],
                "ran_at": result.ran_at if result else "",
                "triage": {"question": answer.question, "verdict": answer.verdict, "score": round(answer.score, 3)}
                if answer
                else None,
                **_quality_fields(status, quality.get(claim.claim_id)),
            }
        )
    return rows


def summary(plan: list[ClaimState]) -> dict[str, Any]:
    """Return a plan's counts by status and kind, and the claims that need a model, for printing or JSON."""
    by_status: dict[str, int] = {}
    for state in plan:
        by_status[state.status] = by_status.get(state.status, 0) + 1
    writes = [
        s
        for s in plan
        if s.status in {"new", "rewrite"} or s.status == "changed" and s.check and s.check.kind != "check"
    ]
    runs = [s for s in plan if s.status in {"unrun", "changed"} and s.check and s.check.kind == "check"]
    return {
        "claims": len(plan),
        "by_status": by_status,
        "to_write": len(writes),
        "to_run": len(runs),
        "settled": sum(1 for s in plan if s.check is not None and s.check.kind == "settled"),
        "claims_to_write": [{"claim_id": s.claim.claim_id, "claim": s.claim.claim, "status": s.status} for s in writes],
        "claims_to_run": [{"claim_id": s.claim.claim_id, "claim": s.claim.claim, "status": s.status} for s in runs],
    }


def as_json(value: Any) -> str:
    """Return a value as JSON text."""
    return json.dumps(value, default=str)
