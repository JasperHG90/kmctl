"""Tests for the checks stage: writing, running and triaging checks, and skipping what has not changed."""

import asyncio
import json
import pathlib as plb
import re
import subprocess
from typing import Any

import httpx
import pytest
import respx
from helpers import make_chunk
from langchain_core.messages import AIMessage

from audit_cli.checks.decide import Decider
from audit_cli.checks.pipeline import Checks, expectation_changed, listing, summary
from audit_cli.checks.steps import Repository
from audit_cli.checks.twocall import FIX, STRENGTHEN, Answers
from audit_cli.config import Config, DecisionsConfig
from audit_cli.db import Store, StoredClaim

CONCEPT = "decisions/0001-queue"
GOOD = {"steps": [{"op": "definition", "name": "retry", "paths": "src/*.py"}], "strength": "exact", "why": "it is"}
BROKEN = {"steps": [{"op": "definition", "name": "retry_job", "paths": "src/*.py"}], "strength": "exact", "why": "x"}
REASON = {"reason": "history: what was decided before"}


class Writer:
    """Stands in for the writing model: answers each claim shown by its text, from fixed write and fix answers."""

    def __init__(
        self,
        write: dict[str, dict[str, Any]],
        fix: dict[str, dict[str, Any]] | None = None,
        strengthen: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self.write, self.fix, self.strengthen = write, fix or {}, strengthen or {}
        self.calls: list[str] = []
        self.model_name = "fake"

    def with_structured_output(self, *args: Any, **kwargs: Any) -> "Writer":
        """Return itself: it answers structured calls."""
        return self

    async def ainvoke(self, messages: list[Any]) -> dict[str, Any]:
        """Answer every labelled claim in the message, from the fix answers when it is a fix call."""
        text = str(messages[-1].content)
        kind = "fix" if text.startswith(FIX) else "strengthen" if text.startswith(STRENGTHEN) else "write"
        self.calls.append(kind)
        answers = []
        for label, claim in re.findall(r"^(c\d+): (.+)$", text, re.MULTILINE):
            given = {"fix": self.fix, "strengthen": self.strengthen, "write": self.write}[kind].get(claim)
            if given is not None:
                answers.append(
                    {
                        "claim": label,
                        **(
                            {"no_check": {"claim": label, **given}}
                            if "reason" in given
                            else {"check": {"claim": label, **given}}
                        ),
                    }
                )
        usage = {
            "input_tokens": 1000,
            "output_tokens": 100,
            "total_tokens": 1100,
            "input_token_details": {"cache_read": 400},
        }
        return {
            "parsed": Answers.model_validate({"answers": answers}),
            "raw": AIMessage(content="", usage_metadata=usage),
            "parsing_error": None,
        }


def stored(n: int, text: str, concept: str = CONCEPT) -> StoredClaim:
    """Return a stored claim on sentence ``n`` of the concept's one section."""
    from audit_cli.claims.models import claim_id

    return StoredClaim(
        chunk_id=f"{concept}#one",
        position=n,
        claim_id=claim_id(concept, text),
        concept=concept,
        sentence_n=n,
        sentence=text,
        claim_type="point",
        claim=text,
        how_to_check="",
        quantifier="",
        refers_to=[],
        run="extractor",
    )


@pytest.fixture
def project(tmp_path: plb.Path) -> tuple[plb.Path, plb.Path]:
    """A repository with code and a bundle concept, and its database path."""
    root = tmp_path / "proj"
    (root / "src").mkdir(parents=True)
    (root / "src" / "worker.py").write_text("def retry(job):\n    return job\n")
    (root / ".okf" / "decisions").mkdir(parents=True)
    (root / ".okf" / "decisions" / "0001-queue.md").write_text(
        "---\ntype: decision\n---\n\n# Queue\n\nThe worker retries.\n"
    )
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    return root, tmp_path / "audit.sqlite"


def checks(project: tuple[plb.Path, plb.Path], store: Store, texts: list[str], **settings: Any) -> Checks:
    """Store the claims and return the checks stage over them."""
    root, _ = project
    chunk = make_chunk(f"{CONCEPT}#one", texts)
    store.replace_chunks([chunk])
    store.replace_claims(chunk.id, [stored(n, t) for n, t in enumerate(texts, 1)])
    config = Config.model_validate({"checks": settings} if settings else {})
    return Checks(store, Repository(root), config, root / ".okf")


def test_new_claims_are_written_run_and_then_left_alone(project: tuple[plb.Path, plb.Path]) -> None:
    """The first write calls the model and runs the checks; a second write and a plan find nothing to do."""
    texts = ["The worker defines `retry`.", "The queue was chosen in 2024."]
    writer = Writer({texts[0]: GOOD, texts[1]: REASON})
    with Store(project[1]) as store:
        stage = checks(project, store, texts)
        assert summary(stage.plan())["to_write"] == 2
        report = asyncio.run(stage.write(writer))
        assert report["outcome"]["holds"] == 1
        assert report["outcome"]["reasons"] == 1 and writer.calls == ["write", "write"]  # two files, two groups
        write = next(s for s in report["stages"] if s["name"] == "write")
        assert (write["calls"], write["tokens_in"], write["tokens_cached"]) == (2, 2000, 800)
        assert {s.status for s in stage.plan()} == {"up to date"}
        again = asyncio.run(stage.write(writer))
        assert again["to_write"] == 0 and len(writer.calls) == 2


def test_a_run_reuses_results_until_a_file_a_check_reads_changes(project: tuple[plb.Path, plb.Path]) -> None:
    """Running again reuses the last result; editing the file the check reads makes it run, and its failure shows."""
    root, db = project
    text = "The worker defines `retry`."
    with Store(db) as store:
        stage = checks(project, store, [text])
        asyncio.run(stage.write(Writer({text: GOOD})))
        assert stage.run()["reused"] == 1
        (root / "src" / "worker.py").write_text("def other(job):\n    return job\n")
        stage = Checks(store, Repository(root), stage.config, root / ".okf")
        assert [s.status for s in stage.plan()] == ["changed"]
        report = stage.run()
        assert (report["ran"], report["counts"]) == (1, {"fails": 1})


def test_a_changed_claim_is_a_new_claim_and_its_old_check_is_pruned(project: tuple[plb.Path, plb.Path]) -> None:
    """Rewording a claim gives it a new id: the old check goes, the new claim is written."""
    old, new = "The worker defines `retry`.", "The worker defines `retry` for jobs."
    writer = Writer({old: GOOD, new: GOOD})
    with Store(project[1]) as store:
        asyncio.run(checks(project, store, [old]).write(writer))
        stage = checks(project, store, [new])
        report = asyncio.run(stage.write(writer))
        assert report["pruned"] == 1 and report["to_write"] == 1 and len(store.checks()) == 1


def test_a_failing_check_is_fixed_once_and_a_bent_expectation_is_flagged(project: tuple[plb.Path, plb.Path]) -> None:
    """A check that fails goes back once; a fix that changes what a failed step expects is flagged for a person."""
    fixed, bent = "The worker defines `retry` (fixed).", "No `retry_job` is defined."
    bent_check = {
        "steps": [{"op": "definition", "name": "retry_job", "paths": "src/*.py", "defined": False}],
        "strength": "exact",
        "why": "bent",
    }
    writer = Writer({fixed: BROKEN, bent: BROKEN}, fix={fixed: GOOD, bent: bent_check})
    with Store(project[1]) as store:
        stage = checks(project, store, [fixed, bent])
        report = asyncio.run(stage.write(writer))
        assert writer.calls == ["write", "fix"]
        assert report["outcome"]["fixed_to_hold"] == 2 and report["outcome"]["expectation_changed"] == 1
        flagged = [c for c in store.checks().values() if c.expectation_changed]
        assert [c.why for c in flagged] == ["bent"]


def test_a_claim_settled_free_needs_no_model(project: tuple[plb.Path, plb.Path]) -> None:
    """A claim the anchors decide is stored as settled, with no call."""
    text = "`src/gone.py` no longer exists in the repository."
    writer = Writer({})
    with Store(project[1]) as store:
        report = asyncio.run(checks(project, store, [text]).write(writer))
        assert writer.calls == [] and next(s for s in report["stages"] if s["name"] == "settle")["claims"] == 1
        (check,) = store.checks().values()
        assert (check.kind, check.settled) == ("settled", True)


def test_an_unanswered_claim_stays_new(project: tuple[plb.Path, plb.Path]) -> None:
    """A claim the model leaves unanswered, twice, is not stored and is planned again."""
    text = "The worker defines `retry`."
    writer = Writer({})
    with Store(project[1]) as store:
        stage = checks(project, store, [text])
        report = asyncio.run(stage.write(writer))
        assert writer.calls == ["write", "write"] and report["outcome"]["unanswered"] == 1
        assert [s.status for s in stage.plan()] == ["new"]


def test_expectation_changed_compares_target_and_expectation() -> None:
    """Only a step on the same target with a different expectation counts; a new target does not."""
    old = [{"op": "query", "paths": "w.yml", "query": "jobs.p.if", "expect": "equals", "value": "success()"}]
    saw = [{"holds": False}]
    assert expectation_changed(old, saw, [old[0] | {"value": "!cancelled()"}])
    assert not expectation_changed(old, saw, [old[0] | {"query": "jobs.publish.if"}])
    assert not expectation_changed(old, [{"holds": True}], [old[0] | {"value": "!cancelled()"}])


@respx.mock
def test_triage_ranks_failures_and_marks_wrong_checks_for_rewrite(
    project: tuple[plb.Path, plb.Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The decision model's answer is stored; a check it calls wrong is planned for rewrite, and not asked again."""
    monkeypatch.setenv("DECIDE_KEY", "k")
    text = "The worker defines `retry` (broken)."
    reply = {
        "answers": {
            "claim_false": {"noul": 0.1},
            "cause": {"probabilities": {"check_wrong": 0.8, "claim_false": 0.1, "unclear": 0.1}},
        }
    }
    route = respx.post("https://decide.test/v1").mock(return_value=httpx.Response(200, json=reply))
    settings = DecisionsConfig.model_validate(
        {
            "providers": {"test": {"base_url": "https://decide.test/v1", "api_key_env": "DECIDE_KEY"}},
            "failure": {"enabled": True, "provider": "test", "model": "m"},
        }
    )
    with Store(project[1]) as store:
        stage = checks(project, store, [text], fix=False)
        asyncio.run(stage.write(Writer({text: BROKEN})))

        async def triage() -> dict[str, Any]:
            """Run triage with a fresh client."""
            async with httpx.AsyncClient() as client:
                return await stage.triage(Decider(settings, client))

        first = asyncio.run(triage())
        assert first["ranked_failures"][0]["verdict"] == "check_wrong" and route.call_count == 1
        assert json.loads(route.calls[0].request.content)["model"] == "m"
        assert [s.status for s in stage.plan()] == ["rewrite"]
        second = asyncio.run(triage())
        assert second["already_asked"] == 1 and route.call_count == 1


def test_a_settled_claim_is_settled_again_on_every_run(project: tuple[plb.Path, plb.Path]) -> None:
    """A file that comes back makes "it no longer exists" false on the next run, with no --all, and triage sees it."""
    root, db = project
    text = "`src/gone.py` no longer exists in the repository."
    with Store(db) as store:
        stage = checks(project, store, [text])
        asyncio.run(stage.write(Writer({})))
        (root / "src" / "gone.py").write_text("x = 1\n")
        subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
        stage = Checks(store, Repository(root), stage.config, root / ".okf")
        assert stage.run()["counts"] == {"fails": 1}
        (check,) = store.checks().values()
        assert check.settled is False and "present" in check.why


def test_a_claim_that_no_longer_settles_goes_back_to_the_writer(project: tuple[plb.Path, plb.Path]) -> None:
    """When the anchors stop deciding a settled claim, its settled check is dropped and the claim is new again."""
    from audit_cli.checks.anchors import Settled

    text = "`src/gone.py` no longer exists in the repository."
    with Store(project[1]) as store:
        stage = checks(project, store, [text])
        asyncio.run(stage.write(Writer({})))
        claim = stage.claims()[0]
        assert stage._save_settled(claim, Settled(None, "", [])) is None
        assert [s.status for s in stage.plan()] == ["new"]


def test_a_fix_may_not_swap_a_failing_check_for_a_reason(project: tuple[plb.Path, plb.Path]) -> None:
    """A failing check may have found drift, so a fix answering "no step can test it" is refused and counted."""
    text = "The worker defines `retry` (broken)."
    with Store(project[1]) as store:
        report = asyncio.run(checks(project, store, [text]).write(Writer({text: BROKEN}, fix={text: REASON})))
        assert report["outcome"]["reason_refused"] == 1 and report["outcome"]["fails"] == 1
        (check,) = store.checks().values()
        assert check.kind == "check"


class AgentWriter(Writer):
    """Writes broken checks in the two calls; as a tool-calling agent, submits a good check for every claim."""

    def bind_tools(self, tools: list[Any]) -> "AgentWriter":
        """Return itself; its tool replies come from agent_reply."""
        self.agent = True
        return self

    async def ainvoke(self, messages: list[Any]) -> Any:
        """Answer as the two-call writer, or, once tools are bound and the message is the agent's, submit."""
        text = str(messages[1].content)
        if getattr(self, "agent", False) and text.startswith("Write a check, or give a reason"):
            self.calls.append("agent")
            labels = re.findall(r"^(c\d+): ", text, re.MULTILINE)
            checks_ = [{"claim": label, **GOOD} for label in labels]
            usage = {"input_tokens": 500, "output_tokens": 50, "total_tokens": 550}
            return AIMessage(
                content="",
                tool_calls=[{"name": "Submit", "args": {"checks": checks_}, "id": "s1"}],
                usage_metadata=usage,
            )
        return await super().ainvoke(messages)


def test_the_agent_takes_what_the_two_calls_left_failing(project: tuple[plb.Path, plb.Path]) -> None:
    """With checks.agent on, a check still failing after the two calls goes to the agent, whose check is stored."""
    text = "The worker defines `retry` (agent)."
    writer = AgentWriter({text: BROKEN}, fix={text: BROKEN})
    with Store(project[1]) as store:
        report = asyncio.run(checks(project, store, [text], agent=True).write(writer))
        assert writer.calls[-1] == "agent" and report["outcome"]["holds"] == 1
        agent = next(s for s in report["stages"] if s["name"] == "agent")
        assert (agent["claims"], agent["tokens_in"]) == (1, 500)
        (check,) = store.checks().values()
        assert check.writer == "agent:fake"


@respx.mock
def test_a_bad_decision_reply_is_named_not_a_crash(
    project: tuple[plb.Path, plb.Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A reply that leaves out a question is recorded as that claim's error; the triage still finishes."""
    monkeypatch.setenv("DECIDE_KEY", "k")
    text = "The worker defines `retry` (broken)."
    respx.post("https://decide.test/v1").mock(
        return_value=httpx.Response(200, json={"answers": {"claim_false": {"noul": 0.1}}})
    )
    settings = DecisionsConfig.model_validate(
        {
            "providers": {"test": {"base_url": "https://decide.test/v1", "api_key_env": "DECIDE_KEY"}},
            "failure": {"enabled": True, "provider": "test", "model": "m"},
        }
    )
    with Store(project[1]) as store:
        stage = checks(project, store, [text], fix=False)
        asyncio.run(stage.write(Writer({text: BROKEN})))

        async def triage() -> dict[str, Any]:
            """Run triage with a fresh client."""
            async with httpx.AsyncClient() as client:
                return await stage.triage(Decider(settings, client))

        report = asyncio.run(triage())
        assert report["asked"] == 0 and "left out ['cause']" in next(iter(report["errors"].values()))


def test_rewrite_failing_keeps_a_failing_check_when_the_answer_is_a_reason(project: tuple[plb.Path, plb.Path]) -> None:
    """--rewrite-failing sends a failing check back, but a reason in reply is refused, as in the fix call."""
    text = "The worker defines `retry` (broken)."
    with Store(project[1]) as store:
        stage = checks(project, store, [text], fix=False)
        asyncio.run(stage.write(Writer({text: BROKEN})))
        report = asyncio.run(stage.write(Writer({text: REASON}), rewrite_failing=True))
        assert report["outcome"]["reason_refused"] == 1
        (check,) = store.checks().values()
        assert check.kind == "check" and [s.status for s in stage.plan()] == ["failing"]


def test_a_holding_check_is_mutation_tested_and_a_hollow_one_listed_weak(project: tuple[plb.Path, plb.Path]) -> None:
    """After a write, each holding check carries a mutation score; one that notices no change is listed weak."""
    from audit_cli.checks.pipeline import listing

    good, hollow = "The worker defines `retry` (scored).", "Jobs are retried (scored)."
    comment = {
        "steps": [{"op": "grep", "pattern": "retries jobs", "paths": "src/*.py"}],
        "strength": "proxy",
        "why": "the comment says so",
    }
    root, db = project
    (root / "src" / "worker.py").write_text("# retries jobs\ndef retry(job):\n    return job\n")
    with Store(db) as store:
        stage = checks(project, store, [good, hollow])
        asyncio.run(stage.write(Writer({good: GOOD, hollow: comment})))
        rows = {r["claim"]: r for r in listing(stage)}
        assert rows[good]["killed"] > 0 and not rows[good]["weak"]
        assert rows[hollow]["mutants"] > 0 and rows[hollow]["killed"] == 0 and rows[hollow]["weak"]


class FlakyWriter(Writer):
    """Answers like Writer, but its call for one claim's group fails as a provider's 504 would."""

    def __init__(self, write: dict[str, dict[str, Any]], fails_on: str) -> None:
        super().__init__(write)
        self.fails_on = fails_on

    async def ainvoke(self, messages: list[Any]) -> dict[str, Any]:
        """Raise a timeout for the group holding ``fails_on``; answer the rest."""
        if self.fails_on in str(messages[-1].content):
            raise TimeoutError("request timed out (504)")
        return await super().ainvoke(messages)


def test_a_failed_call_loses_its_group_only(project: tuple[plb.Path, plb.Path]) -> None:
    """One group's call failing (a 504) is recorded; the other groups are written, and its claims stay new."""
    ok, flaky = "The worker defines `retry`.", "The queue was chosen in 2024."
    with Store(project[1]) as store:
        stage = checks(project, store, [ok, flaky])
        report = asyncio.run(stage.write(FlakyWriter({ok: GOOD, flaky: REASON}, fails_on=flaky)))
        assert report["outcome"]["holds"] == 1 and report["outcome"]["errors"] == 1
        assert "504" in next(iter(report["errors"].values()))
        assert {s.claim.claim: s.status for s in stage.plan()}[flaky] == "new"


@respx.mock
def test_triage_with_failure_off_asks_no_failure_question(
    project: tuple[plb.Path, plb.Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """With only the link question on, a failing check is not asked about; the link question is."""
    monkeypatch.setenv("DECIDE_KEY", "k")
    text = "The worker defines `retry` (broken)."
    link = {"answers": {"link": {"probabilities": {"0": 0.1, "1": 0.1, "2": 0.2, "3": 0.6}}}}
    route = respx.post("https://decide.test/v1").mock(return_value=httpx.Response(200, json=link))
    settings = DecisionsConfig.model_validate(
        {
            "providers": {"test": {"base_url": "https://decide.test/v1", "api_key_env": "DECIDE_KEY"}},
            "link": {"enabled": True, "provider": "test", "model": "m"},
        }
    )
    with Store(project[1]) as store:
        stage = checks(project, store, [text], fix=False)
        asyncio.run(stage.write(Writer({text: BROKEN})))

        async def triage() -> dict[str, Any]:
            """Run triage with a fresh client."""
            async with httpx.AsyncClient() as client:
                return await stage.triage(Decider(settings, client))

        report = asyncio.run(triage())
        assert report["failures"] == 0 and report["linked"] == 1 and report["errors"] == {}
        assert json.loads(route.calls[0].request.content)["questions"].keys() == {"link"}


def test_trust_levels_weak_unsure_and_accepted() -> None:
    """Weak when the scores say so; unsure when they disagree; accepted once someone accepted it."""
    from audit_cli.checks.pipeline import trust
    from audit_cli.db import CheckQuality

    def q(**kw: Any) -> CheckQuality:
        """Return a quality row with the given fields."""
        return CheckQuality(claim_id="c", **kw)

    assert trust("holds", q(mutants=5, killed=0)) == "weak"
    assert trust("holds", q(mutants=5, killed=0, link_score=0.9)) == "unsure"
    assert trust("holds", q(mutants=5, killed=2, link_score=0.3)) == "unsure"
    assert trust("holds", q(link_score=0.3)) == "weak"
    assert trust("holds", q(mutants=5, killed=2, link_score=0.9)) == ""
    assert trust("holds", q(mutants=5, killed=0, accepted_by="person")) == "accepted"
    assert trust("fails", q(mutants=5, killed=0)) == ""


def test_a_weak_check_is_rewritten_once_and_kept_only_if_better(project: tuple[plb.Path, plb.Path]) -> None:
    """A rewrite that notices more of its code replaces the weak check; one that does not leaves it, accepted, and is
    not tried again while the check and its code stay the same."""
    better, stuck = "The worker defines `retry` (to strengthen).", "Jobs are retried (to strengthen)."
    comment = {
        "steps": [{"op": "grep", "pattern": "retries jobs", "paths": "src/*.py"}],
        "strength": "proxy",
        "why": "the comment says so",
    }
    root, db = project
    (root / "src" / "worker.py").write_text("# retries jobs\ndef retry(job):\n    return job\n")
    writer = Writer({better: comment, stuck: comment}, strengthen={better: GOOD, stuck: comment})
    with Store(db) as store:
        stage = checks(project, store, [better, stuck])
        asyncio.run(stage.write(writer))
        report = asyncio.run(stage.strengthen(writer))
        assert (report["tried"], report["improved"], report["accepted"]) == (2, 1, 1)
        rows = {r["claim"]: r for r in listing(stage)}
        assert rows[better]["trust"] == "" and rows[better]["killed"] > 0
        assert rows[stuck]["trust"] == "accepted" and "no more than the old check" in rows[stuck]["accepted_note"]
        again = asyncio.run(stage.strengthen(writer))
        assert again["tried"] == 0 and writer.calls.count("strengthen") == 1


COMMENT = {"steps": [{"op": "grep", "pattern": "retries jobs", "paths": "src/*.py"}], "strength": "proxy", "why": "c"}


def _weak_project(project: tuple[plb.Path, plb.Path]) -> None:
    """Give the worker a comment a weak check can match, and an import an unrelated check can match."""
    (project[0] / "src" / "worker.py").write_text("import os\n# retries jobs\ndef retry(job):\n    return job\n")


@pytest.mark.parametrize(
    ("rewrite", "why"),
    [
        (
            {"steps": [{"op": "grep", "pattern": "^import os", "paths": "src/*.py"}], "strength": "proxy", "why": "x"},
            "no more than the old check",
        ),
        (
            {"steps": [{"op": "file", "path": "src/worker.py"}], "strength": "proxy", "why": "x"},
            "only tested that files exist",
        ),
    ],
)
def test_a_rewrite_that_tests_something_else_is_not_kept(
    project: tuple[plb.Path, plb.Path], rewrite: dict[str, Any], why: str
) -> None:
    """A grep that only a deleted line breaks, or a file that exists, is no better than the weak check."""
    _weak_project(project)
    text = "The worker retries jobs (rewrite)."
    with Store(project[1]) as store:
        stage = checks(project, store, [text])
        asyncio.run(stage.write(Writer({text: COMMENT})))
        report = asyncio.run(stage.strengthen(Writer({}, strengthen={text: rewrite})))
        assert report["improved"] == 0 and report["accepted"] == 1
        (row,) = listing(stage)
        assert row["trust"] == "accepted" and why in row["accepted_note"]
        (check,) = store.checks().values()
        assert [st["pattern"] for st in check.steps] == ["retries jobs"]  # the old check stays


def test_an_automatic_acceptance_ends_when_the_code_changes(project: tuple[plb.Path, plb.Path]) -> None:
    """A check accepted because its rewrite did no better is tried again once the code it reads changes."""
    _weak_project(project)
    root, db = project
    text = "The worker retries jobs (retry)."
    with Store(db) as store:
        stage = checks(project, store, [text])
        asyncio.run(stage.write(Writer({text: COMMENT})))
        asyncio.run(stage.strengthen(Writer({}, strengthen={text: COMMENT})))
        assert listing(stage)[0]["trust"] == "accepted"
        (root / "src" / "worker.py").write_text("import os\n# retries jobs, twice\ndef retry(job):\n    return job\n")
        stage = Checks(store, Repository(root), stage.config, root / ".okf")
        stage.run()
        assert listing(stage)[0]["trust"] == "weak"
        again = Writer({}, strengthen={text: GOOD})
        assert asyncio.run(stage.strengthen(again))["improved"] == 1


def test_no_answer_is_tried_again_not_accepted(project: tuple[plb.Path, plb.Path]) -> None:
    """When the rewrite call leaves a claim out, the weak check stays weak and is tried on the next run."""
    _weak_project(project)
    text = "The worker retries jobs (silent)."
    with Store(project[1]) as store:
        stage = checks(project, store, [text])
        asyncio.run(stage.write(Writer({text: COMMENT})))
        assert asyncio.run(stage.strengthen(Writer({})))["unanswered"] == 1
        assert listing(stage)[0]["trust"] == "weak"
        assert asyncio.run(stage.strengthen(Writer({})))["tried"] == 1


@respx.mock
def test_a_rewrite_the_decision_model_scores_off_the_claim_is_not_kept(
    project: tuple[plb.Path, plb.Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """With the link question on, a rewrite that notices more but tests only a keyword is not kept."""
    monkeypatch.setenv("DECIDE_KEY", "k")
    _weak_project(project)
    text = "The worker retries jobs (scored)."
    keyword = {"answers": {"link": {"probabilities": {"0": 0.2, "1": 0.7, "2": 0.1, "3": 0.0}}}}
    respx.post("https://decide.test/v1").mock(return_value=httpx.Response(200, json=keyword))
    settings = DecisionsConfig.model_validate(
        {
            "providers": {"test": {"base_url": "https://decide.test/v1", "api_key_env": "DECIDE_KEY"}},
            "link": {"enabled": True, "provider": "test", "model": "m"},
        }
    )
    with Store(project[1]) as store:
        stage = checks(project, store, [text])
        asyncio.run(stage.write(Writer({text: COMMENT})))

        async def strengthen() -> dict[str, Any]:
            """Strengthen with the link question on."""
            async with httpx.AsyncClient() as client:
                return await stage.strengthen(Writer({}, strengthen={text: GOOD}), Decider(settings, client))

        report = asyncio.run(strengthen())
        assert report["improved"] == 0 and "keyword" in listing(stage)[0]["accepted_note"]


@respx.mock
@pytest.mark.parametrize("status", [401, 503])
def test_a_rewrite_the_decision_model_could_not_score_is_tried_again(
    project: tuple[plb.Path, plb.Path], monkeypatch: pytest.MonkeyPatch, status: int
) -> None:
    """A failed link call is no verdict on the rewrite: the old check stays weak, not accepted, and is tried again."""
    monkeypatch.setenv("DECIDE_KEY", "k")
    monkeypatch.setattr("audit_cli.checks.decide.ATTEMPTS", 1)
    _weak_project(project)
    text = "The worker retries jobs (scored)."
    respx.post("https://decide.test/v1").mock(return_value=httpx.Response(status, json={}))
    settings = DecisionsConfig.model_validate(
        {
            "providers": {"test": {"base_url": "https://decide.test/v1", "api_key_env": "DECIDE_KEY"}},
            "link": {"enabled": True, "provider": "test", "model": "m"},
        }
    )
    with Store(project[1]) as store:
        stage = checks(project, store, [text])
        asyncio.run(stage.write(Writer({text: COMMENT})))

        async def strengthen() -> dict[str, Any]:
            """Strengthen with a link endpoint that fails."""
            async with httpx.AsyncClient() as client:
                return await stage.strengthen(Writer({}, strengthen={text: GOOD}), Decider(settings, client))

        report = asyncio.run(strengthen())
        row = listing(stage)[0]
        assert report["unanswered"] == 1 and report["accepted"] == 0
        assert not row["accepted_by"] and row["trust"] == "weak"
