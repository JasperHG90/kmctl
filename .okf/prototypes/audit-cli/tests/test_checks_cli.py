"""Tests for the audit checks commands, run against the temporary repository with claims stored directly."""

import json
import pathlib as plb
from typing import Any

import httpx
import pytest
import respx
from helpers import make_chunk
from test_pipeline import GOOD, REASON, Writer, stored
from typer.testing import CliRunner

from audit_cli import checks_cli
from audit_cli.cli import REFUSED, app
from audit_cli.config import load_config
from audit_cli.db import Store

runner = CliRunner()
CONCEPT = "decisions/0001-use-a-queue"
CLAIMS = ["The worker defines `retry`.", "The queue was chosen in 2024."]
DECISIONS = '\n[decisions.providers.test]\nbase_url = "https://decide.test/v1"\napi_key_env = "DECIDE_KEY"\n' + "".join(
    f'\n[decisions.{q}]\nenabled = true\nprovider = "test"\nmodel = "m"\n' for q in ("failure", "judge", "link")
)


@pytest.fixture
def with_claims(repo: plb.Path, monkeypatch: pytest.MonkeyPatch) -> plb.Path:
    """Store two claims for the repository's concept and run from the repository, with a scripted writer."""
    monkeypatch.chdir(repo)
    (repo / "audit.toml").write_text((repo / "audit.toml").read_text() + "\n[telemetry]\nenabled = false\n")
    database = load_config(repo / "audit.toml").database_path(repo)
    chunk = make_chunk(f"{CONCEPT}#context", CLAIMS)
    with Store(database) as store:
        store.replace_chunks([chunk])
        store.replace_claims(
            chunk.id, [stored(n, t, CONCEPT).model_copy(update={"chunk_id": chunk.id}) for n, t in enumerate(CLAIMS, 1)]
        )
    writer = Writer({CLAIMS[0]: GOOD, CLAIMS[1]: REASON})
    monkeypatch.setattr(checks_cli, "build_llm", lambda *args: writer)
    return repo


def invoke(*args: str) -> Any:
    """Run the CLI with the arguments."""
    return runner.invoke(app, list(args))


def test_checks_are_refused_until_claims_are_extracted(repo: plb.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """With nothing extracted, every checks verb says to extract first."""
    monkeypatch.chdir(repo)
    result = invoke("checks", "diff", ".")
    assert result.exit_code == REFUSED and "audit claims extract" in result.output


def test_diff_write_run_then_nothing_left(with_claims: plb.Path) -> None:
    """diff lists both claims to write; write stores a check and a reason; run holds; diff then finds nothing."""
    first = invoke("checks", "diff", ".", "--json")
    assert first.exit_code == 1 and json.loads(first.output)["to_write"] == 2
    written = invoke("checks", "write", ".", "--json")
    assert written.exit_code == 0, written.output
    report = json.loads(written.output.splitlines()[-1])
    assert report["outcome"]["holds"] == 1 and report["outcome"]["reasons"] == 1
    ran = invoke("checks", "run", ".")
    assert ran.exit_code == 0 and "1 unchanged" in ran.output
    assert invoke("checks", "diff", ".").exit_code == 0
    with Store(load_config(with_claims / "audit.toml").database_path(with_claims)) as store:
        assert [p["verb"] for p in store.passes()] == ["checks write", "checks run"]


def test_run_fails_when_a_check_fails(with_claims: plb.Path) -> None:
    """After the code changes under a check, run reports the failure and exits 1."""
    assert invoke("checks", "write", ".").exit_code == 0
    (with_claims / "src" / "worker.py").write_text("def other(job):\n    return job\n")
    result = invoke("checks", "run", ".")
    assert result.exit_code == 1 and "fails: The worker defines `retry`." in result.output


def test_triage_is_refused_without_a_decision_model(with_claims: plb.Path) -> None:
    """triage names the settings it needs."""
    result = invoke("checks", "triage", ".")
    assert result.exit_code == REFUSED and "[decisions.failure]" in result.output


@respx.mock
def test_triage_asks_the_configured_decision_model(with_claims: plb.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """With decisions set, triage judges the reason-only claim and exits 0 when nothing looks like drift."""
    monkeypatch.setenv("DECIDE_KEY", "k")
    (with_claims / "audit.toml").write_text((with_claims / "audit.toml").read_text() + DECISIONS)
    reply = {
        "answers": {
            "shown_true": {"noul": 0.2},
            "verdict": {"probabilities": {"not_shown": 0.9, "true": 0.05, "false": 0.05}},
            "link": {"probabilities": {"0": 0.05, "1": 0.05, "2": 0.1, "3": 0.8}},
        }
    }
    route = respx.post("https://decide.test/v1").mock(return_value=httpx.Response(200, json=reply))
    assert invoke("checks", "write", ".").exit_code == 0
    result = invoke("checks", "triage", ".", "--json")
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["judged"] == 1 and report["judgements"][0]["verdict"] == "not_shown"
    assert report["linked"] == 1 and route.call_count == 2  # one judge question, one link question
    listed = json.loads(invoke("checks", "list", "--status", "holds", "--json").output)["claims"]
    assert listed[0]["link_verdict"] == "the claim" and listed[0]["link_score"] > 0.8


@respx.mock
def test_triage_with_a_refused_key_exits_2_and_says_why(with_claims: plb.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """When every question is refused, triage names the status and the setting to check."""
    monkeypatch.setenv("DECIDE_KEY", "wrong")
    (with_claims / "audit.toml").write_text((with_claims / "audit.toml").read_text() + DECISIONS)
    respx.post("https://decide.test/v1").mock(return_value=httpx.Response(401, text="bad key"))
    assert invoke("checks", "write", ".").exit_code == 0
    result = invoke("checks", "triage", ".")
    assert (
        result.exit_code == REFUSED
        and "401" in result.output
        and "decisions.providers.test.api_key_env" in result.output
    )


def test_checks_take_any_folder_in_the_repository(with_claims: plb.Path) -> None:
    """A folder with no bundle in it still names its repository's claims: checks work on claims, not on a bundle."""
    (with_claims / "src" / "deep").mkdir()
    result = invoke("checks", "diff", "src/deep", "--json")
    assert result.exit_code == 1 and json.loads(result.output)["claims"] == 2


def test_list_shows_status_details_and_filters(with_claims: plb.Path) -> None:
    """list reads the database only: every claim with its status, a filter, and one claim's details by id prefix."""
    before = invoke("checks", "list", "--json")
    assert {r["status"] for r in json.loads(before.output)["claims"]} == {"no check"}
    assert invoke("checks", "write", ".").exit_code == 0
    holds = json.loads(invoke("checks", "list", "--status", "holds", "--json").output)["claims"]
    assert [r["claim"] for r in holds] == [CLAIMS[0]]
    detail = invoke("checks", "list", "--claim", holds[0]["claim_id"][:6])
    assert detail.exit_code == 0 and '"op": "definition"' in detail.output
    assert invoke("checks", "list", "--status", "nonsense").exit_code == REFUSED


def test_run_takes_every_claim_to_a_verdict_and_no_write_calls_no_model(with_claims: plb.Path) -> None:
    """run writes what has no check, then runs it; --no-write runs stored checks only and says what it skipped."""
    skipped = invoke("checks", "run", "--no-write")
    assert skipped.exit_code == 0 and "were not written (--no-write)" in skipped.output
    assert {r["status"] for r in json.loads(invoke("checks", "list", "--json").output)["claims"]} == {"no check"}
    result = invoke("checks", "run", "--json")
    assert result.exit_code == 0, result.output
    report = json.loads(result.output.splitlines()[-1])
    assert report["write"]["outcome"]["holds"] == 1 and report["run"]["counts"] == {"holds": 1, "reason": 1}


def _store(repo: plb.Path) -> Store:
    """Open the repository's database."""
    return Store(load_config(repo / "audit.toml").database_path(repo))


def test_a_second_run_is_refused_while_one_is_going(with_claims: plb.Path) -> None:
    """Two runs would write the same claims twice, so a run is refused while another one's process is alive."""
    import os

    with _store(with_claims) as store:
        store.start_job("checks run", [], pid=os.getpid())  # this test's own process: alive
    result = invoke("checks", "run", "--no-triage")
    assert result.exit_code == REFUSED and "is already going" in result.output


def test_a_run_whose_process_ended_is_marked_died_and_does_not_block(with_claims: plb.Path) -> None:
    """A run left behind by a killed process does not hold the lock; status shows it died."""
    import subprocess

    gone = subprocess.Popen(["true"])
    gone.wait()
    with _store(with_claims) as store:
        store.start_job("checks run", [], pid=gone.pid)
    assert invoke("checks", "run", "--no-triage").exit_code == 0
    status = invoke("checks", "status")
    assert "died" in status.output and "done" in status.output and "checks:" in status.output


def test_a_background_run_finishes_and_status_follows_it(with_claims: plb.Path) -> None:
    """--background returns at once; the detached run reports to its job until it is done."""
    import time

    started = invoke("checks", "run", "--background", "--no-write", "--no-triage")
    assert started.exit_code == 0 and "in the background" in started.output
    for _ in range(120):
        jobs = json.loads(invoke("checks", "status", "--json").output)["jobs"]
        if jobs[0]["status"] not in {"running", "starting"}:
            break
        time.sleep(0.5)
    assert jobs[0]["status"] == "done" and jobs[0]["stage"] == "done", jobs[0]


def test_stop_ends_the_run_that_is_going(with_claims: plb.Path) -> None:
    """stop ends the process of the run going now and marks it stopped."""
    import subprocess

    sleeper = subprocess.Popen(["sleep", "30"], start_new_session=True)
    with _store(with_claims) as store:
        store.start_job("checks run", [], pid=sleeper.pid)
    result = invoke("checks", "stop")
    assert result.exit_code == 0 and f"pid {sleeper.pid}" in result.output
    assert sleeper.wait(timeout=10) != 0
    assert json.loads(invoke("checks", "status", "--json").output)["jobs"][0]["status"] == "stopped"


def test_a_folder_inside_the_bundle_with_no_claims_means_the_repository(with_claims: plb.Path) -> None:
    """Running from a prototype folder inside .okf/ (which holds no concepts) checks the repository's claims."""
    (with_claims / ".okf" / "prototypes" / "tool").mkdir(parents=True)
    (with_claims / ".okf" / "prototypes" / "tool" / "README.md").write_text("---\ntype: prototype\n---\n\n# Tool\n")
    result = invoke("checks", "diff", ".okf/prototypes/tool", "--json")
    assert result.exit_code == 1 and json.loads(result.output)["claims"] == 2


def test_a_reused_process_id_does_not_hold_the_lock(with_claims: plb.Path) -> None:
    """A job whose recorded start time does not match the live process with its id is a dead run, not a live one."""
    import os

    with _store(with_claims) as store:
        job = store.start_job("checks run", [], pid=os.getpid())
        store.update_job(job, pid_started="Mon Jan  1 00:00:00 2001")  # this pid, but some earlier process
    assert invoke("checks", "run", "--no-triage").exit_code == 0


def test_the_slot_is_taken_in_one_transaction(with_claims: plb.Path) -> None:
    """Two processes claiming at once: the first takes the slot, the second is told who holds it."""
    import os

    database = load_config(with_claims / "audit.toml").database_path(with_claims)
    with Store(database) as first, Store(database) as second:
        taken, _ = first.claim_job("checks run", [], os.getpid(), "", lambda pid, started: True)
        refused, holder = second.claim_job("checks run", [], os.getpid(), "", lambda pid, started: True)
    assert taken is not None and refused is None and holder is not None and holder["id"] == taken


def test_a_write_holds_the_slot_and_is_listed_as_a_run(with_claims: plb.Path) -> None:
    """write takes the same slot as run, so status shows it and a run cannot start beside it."""
    assert invoke("checks", "write").exit_code == 0
    jobs = json.loads(invoke("checks", "status", "--json").output)["jobs"]
    assert jobs[0]["verb"] == "checks write" and jobs[0]["status"] == "done"


def test_a_missing_writer_model_is_refused_not_a_crash(with_claims: plb.Path) -> None:
    """With no model for checks.writer, write refuses with exit 2, names the setting, and marks its job refused."""
    (with_claims / "audit.toml").write_text(
        (with_claims / "audit.toml").read_text().replace('model = "test-model"', 'model = ""')
    )
    result = invoke("checks", "write")
    assert result.exit_code == REFUSED and "agents.extractor.model" in result.output
    assert json.loads(invoke("checks", "status", "--json").output)["jobs"][0]["status"] == "refused"


def test_a_process_start_time_reads_the_same_in_any_time_zone_or_language(monkeypatch: pytest.MonkeyPatch) -> None:
    """The start time a job stores is compared later by another caller, who may have another TZ or LANG."""
    import os

    from audit_cli.checks_cli import _process_started

    monkeypatch.setenv("TZ", "UTC")
    first = _process_started(os.getpid())
    monkeypatch.setenv("TZ", "Asia/Tokyo")
    monkeypatch.setenv("LC_ALL", "de_DE.UTF-8")
    assert first and _process_started(os.getpid()) == first


def test_accept_marks_a_check_and_undo_clears_it(with_claims: plb.Path) -> None:
    """accept takes a check by id prefix; list shows who accepted it and why; --undo clears the mark."""
    assert invoke("checks", "write").exit_code == 0
    claim_id = json.loads(invoke("checks", "list", "--status", "holds", "--json").output)["claims"][0]["claim_id"]
    assert invoke("checks", "accept", claim_id[:6], "--note", "fine as it is").exit_code == 0
    with _store(with_claims) as store:
        accepted = store.quality_of(claim_id)
        assert accepted is not None and accepted.accepted_by == "person"
    assert invoke("checks", "accept", claim_id[:6], "--undo").exit_code == 0
    with _store(with_claims) as store:
        cleared = store.quality_of(claim_id)
        assert cleared is not None and cleared.accepted_by == ""
    assert invoke("checks", "accept", "zzzz").exit_code == REFUSED


def test_write_claim_rewrites_just_that_claim(with_claims: plb.Path) -> None:
    """--claim writes one claim again even when its check is up to date, and leaves the others alone."""
    assert invoke("checks", "write").exit_code == 0
    claim_id = json.loads(invoke("checks", "list", "--status", "holds", "--json").output)["claims"][0]["claim_id"]
    result = invoke("checks", "write", "--claim", claim_id[:8], "--json")
    assert result.exit_code == 0
    assert json.loads(result.output.splitlines()[-1])["to_write"] == 1


class LoopBound(Writer):
    """A writer that, like langchain_openai's one shared connection pool, breaks in any event loop but the first."""

    loop: Any = None  # shared by every instance, as the pool is

    async def ainvoke(self, messages: list[Any]) -> dict[str, Any]:
        """Answer as the writer does, or fail as a pool whose connections belong to a closed loop."""
        import asyncio

        loop = asyncio.get_running_loop()
        if LoopBound.loop not in (None, loop):
            raise RuntimeError("Event loop is closed")
        LoopBound.loop = loop
        return await super().ainvoke(messages)


def test_a_run_that_writes_then_strengthens_uses_one_event_loop(
    with_claims: plb.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Writing and strengthening share one event loop, because every model client shares one connection pool."""
    monkeypatch.setattr(LoopBound, "loop", None)
    (with_claims / "src" / "worker.py").write_text("# retries jobs\ndef retry(job):\n    return job\n")
    comment = {
        "steps": [{"op": "grep", "pattern": "retries jobs", "paths": "src/*.py"}],
        "strength": "proxy",
        "why": "c",
    }
    monkeypatch.setattr(checks_cli, "build_llm", lambda *args: LoopBound({CLAIMS[0]: comment, CLAIMS[1]: REASON}))
    result = invoke("checks", "run", "--json")
    assert result.exit_code == 0, result.output
    assert "strengthen" in json.loads(result.output.splitlines()[-1])
