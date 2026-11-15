"""The ``audit checks`` commands: turn stored claims into checks, run them, and triage what fails."""

import asyncio
import datetime as dt
import json
import os
import pathlib as plb
import signal
import subprocess
import sys
import time
from collections.abc import Callable
from typing import Annotated, Any

import httpx
import typer
from tqdm import tqdm

from audit_cli.checks.decide import Decider
from audit_cli.checks.pipeline import Checks, listing, summary
from audit_cli.checks.steps import Repository
from audit_cli.claims.extractor import build_llm
from audit_cli.config import Config, ConfigError
from audit_cli.db import Store
from audit_cli.logs import get_logger
from audit_cli.processing.target import Target, resolve_project

log = get_logger("checks")

checks_app = typer.Typer(
    help=(
        "Check stored claims against the code: audit checks run takes every claim to a verdict. Verbs: run, status, "
        "stop, list, accept, diff, write, triage.\n\n"
        "Needs claims first: run audit claims extract on the same path. write needs checks.writer in audit.toml to name an agent "
        "with a model and its provider's key; triage needs a question switched on under decisions (failure, judge, link). "
        "A claim is "
        "written once and again only when its text changes, its check is judged wrong, or a file it was decided "
        "from changes; a check runs again only when a file it reads changes."
    ),
    no_args_is_help=True,
)

_PATH = typer.Argument(
    help="Whose claims: any folder in the repository (all its claims), or a bundle or concept file to narrow them.",
    show_default=False,
)
_CONFIG = typer.Option(
    "--config", "-c", metavar="audit.toml", help="Settings file. Default: audit.toml in the repository root."
)
_JSON = typer.Option("--json", help="Print one JSON object instead of text, for scripts.")
_DEBUG = typer.Option("--debug", help="Log debug events too, whatever logging.level says.")

Loader = Callable[..., tuple[Target, Config]]
Refuser = Callable[[str, str], typer.Exit]


class _Env:
    """What every checks command needs from the main CLI: its loader and its refusal, set by ``attach``."""

    load: Loader
    refuse: Refuser
    scope: Callable[[Target], set[str] | None]


ENV = _Env()


def attach(app: typer.Typer, load: Loader, refuse: Refuser, scope: Callable[[Target], set[str] | None]) -> None:
    """Add the checks group to ``app``, using the main CLI's loader, refusal and scope."""
    ENV.load, ENV.refuse, ENV.scope = load, refuse, scope
    app.add_typer(checks_app, name="checks")


def _open(verb: str, path: plb.Path, config_path: plb.Path | None, debug: bool) -> tuple[Target, Config, Store, Checks]:
    """Load settings, open the database, and refuse when it holds no claims for the path."""
    target, config = ENV.load(verb, path, config_path, debug, resolve=resolve_project)
    database = config.database_path(target.project_root)
    if not database.exists():
        raise ENV.refuse(verb, f"no claims stored for {path}: run audit claims extract {path} first")
    store = Store(database)
    repo = Repository(target.project_root, config.files)
    stage = Checks(store, repo, config, target.bundle, ENV.scope(target))
    if not stage.claims() and target.files is not None and not path.is_file():
        # A folder with no claims of its own (a prototype or scratch folder inside the bundle) means the repository.
        stage = Checks(store, repo, config, target.bundle, None)
    if not stage.claims():
        store.__exit__(None, None, None)
        raise ENV.refuse(verb, f"no claims stored for {path}: run audit claims extract {path} first")
    return target, config, store, stage


def _record(store: Store, verb: str, started: float, report: dict[str, Any]) -> None:
    """Record the pass in the database and log it."""
    seconds = round(time.monotonic() - started, 1)
    when = dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()
    store.record_pass(verb, when, seconds, {k: v for k, v in report.items() if k not in {"rows"}})
    fields = {k: v for k, v in report.items() if k not in {"rows", "seconds"}}
    log.info(verb.replace(" ", "_") + "_done", seconds=seconds, **fields)


def _tokens(stages: list[dict[str, Any]]) -> str:
    """Return one line of what the model stages spent."""
    used = [s for s in stages if s["calls"]]
    if not used:
        return "model calls: none"
    parts = [
        f"{s['name']} {s['calls']} calls, {s['tokens_in']:,} in ({s['tokens_cached']:,} cached), {s['tokens_out']:,} out"
        for s in used
    ]
    return "model calls: " + "; ".join(parts)


STATUSES = ["holds", "fails", "reason", "settled", "none", "flagged", "unrun", "weak", "unsure", "accepted"]


def _matches(row: dict[str, Any], wanted: set[str]) -> bool:
    """Whether a listed claim has one of the statuses asked for."""
    status = row["status"]
    return (
        not wanted
        or status in wanted
        or "settled" in wanted
        and status.startswith("settled")
        or "none" in wanted
        and status == "no check"
        or "flagged" in wanted
        and row["flagged"]
        or bool(row["trust"])
        and row["trust"] in wanted
    )


def _print_row(row: dict[str, Any], details: bool) -> None:
    """Print one claim's line, and with ``details`` its check, what failed and its triage."""
    strength = f" {row['strength']}" if row["strength"] else ""
    flag = " [flagged: the fix changed what it expects]" if row["flagged"] else ""
    trust = []
    if row["mutants"]:
        trust.append(f"noticed {row['killed']}/{row['mutants']} changes")
    if row["link_verdict"]:
        trust.append(f"tests {row['link_verdict']} {row['link_score']:.2f}")
    level = {"weak": " WEAK", "unsure": " UNSURE", "accepted": " weak, accepted"}.get(row["trust"], "")
    shown = f" ({', '.join(trust)})" if trust else ""
    typer.echo(f"  {row['claim_id']} {row['status']}{strength}{level}{shown}{flag}: {row['claim']}")
    if not details:
        return
    if row["accepted_by"]:
        typer.echo(f"      accepted by {row['accepted_by']}: {row['accepted_note']}")
    if row["why"]:
        typer.echo(f"      why: {row['why']}")
    for step in row["steps"]:
        typer.echo(f"      step: {json.dumps(step)}")
    for step in row["failed_steps"]:
        typer.echo(f"      failed: {str(step.get('detail', ''))[:200]}")
    if row["triage"]:
        t = row["triage"]
        typer.echo(f"      triage ({t['question']}): {t['verdict']} {t['score']:.2f}")
    for change in row["survived"][:3]:
        typer.echo(f"      did not notice: {change}")
    if row["reads"]:
        typer.echo(f"      reads: {', '.join(row['reads'][:8])}" + (" ..." if len(row["reads"]) > 8 else ""))


@checks_app.command(
    "list",
    epilog=(
        "Examples:\n\n  audit checks list\n\n  audit checks list --status fails --details\n\n"
        "  audit checks list --claim 1f23c8cc0e4e\n\n"
        "Reads the database only: no model, no run. Each claim shows its id, status and claim; statuses are holds or "
        "fails (as of the last audit checks run), reason, settled true or false, unrun, or no check. --details adds "
        "the check's why and steps, what failed, the triage verdict and the files it reads. Each holding check "
        "shows how many small changes to its code it noticed (mutation testing, no model) and, after triage, "
        "whether it tests the claim itself, a nearby fact, a keyword or nothing related; weak lists holding checks "
        "that noticed no change or test less than a nearby fact.\n\n"
        "Exit 0 when listed; 2 when the path or settings are wrong or no claims are stored."
    ),
)
def list_command(
    path: Annotated[plb.Path, _PATH] = plb.Path("."),
    config_path: Annotated[plb.Path | None, _CONFIG] = None,
    status: Annotated[
        list[str] | None,
        typer.Option("--status", metavar="fails", help=f"Only these: {', '.join(STATUSES)}. Repeatable."),
    ] = None,
    claim_id: Annotated[
        str | None, typer.Option("--claim", metavar="1f23c8cc0e4e", help="One claim by id, with details.")
    ] = None,
    details: Annotated[bool, typer.Option("--details", help="Add each check's why, steps, failures, triage.")] = False,
    as_json: Annotated[bool, _JSON] = False,
    debug: Annotated[bool, _DEBUG] = False,
) -> None:
    """List claims with their checks, results and triage."""
    unknown = sorted(set(status or []) - set(STATUSES))
    if unknown:
        raise ENV.refuse("checks list", f"--status {unknown[0]} is not one of {', '.join(STATUSES)}")
    _, _, store, stage = _open("checks list", path, config_path, debug)
    with store:
        rows = [r for r in listing(stage) if _matches(r, set(status or []))]
    if claim_id is not None:
        rows = [r for r in rows if r["claim_id"].startswith(claim_id)]
    if as_json:
        typer.echo(json.dumps({"claims": rows}))
        return
    concept = None
    for row in rows:
        if row["concept"] != concept:
            concept = row["concept"]
            typer.echo(concept)
        _print_row(row, details or claim_id is not None)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    typer.echo(f"{len(rows)} claims: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))


@checks_app.command(
    "diff",
    epilog=(
        "Examples:\n\n  audit checks diff .\n\n  audit checks diff . --json\n\n"
        "No model, no write. Each claim is new, unrun, changed (a file it reads changed), failing, rewrite (its "
        "check was judged wrong) or up to date. Settled claims are settled again by every run, free, and do not "
        "change the exit.\n\n"
        "Exit 0 when nothing needs writing or running; 1 when something does; 2 when the path or settings are wrong "
        "or no claims are stored."
    ),
)
def diff_command(
    path: Annotated[plb.Path, _PATH] = plb.Path("."),
    config_path: Annotated[plb.Path | None, _CONFIG] = None,
    as_json: Annotated[bool, _JSON] = False,
    debug: Annotated[bool, _DEBUG] = False,
) -> None:
    """Show which claims need a check written or run."""
    _, _, store, stage = _open("checks diff", path, config_path, debug)
    with store:
        report = summary(stage.plan())
    if as_json:
        typer.echo(json.dumps(report))
    else:
        typer.echo(f"{report['claims']} claims: " + ", ".join(f"{k} {v}" for k, v in report["by_status"].items()))
        for row in report["claims_to_write"]:
            typer.echo(f"  write ({row['status']}): {row['claim']}")
        for row in report["claims_to_run"]:
            typer.echo(f"  run ({row['status']}): {row['claim']}")
        typer.echo(
            f"{report['to_write']} to write, {report['to_run']} to run, {report['settled']} settled (settled again by run)"
        )
    if report["to_write"] or report["to_run"]:
        raise typer.Exit(1)


def _process_started(pid: int | None) -> str:
    """Return when a process started, as ps prints it, or "" when no such process is running."""
    if not pid:
        return ""
    out = subprocess.run(
        ["ps", "-o", "lstart=", "-p", str(pid)],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "TZ": "UTC", "LC_ALL": "C"},  # the same text whatever the caller's time zone and language
    )
    return out.stdout.strip()


def _alive(pid: int | None, started: str) -> bool:
    """Whether the process that started a job is still running: same id and same start time, so an id reused by
    another program after the run died does not count."""
    now = _process_started(pid)
    return bool(now) and (not started or now == started)


def _running_job(store: Store) -> dict[str, Any] | None:
    """Return the run that is going now, marking runs whose process has gone as died."""
    for job in store.jobs(limit=20):
        if job["status"] not in {"running", "starting"}:
            continue
        if _alive(job["pid"], job["pid_started"]):
            return job
        store.update_job(job["id"], status="died", error=job["error"] or "its process ended without saying how")
    return None


def _claim(verb: str, store: Store, args: list[str], job_id: int | None = None) -> int:
    """Take the project's one run slot for this process, or refuse (closing the store) when a live run holds it.

    Two runs would write the same claims twice, so run and write each take the slot first, in one transaction.
    """
    me = os.getpid()
    claimed, holder = store.claim_job(verb, args, me, _process_started(me), _alive, job_id)
    if claimed is None:
        assert holder is not None
        store.__exit__(None, None, None)
        raise ENV.refuse(
            verb,
            f"run {holder['id']} is already going (pid {holder['pid']}, {holder['stage'] or 'starting'}, "
            f"{holder['done']}/{holder['total']}): see audit checks status, or stop it with audit checks stop",
        )
    return claimed


def _finish(
    store: Store, job_id: int, error: BaseException | None = None, summary: dict[str, Any] | None = None
) -> None:
    """Mark a job done, or stopped or failed with the error that ended it."""
    if error is None:
        store.update_job(job_id, status="done", stage="done", summary=summary or {})
    elif isinstance(error, typer.Exit):  # a refusal: its reason is already printed
        store.update_job(job_id, status="refused", error="refused before it started; see its output")
    else:
        status = "stopped" if isinstance(error, KeyboardInterrupt) else "failed"
        store.update_job(job_id, status=status, error=f"{type(error).__name__}: {error}"[:500])


def _job_tokens(stage: Checks) -> dict[str, int]:
    """Return the tokens the write's calls spent so far."""
    return {
        "tokens_in": sum(s.tokens_in for s in stage.spent),
        "tokens_out": sum(s.tokens_out for s in stage.spent),
        "tokens_cached": sum(s.tokens_cached for s in stage.spent),
        "calls": sum(s.calls for s in stage.spent),
    }


def _writer(verb: str, config: Config, store: Store) -> Any:
    """Return the checks.writer model, or refuse when it is not set up; the caller's ``with store`` closes the store."""
    agent = config.agents[config.checks.writer]
    if not agent.model.strip():
        raise ENV.refuse(verb, f"set a model for agents.{config.checks.writer}.model (checks.writer)")
    try:
        return build_llm(agent, config.providers[agent.provider])
    except ConfigError as error:
        raise ENV.refuse(verb, str(error)) from error


def _write(
    stage: Checks,
    store: Store,
    llm: Any,
    rewrite_failing: bool,
    job_id: int | None = None,
    only: set[str] | None = None,
    runner: asyncio.Runner | None = None,
) -> dict[str, Any]:
    """Write the checks that need writing, with a progress bar and the job's progress, and record the pass.

    ``runner`` is the event loop of a longer command, so later stages reuse the model's connections; else its own.
    """
    started = time.monotonic()
    claims = len(only) if only else summary(stage.plan())["to_write"]
    if job_id is not None:
        store.update_job(job_id, stage="write", done=0, total=claims)
    done = 0

    def progress(n: int) -> None:
        """Advance the bar and the job by ``n`` claims."""
        nonlocal done
        done += n
        bar.update(n)
        if job_id is not None:
            store.update_job(job_id, done=done, summary=_job_tokens(stage))

    with tqdm(total=claims, desc="checks", unit="claim", file=sys.stderr, disable=None) as bar:
        report = (runner.run if runner else asyncio.run)(
            stage.write(llm, rewrite_failing, on_group=progress, only=only or None)
        )
    _record(store, "checks write", started, report)
    return report


def _print_write(report: dict[str, Any]) -> None:
    """Print what a write did and spent."""
    outcome = report.get("outcome", {})
    typer.echo(f"{report['claims']} claims, {report['to_write']} to write, {report['pruned']} old checks pruned")
    if outcome:
        typer.echo(
            f"written: {outcome['holds']} hold, {outcome['fails']} fail, {outcome['reasons']} reasons, "
            f"{outcome['unanswered']} unanswered; {outcome['fixed_to_hold']} held after the fix call"
        )
        if outcome["expectation_changed"]:
            typer.echo(f"{outcome['expectation_changed']} fixed checks expect something else now: read them")
        if outcome["reason_refused"]:
            typer.echo(f"{outcome['reason_refused']} failing checks kept: a reason may not replace one")
    typer.echo(_tokens(report["stages"]))
    for claim_id, problem in report.get("errors", {}).items():
        typer.echo(f"not written: {claim_id}: {problem}", err=True)


def _bar(desc: str, store: Store, job_id: int | None, stage_name: str) -> tuple[Any, Callable[[int, int], None]]:
    """Return a progress bar on stderr and a callback that moves it and the job to ``done`` of ``total``."""
    bar = tqdm(desc=desc, unit="claim", file=sys.stderr, disable=None)

    def moved(done: int, total: int) -> None:
        """Move the bar and the job."""
        bar.total = total
        bar.n = done
        bar.refresh()
        if job_id is not None and (done == total or done % 10 == 0):
            store.update_job(job_id, stage=stage_name, done=done, total=total)

    return bar, moved


def _triage(
    stage: Checks, store: Store, config: Config, job_id: int | None = None, runner: asyncio.Runner | None = None
) -> dict[str, Any]:
    """Ask the decision questions switched on in [decisions], with a progress bar, and record the pass."""
    started = time.monotonic()
    bar, moved = _bar("triage", store, job_id, "triage")

    async def go() -> dict[str, Any]:
        """Run triage with one HTTP client."""
        async with httpx.AsyncClient() as client:
            return await stage.triage(Decider(config.decisions, client), on_question=moved)

    with bar:
        report = (runner.run if runner else asyncio.run)(go())
    _record(store, "checks triage", started, report)
    for claim_id, problem in report["errors"].items():
        typer.echo(f"not triaged: {claim_id}: {problem}", err=True)
    return report


def _print_triage(report: dict[str, Any]) -> None:
    """Print the ranked failures, false settled claims and judgements."""
    for row in report["ranked_failures"]:
        typer.echo(f"{row['score']:.2f} {row['verdict']}: {row['claim']}")
    for row in report["settled_false"]:
        typer.echo(f"settled false: {row['claim']}")
    for row in report["judgements"]:
        typer.echo(f"judged {row['verdict']} ({row['score']:.2f}): {row['claim']}")
    if report.get("links"):
        levels = ", ".join(f"{level} {n}" for level, n in report["links"].items())
        typer.echo(f"link: {levels} (what checks test; audit checks list --status weak --details)")
    typer.echo(
        f"{report['failures']} failures, {report['judged']} judged; {report['asked']} asked, "
        f"{report['already_asked']} already answered; {report['decision_calls']} decision calls"
    )


def _print_run(report: dict[str, Any]) -> None:
    """Print each claim that does not hold, then the counts."""
    for row in report["rows"]:
        if row["status"] == "fails":
            typer.echo(f"fails: {row['claim']}  [{row['claim_id']}]")
            for step in row["failed_steps"]:
                typer.echo(f"    {str(step.get('detail', ''))[:160]}")
    counts = ", ".join(f"{k} {v}" for k, v in sorted(report["counts"].items()))
    typer.echo(f"{report['claims']} claims: {counts}; {report['ran']} ran, {report['reused']} unchanged")
    if report.get("weak"):
        typer.echo(f"{report['weak']} holding checks look weak: audit checks list --status weak --details")


def _run_all(
    stage: Checks,
    store: Store,
    config: Config,
    llm: Any,
    everything: bool,
    no_triage: bool,
    job_id: int,
    strengthen_llm: Any = None,
) -> dict[str, Any]:
    """Write what needs writing, run every check, triage, and rewrite weak checks once with what they missed; report
    progress to the job as each stage starts.

    Every stage runs in one event loop: langchain_openai shares one connection pool between all its clients, and a
    pool used in a loop that has closed fails with "Event loop is closed".
    """
    out: dict[str, Any] = {}
    with asyncio.Runner() as runner:
        if llm is not None:
            out["write"] = _write(stage, store, llm, rewrite_failing=False, job_id=job_id, runner=runner)
        started = time.monotonic()
        store.update_job(job_id, stage="run")
        bar, moved = _bar("run", store, job_id, "run")
        with bar:
            out["run"] = stage.run(everything, on_check=moved)
        _record(store, "checks run", started, out["run"])
        if config.decisions.enabled and not no_triage:
            store.update_job(job_id, stage="triage")
            try:
                out["triage"] = _triage(stage, store, config, job_id, runner)
            except ConfigError as error:
                typer.echo(f"triage skipped: {error}", err=True)
        if strengthen_llm is not None and any(row["weak"] for row in listing(stage)):
            store.update_job(job_id, stage="strengthen")
            started = time.monotonic()
            bar, moved = _bar("strengthen", store, job_id, "strengthen")
            done = 0

            def ticked(n: int) -> None:
                """Advance the strengthen bar by ``n`` claims."""
                nonlocal done
                done += n
                moved(done, max(done, bar.total or 0))

            async def strengthened() -> dict[str, Any]:
                """Strengthen, asking the link question of each rewrite when it is switched on."""
                if not config.decisions.link.enabled:
                    return await stage.strengthen(strengthen_llm, None, on_group=ticked)
                async with httpx.AsyncClient() as client:
                    return await stage.strengthen(strengthen_llm, Decider(config.decisions, client), on_group=ticked)

            with bar:
                out["strengthen"] = runner.run(strengthened())
            _record(store, "checks strengthen", started, out["strengthen"])
    out["run"]["weak"] = sum(1 for row in listing(stage) if row["weak"])  # after triage and strengthen
    return out


def _job_summary(stage: Checks, out: dict[str, Any]) -> dict[str, Any]:
    """Return what a finished run leaves in its job: the counts, what failed to write, and the tokens."""
    return {
        **out["run"]["counts"],
        "weak": out["run"].get("weak", 0),
        "not_written": len(out.get("write", {}).get("errors", {})),
        **_job_tokens(stage),
    }


def _start_background(store: Store, config: Config, root: plb.Path, args: list[str], job_id: int) -> None:
    """Hand the claimed job to a detached run, logging next to the project's log, and print how to follow it.

    This process holds the slot until the child takes it over: the job's pid becomes the child's, with its start
    time, so no other run can start in between.
    """
    log_dir = config.log_path(root).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{config.project_key(root)}-checks-run-{job_id}.log"
    with log_file.open("w") as log:
        child = subprocess.Popen(
            [sys.executable, "-m", "audit_cli", *args, "--job", str(job_id)],
            stdout=log,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,  # it outlives this terminal, and stop ends its whole process group
        )
    store.update_job(job_id, pid=child.pid, pid_started=_process_started(child.pid), log_path=str(log_file))
    typer.echo(f"started run {job_id} in the background (pid {child.pid})")
    typer.echo("follow it: audit checks status    stop it: audit checks stop")
    typer.echo(f"log: {log_file}")


@checks_app.command(
    "run",
    epilog=(
        "Examples:\n\n  audit checks run\n\n  audit checks run --no-write --all\n\n"
        "Takes every claim to a verdict: writes checks for claims that need one (new, or judged wrong) with "
        "checks.writer, runs every check (one whose files are unchanged keeps its last result; settled claims are "
        "settled again), then asks the decision questions switched on in audit.toml: why each check failed, what a "
        "reason-only claim's lines show, whether each check tests its claim. "
        "--no-write runs the stored checks only, with no model. --background starts it detached: audit checks "
        "status shows its stage, claims done, tokens and errors, and audit checks stop ends it. Only one run (or "
        "write) per project goes at a time.\n\n"
        "Exit 0 when every check holds; 1 when one fails, a settled claim is false or a claim was left unanswered; "
        "2 when the path or settings are wrong, the writer's key is missing, another run is going, or no claims are "
        "stored. A decision question that cannot be asked is reported and does not change the exit."
    ),
)
def run_command(
    path: Annotated[plb.Path, _PATH] = plb.Path("."),
    config_path: Annotated[plb.Path | None, _CONFIG] = None,
    everything: Annotated[bool, typer.Option("--all", help="Run every check, changed or not.")] = False,
    no_write: Annotated[bool, typer.Option("--no-write", help="Run stored checks only; call no model.")] = False,
    no_triage: Annotated[bool, typer.Option("--no-triage", help="Skip the decision model.")] = False,
    background: Annotated[
        bool, typer.Option("--background", help="Start it detached and return; follow it with audit checks status.")
    ] = False,
    job: Annotated[int | None, typer.Option("--job", hidden=True, help="The job a background run reports to.")] = None,
    as_json: Annotated[bool, _JSON] = False,
    debug: Annotated[bool, _DEBUG] = False,
) -> None:
    """Check every claim: write what is missing, run, and rank failures."""
    target, config, store, stage = _open("checks run", path, config_path, debug)
    args = ["checks", "run", str(path.resolve())]
    args += ["-c", str(config_path.resolve())] if config_path else []
    args += [
        f
        for f, on in (("--all", everything), ("--no-write", no_write), ("--no-triage", no_triage), ("--debug", debug))
        if on
    ]
    job_id = _claim("checks run", store, args, job)  # before anything slow: the slot is taken in one transaction
    if background:
        with store:
            _start_background(store, config, target.project_root, args, job_id)
        return
    with store:
        try:
            needs_writing = summary(stage.plan())["to_write"] > 0
            llm = _writer("checks run", config, store) if needs_writing and not no_write else None
            writer_set = bool(config.agents[config.checks.writer].model.strip())
            strengthen_llm = llm or (_writer("checks run", config, store) if writer_set and not no_write else None)
            out = _run_all(stage, store, config, llm, everything, no_triage, job_id, strengthen_llm)
        except BaseException as error:
            _finish(store, job_id, error)
            raise
        _finish(store, job_id, summary=_job_summary(stage, out))
    if as_json:
        typer.echo(json.dumps(out))
    else:
        if "write" in out:
            _print_write(out["write"])
        _print_run(out["run"])
        if "triage" in out:
            _print_triage(out["triage"])
        if "strengthen" in out:
            st = out["strengthen"]
            typer.echo(
                f"weak checks: {st['tried']} rewritten with what they missed, {st['improved']} better and kept, "
                f"{st['accepted']} accepted as they were until their code changes, {st['unanswered']} unanswered "
                "(audit checks list --status accepted --details)"
            )
            typer.echo(_tokens(st["stages"]))
        elif needs_writing and no_write:
            typer.echo("claims with no check were not written (--no-write)")
    unanswered = out.get("write", {}).get("outcome", {}).get("unanswered", 0)  # includes claims whose call failed
    settled_false = out.get("triage", {}).get("settled_false") or any(
        r["status"] == "fails" and r["kind"] == "settled" for r in out["run"]["rows"]
    )
    if out["run"]["counts"].get("fails") or settled_false or unanswered:
        raise typer.Exit(1)


@checks_app.command(
    "write",
    epilog=(
        "Examples:\n\n  audit checks write .\n\n  audit checks write . --rewrite-failing --json\n\n"
        "Only the writing part of audit checks run. Claims the repository settles alone (a file is gone, a flag's "
        "default) need no model. The rest go to the checks.writer agent with the lines found for them, grouped by "
        "file; failing checks go back once with what each step saw. A fix that changes what a failed step expects "
        "is flagged for a person.\n\n"
        "Exit 0 when every claim got a check, reason or verdict; 1 when one was left unanswered (retried next "
        "time); 2 when the path, settings or key are wrong."
    ),
)
def write_command(
    path: Annotated[plb.Path, _PATH] = plb.Path("."),
    config_path: Annotated[plb.Path | None, _CONFIG] = None,
    rewrite_failing: Annotated[
        bool, typer.Option("--rewrite-failing", help="Also rewrite every failing check, drift or not.")
    ] = False,
    claim_ids: Annotated[
        list[str] | None,
        typer.Option("--claim", metavar="1f23c8cc0e4e", help="Rewrite only this claim (an id or prefix). Repeatable."),
    ] = None,
    as_json: Annotated[bool, _JSON] = False,
    debug: Annotated[bool, _DEBUG] = False,
) -> None:
    """Write checks for the claims that need one, and run them."""
    _, config, store, stage = _open("checks write", path, config_path, debug)
    job_id = _claim("checks write", store, ["checks", "write", str(path.resolve())])
    with store:
        try:
            llm = _writer("checks write", config, store)
            report = _write(stage, store, llm, rewrite_failing, job_id, set(claim_ids or []))
        except BaseException as error:
            _finish(store, job_id, error)
            raise
        _finish(store, job_id, summary=_job_tokens(stage))
    if as_json:
        typer.echo(json.dumps(report))
    else:
        _print_write(report)
    if report.get("outcome", {}).get("unanswered"):
        raise typer.Exit(1)


@checks_app.command(
    "triage",
    epilog=(
        "Examples:\n\n  audit checks triage .\n\n  audit checks triage . --json\n\n"
        "Only the decision part of audit checks run. Each question is switched on, with its provider and model, "
        "in audit.toml: decisions.failure (did a failing check find drift, or is it wrong; the next write rewrites "
        "wrong ones), decisions.judge (what a reason-only claim's lines show), decisions.link (whether a check tests "
        "its claim). Nothing is asked twice for the same check and result.\n\n"
        "Exit 0 when no failure looks like drift; 1 when one does (score above 0.5) or a settled claim is false; 2 "
        "when no question is switched on, a provider's key is missing or refused, or no claims are stored."
    ),
)
def triage_command(
    path: Annotated[plb.Path, _PATH] = plb.Path("."),
    config_path: Annotated[plb.Path | None, _CONFIG] = None,
    as_json: Annotated[bool, _JSON] = False,
    debug: Annotated[bool, _DEBUG] = False,
) -> None:
    """Rank failing checks by how likely they found drift."""
    _, config, store, stage = _open("checks triage", path, config_path, debug)
    if not config.decisions.enabled:
        store.__exit__(None, None, None)
        raise ENV.refuse(
            "checks triage",
            "no decision question is on: set enabled, provider and model under [decisions.failure], "
            "[decisions.judge] or [decisions.link], with the provider under [decisions.providers.NAME]",
        )
    with store:
        try:
            report = _triage(stage, store, config)
        except ConfigError as error:
            raise ENV.refuse("checks triage", str(error)) from error
    if as_json:
        typer.echo(json.dumps(report))
    if report["errors"] and not report["asked"] and not report["already_asked"]:
        raise ENV.refuse("checks triage", "every question failed: " + next(iter(report["errors"].values())))
    if not as_json:
        _print_triage(report)
    if any(r["score"] > 0.5 for r in report["ranked_failures"]) or report["settled_false"]:
        raise typer.Exit(1)


def _elapsed(job: dict[str, Any]) -> str:
    """Return how long a job ran, or has been running, as minutes and seconds."""
    start = dt.datetime.fromisoformat(job["started_at"])
    end = dt.datetime.fromisoformat(job["finished_at"]) if job["finished_at"] else dt.datetime.now(dt.UTC)
    seconds = int((end - start).total_seconds())
    return f"{seconds // 60}m{seconds % 60:02d}s"


@checks_app.command(
    "status",
    epilog=(
        "Examples:\n\n  audit checks status\n\n  audit checks status --json\n\n"
        "Shows the latest runs (the one going first): its stage (write, run, triage, done), claims written out of "
        "those to write, time, model calls and tokens so far, how it ended, its error and its log; then the checks "
        "the database holds now. A run whose process ended without finishing is marked died. Reads only.\n\n"
        "Exit 0 when shown; 2 when the path or settings are wrong or no claims are stored."
    ),
)
def status_command(
    path: Annotated[plb.Path, _PATH] = plb.Path("."),
    config_path: Annotated[plb.Path | None, _CONFIG] = None,
    as_json: Annotated[bool, _JSON] = False,
    debug: Annotated[bool, _DEBUG] = False,
) -> None:
    """Show the run going now, the last runs, and where the checks stand."""
    _, _, store, stage = _open("checks status", path, config_path, debug)
    with store:
        _running_job(store)  # marks runs whose process has gone
        jobs = store.jobs(limit=5)
        counts: dict[str, int] = {}
        for row in listing(stage):
            counts[row["status"]] = counts.get(row["status"], 0) + 1
            counts["weak"] = counts.get("weak", 0) + int(row["weak"])
    if as_json:
        typer.echo(json.dumps({"jobs": jobs, "checks": counts}))
        return
    for job in jobs:
        tokens = job["summary"]
        spent = (
            f", {tokens.get('calls', 0)} calls, {tokens.get('tokens_in', 0):,} in "
            f"({tokens.get('tokens_cached', 0):,} cached), {tokens.get('tokens_out', 0):,} out"
            if tokens.get("calls")
            else ""
        )
        progress = f" {job['done']}/{job['total']} claims" if job["total"] else ""
        typer.echo(f"run {job['id']}: {job['status']}, {job['stage'] or '-'}{progress}, {_elapsed(job)}{spent}")
        if job["error"]:
            typer.echo(f"    error: {job['error']}")
        if job["log_path"]:
            typer.echo(f"    log: {job['log_path']}")
    if not jobs:
        typer.echo("no runs yet")
    typer.echo("checks: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))


@checks_app.command(
    "stop",
    epilog=(
        "Examples:\n\n  audit checks stop\n\n"
        "Ends the run that is going (a background one, or one in another terminal) and everything it started. "
        "Checks it already wrote stay stored; the next run writes the rest.\n\n"
        "Exit 0 when a run was stopped or none was going; 2 when the path or settings are wrong."
    ),
)
def stop_command(
    path: Annotated[plb.Path, _PATH] = plb.Path("."),
    config_path: Annotated[plb.Path | None, _CONFIG] = None,
    debug: Annotated[bool, _DEBUG] = False,
) -> None:
    """Stop the run that is going."""
    _, _, store, _ = _open("checks stop", path, config_path, debug)
    with store:
        job = _running_job(store)
        if job is None:
            typer.echo("no run is going")
            return
        pid = job["pid"]
        try:
            if os.getpgid(pid) == pid:  # a background run leads its own process group: end it and what it started
                os.killpg(pid, signal.SIGTERM)
            else:  # a run in another terminal: end that process only, not the rest of its shell's job
                os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass  # it ended just now
        except PermissionError as error:
            raise ENV.refuse("checks stop", f"run {job['id']} (pid {pid}) belongs to another user: {error}") from error
        store.update_job(job["id"], status="stopped", error="stopped with audit checks stop")
    typer.echo(f"stopped run {job['id']} (pid {pid})")


@checks_app.command(
    "accept",
    epilog=(
        'Examples:\n\n  audit checks accept 6f7fc8dd --note "the query tests the matrix itself"\n\n'
        "  audit checks accept 6f7fc8dd --undo\n\n"
        "Marks a weak or unsure check as checked by you: it stops counting as weak, and run no longer tries to "
        "rewrite it. The mark goes when the check is rewritten. --undo clears it. Writes the database only.\n\n"
        "Exit 0 when marked; 2 when no stored check matches the id, or it matches more than one."
    ),
)
def accept_command(
    claim_id: Annotated[str, typer.Argument(metavar="CLAIM_ID", help="The claim's id, or a prefix of it.")],
    path: Annotated[plb.Path, _PATH] = plb.Path("."),
    config_path: Annotated[plb.Path | None, _CONFIG] = None,
    note: Annotated[str, typer.Option("--note", metavar="WHY", help="Why it is good enough.")] = "",
    undo: Annotated[bool, typer.Option("--undo", help="Clear the mark instead.")] = False,
    debug: Annotated[bool, _DEBUG] = False,
) -> None:
    """Mark a weak check as checked by a person."""
    _, _, store, _ = _open("checks accept", path, config_path, debug)
    with store:
        matches = [cid for cid in store.checks() if cid.startswith(claim_id)]
        if len(matches) != 1:
            raise ENV.refuse("checks accept", f"{len(matches)} stored checks match {claim_id!r}; give more of the id")
        if undo:  # clear the mark and any rewrite attempt, so run tries it again
            store.set_acceptance(matches[0], "", "", strengthen_key="")
        else:
            store.set_acceptance(matches[0], "person", note or "checked by hand")
    typer.echo(f"{'cleared' if undo else 'accepted'}: {matches[0]}")
