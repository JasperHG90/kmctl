"""The ``audit`` command: extract an OKF bundle's claims into the project's database, and diff against it."""

import asyncio
import json
import os
import pathlib as plb
import sys
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict
from typing import Annotated

import typer
from dotenv import find_dotenv, load_dotenv
from pydantic import BaseModel, Field
from tqdm import tqdm

from audit_cli.checks_cli import attach
from audit_cli.claims.corrections import CorrectionJudge, CorrectionsReport, judge_corrections
from audit_cli.claims.diff import DiffReport, diff
from audit_cli.claims.extractor import ClaimExtractor, build_llm
from audit_cli.claims.models import CorrectionLink
from audit_cli.claims.runner import ClaimsReport, ClaimsRunner, Run, pending
from audit_cli.config import DEFAULT_CONFIG_NAME, DEFAULT_TOML, Config, ConfigError, load_config
from audit_cli.db import Store, StoredClaim
from audit_cli.logs import configure_logging, get_logger
from audit_cli.processing.chunker import BundleChunker, Chunk, SentenceSplitter
from audit_cli.processing.target import Target, TargetError, resolve_project, resolve_target

REFUSED = 2  # the verb could not start: a bad path, config or missing key
log = get_logger("cli")

app = typer.Typer(
    help="Extract the claims an OKF bundle makes into a per-project SQLite database, and check them against the "
    "code. Verbs: claims, checks, init.",
    no_args_is_help=True,
)
claims_app = typer.Typer(
    help="Extract a bundle's claims, see what extracting would change, or list what is stored. Verbs: extract, diff, "
    "list.",
    no_args_is_help=True,
)
app.add_typer(claims_app, name="claims")

_PATH_ARGUMENT = typer.Argument(
    help="An OKF bundle folder, a repository with a .okf/ folder, or one concept file (.md) inside a bundle.",
    show_default=False,
)
_CONFIG_OPTION = typer.Option(
    "--config",
    "-c",
    help=f"The TOML settings file. Default: {DEFAULT_CONFIG_NAME} in the repository root, then in the current "
    "folder, else built-in defaults.",
)
_JSON_OPTION = typer.Option("--json", help="Print one JSON object instead of text, for scripts.")
_DEBUG_OPTION = typer.Option(
    "--debug", help="Log debug events too (each model call and stored result), whatever logging.level says."
)


def _refuse(verb: str, message: str) -> typer.Exit:
    """Print why a verb cannot start, on stderr, and return the exit to raise."""
    typer.echo(f"audit {verb}: refused: {message}", err=True)
    return typer.Exit(REFUSED)


def _load(
    verb: str,
    path: plb.Path,
    config_path: plb.Path | None,
    debug: bool,
    resolve: Callable[[plb.Path], Target] = resolve_target,
) -> tuple[Target, Config]:
    """Resolve the path (with ``resolve``) and load the .env file, settings and log.

    ``telemetry.enabled`` sets LANGSMITH_TRACING to true or false. LangSmith reads everything else from its own
    environment variables (LANGSMITH_API_KEY, and LANGSMITH_PROJECT or LANGSMITH_AGENT_ID with
    LANGSMITH_AGENT_ENVIRONMENT), with the .env file loaded first.
    """
    try:
        target = resolve(path)
    except TargetError as error:
        raise _refuse(verb, str(error)) from error
    load_dotenv(find_dotenv(usecwd=True))
    try:
        config = load_config(config_path, search=[target.project_root, plb.Path.cwd()])
    except ConfigError as error:
        raise _refuse(verb, str(error)) from error
    configure_logging(config.log_path(target.project_root), "debug" if debug else config.logging.level)
    for name in ("LANGSMITH_TRACING", "LANGSMITH_TRACING_V2", "LANGCHAIN_TRACING_V2"):  # the SDK reads V2 first
        os.environ[name] = "true" if config.telemetry.enabled else "false"
    return target, config


def _setup(verb: str, path: plb.Path, config_path: plb.Path | None, debug: bool) -> tuple[Target, Config, list[Chunk]]:
    """Load everything, check a model is set, and chunk what the path names."""
    target, config = _load(verb, path, config_path, debug)
    unset = config.unset_models()
    if unset:
        where = str(config.source) if config.source else f"{DEFAULT_CONFIG_NAME} (audit init writes one)"
        raise _refuse(verb, "set a model for " + ", ".join(f"agents.{n}.model" for n in unset) + f" in {where}")
    chunker = BundleChunker(
        SentenceSplitter(),
        skip_names=config.chunking.skip_names,
        skip_dirs=config.chunking.skip_dirs,
        earlier_sentences=config.chunking.earlier_sentences,
    )
    chunks = list(chunker.chunks(target.bundle, target.files))
    if not chunks:
        log.warning("refused", verb=verb, path=str(path), reason="no concept with any sentence")
        raise _refuse(verb, f"{path} holds no concept with any sentence (empty, deprecated or not a concept)")
    log.info(
        "start",
        verb=verb,
        path=str(path),
        bundle=str(target.bundle),
        files=[str(f) for f in target.files] if target.files is not None else "whole bundle",
        project_root=str(target.project_root),
        project_key=config.project_key(target.project_root),
        config=str(config.source) if config.source else "built-in defaults",
        database=str(config.database_path(target.project_root)),
        concepts=len({c.concept for c in chunks}),
        sections=len(chunks),
        runs={label: model for label, model, _ in _run_specs(config)},
        max_model_calls=config.concurrency.max_model_calls,
    )
    log.debug("settings", **config.model_dump(mode="json"))
    return target, config, chunks


def _scope(target: Target) -> set[str] | None:
    """Return the concepts a single-file target covers, or None for a whole bundle."""
    return {target.concept(f) for f in target.files} if target.files is not None else None


def _run_specs(config: Config) -> list[tuple[str, str, str]]:
    """Return each configured run's label, model and salt."""
    specs = []
    for label in config.claims.runs:
        name, _, salt = label.partition("@")
        specs.append((label, config.agents[name].model, salt))
    return specs


def _runs(config: Config, limit: asyncio.Semaphore) -> list[Run]:
    """Build one extractor per configured run, all sharing ``limit``, the bound on model calls in flight."""
    runs = []
    for label, model, salt in _run_specs(config):
        agent = config.agents[label.partition("@")[0]]
        extractor = ClaimExtractor(build_llm(agent, config.providers[agent.provider]), limit)
        runs.append(Run(label=label, model=model, salt=salt, extractor=extractor))
    return runs


def _open_store(config: Config, target: Target) -> Store:
    """Open the project's database and record which repository it belongs to."""
    store = Store(config.database_path(target.project_root))
    store.record_project(config.project_key(target.project_root), target.project_root)
    return store


def _judge(config: Config, limit: asyncio.Semaphore) -> CorrectionJudge:
    """Build the corrections judge on the first run's agent, sharing ``limit``."""
    agent = config.agents[config.claims.runs[0].partition("@")[0]]
    return CorrectionJudge(build_llm(agent, config.providers[agent.provider]), limit)


async def _extract_all(
    config: Config, store: Store, chunks: list[Chunk], on_done: Callable[[], object]
) -> tuple[ClaimsReport, CorrectionsReport]:
    """Extract the chunks, then tie their corrections, with one bound on calls built inside the running loop."""
    limit = asyncio.Semaphore(config.concurrency.max_model_calls)
    report = await ClaimsRunner(store, _runs(config, limit)).run(chunks, on_done=on_done)
    corrections = await judge_corrections(store, chunks, _judge(config, limit), failed_chunks=report.incomplete_chunks)
    return report, corrections


def _print_report(
    report: ClaimsReport, corrections: CorrectionsReport, database: plb.Path, log_file: plb.Path, as_json: bool
) -> None:
    """Print what an extraction pass did, and where the database and log are."""
    if as_json:
        out = {
            **asdict(report),
            "corrections": asdict(corrections),
            "claims_by_type": dict(report.claims_by_type.most_common()),
            "database": str(database),
            "log": str(log_file),
        }
        typer.echo(json.dumps(out))
        return
    claims = sum(report.claims_by_type.values())
    typer.echo(f"{report.chunks} sections: {report.cached} run results already stored, {report.fresh} from the model")
    typer.echo(f"{claims} claims: " + ", ".join(f"{k} {v}" for k, v in report.claims_by_type.most_common()))
    if report.fresh:
        typer.echo(f"tokens: {report.tokens_in:,} in, {report.tokens_out:,} out")
    if corrections.judged or corrections.stored or corrections.failed or corrections.skipped:
        typer.echo(
            f"corrections: {corrections.judged} judged ({corrections.links} links), {corrections.stored} already judged"
        )
    typer.echo(f"database: {database}")
    typer.echo(f"log: {log_file}")
    for chunk_id, error in report.failed.items():
        typer.echo(f"failed: {chunk_id}: {error}", err=True)
    for key, error in report.skipped_runs.items():
        typer.echo(f"run skipped: {key}: {error}", err=True)
    for key, error in report.unreadable.items():
        typer.echo(f"answer unreadable: {key}: {error[:200]}", err=True)
    for chunk_id, error in corrections.failed.items():
        typer.echo(f"correction not judged: {chunk_id}: {error[:200]}", err=True)
    for chunk_id in corrections.skipped:
        typer.echo(f"correction skipped: {chunk_id}: a section of its record failed to extract", err=True)


@claims_app.command(
    epilog=(
        "Examples:\n\n  audit claims extract .\n\n  audit claims extract .okf/decisions/0001-use-a-queue.md\n\n"
        "  audit claims extract ../other-repo --json\n\n"
        "Cuts each live concept into one section per header, with numbered sentences, and runs every section "
        "through claims.runs in order: the first run's claims stand and each later run adds claims for sentences "
        "the earlier runs skipped. A run already stored for a section's current text is read, not called again, so "
        "run audit claims diff first to see what would call a model. At most concurrency.max_model_calls calls are "
        "in flight; a progress bar on stderr counts sections done. The database is the project's file in your "
        "data folder (database in audit.toml moves it); each run appends JSON lines to the project's log in your "
        "log folder: info by default, --debug for each model call (logging in audit.toml). Then each correction "
        "section (a header starting Correction or Amended) is shown to the first run's model with the rest of its "
        "record, which says which sentences it corrects and which of their claims it overturns; those claims are "
        "marked superseded (audit claims list shows the link). A correction judged against the same text and claims "
        "is not judged again.\n\n"
        "Exit 0 when every section was extracted; 1 when a section's first run failed or an answer could not be "
        "read, or a correction could not be judged (the rest is stored, and running again retries only what went "
        "wrong); 2 when the path, settings or "
        "a provider key are wrong."
    )
)
def extract(
    path: Annotated[plb.Path, _PATH_ARGUMENT],
    config_path: Annotated[plb.Path | None, _CONFIG_OPTION] = None,
    as_json: Annotated[bool, _JSON_OPTION] = False,
    debug: Annotated[bool, _DEBUG_OPTION] = False,
) -> None:
    """Extract the claims of a bundle or one concept file into the database."""
    target, config, chunks = _setup("claims extract", path, config_path, debug)
    try:
        for name in {config.agents[label.partition("@")[0]].provider for label in config.claims.runs}:
            config.providers[name].api_key()
    except ConfigError as error:
        raise _refuse("claims extract", str(error)) from error
    started = time.monotonic()
    with _open_store(config, target) as store:
        store.replace_chunks(chunks, _scope(target))
        planned = pending(store, chunks, [(model, salt) for _, model, salt in _run_specs(config)])
        log.info(
            "extract_plan",
            sections=len(chunks),
            model_calls=planned,
            already_stored=len(chunks) * len(config.claims.runs) - planned,
        )
        with tqdm(total=len(chunks), desc="claims", unit="section", file=sys.stderr, disable=None) as progress:
            report, corrections = asyncio.run(_extract_all(config, store, chunks, lambda: progress.update(1)))
    log.info(
        "extract_done",
        seconds=round(time.monotonic() - started, 1),
        claims_by_type=dict(report.claims_by_type.most_common()),
        sections=report.chunks,
        fresh=report.fresh,
        cached=report.cached,
        failed=len(report.failed),
        unreadable=len(report.unreadable),
        claims=sum(report.claims_by_type.values()),
        tokens_in=report.tokens_in,
        tokens_out=report.tokens_out,
        corrections_judged=corrections.judged,
        correction_links=corrections.links,
        corrections_failed=len(corrections.failed),
    )
    _print_report(
        report, corrections, config.database_path(target.project_root), config.log_path(target.project_root), as_json
    )
    if report.failed or report.unreadable or corrections.failed:
        raise typer.Exit(1)


def _print_diff(report: DiffReport, as_json: bool) -> None:
    """Print what extracting would change: each concept that is not up to date, then a summary."""
    if as_json:
        typer.echo(report.model_dump_json())
        return
    for concept in report.concepts:
        if concept.status == "up to date":
            continue
        typer.echo(f"{concept.concept}: {concept.status}")
        for chunk in concept.chunks:
            if chunk.status == "up to date":
                continue
            detail = []
            if chunk.status == "changed":
                detail.append(f"+{chunk.sentences_added} / -{chunk.sentences_removed} sentences")
            if chunk.pending_runs:
                detail.append(f"{len(chunk.pending_runs)} runs to call")
            section = chunk.id.partition("#")[2]
            typer.echo(f"  #{section}: {chunk.status}" + (f" ({', '.join(detail)})" if detail else ""))
    counts = Counter(c.status for c in report.concepts)
    summary = ", ".join(f"{n} {status}" for status, n in counts.most_common())
    if report.up_to_date:
        typer.echo(f"up to date: {summary}")
    else:
        typer.echo(f"{summary}; {report.pending_calls} model calls to bring them up to date")


@claims_app.command(
    "diff",
    epilog=(
        "Examples:\n\n  audit claims diff .\n\n  audit claims diff .okf/manifesto.md --json\n\n"
        "Compares what the path holds now with the database, per concept file and section: up to date (extracted "
        "from this text by every run), new (never extracted), changed (extracted from older text; shows sentences "
        "added and removed), incomplete (same text, some runs missing) or removed (the section is gone). Counts "
        "the model calls claims extract would make. Writes nothing, calls no model and needs no key.\n\n"
        "Exit 0 when everything is up to date; 1 when extracting would change claims; 2 when the path or settings "
        "are wrong."
    ),
)
def diff_command(
    path: Annotated[plb.Path, _PATH_ARGUMENT],
    config_path: Annotated[plb.Path | None, _CONFIG_OPTION] = None,
    as_json: Annotated[bool, _JSON_OPTION] = False,
    debug: Annotated[bool, _DEBUG_OPTION] = False,
) -> None:
    """Show whether a bundle or file is fully extracted, and what extracting would change."""
    target, config, chunks = _setup("claims diff", path, config_path, debug)
    database = config.database_path(target.project_root)
    with Store(database if database.exists() else None) as store:
        first_model = config.agents[config.claims.runs[0].partition("@")[0]].model
        report = diff(store, chunks, _scope(target), _run_specs(config), corrections_model=first_model)
    log.info(
        "diff_done",
        up_to_date=report.up_to_date,
        pending_calls=report.pending_calls,
        concepts=dict(Counter(c.status for c in report.concepts)),
        sections=dict(Counter(chunk.status for c in report.concepts for chunk in c.chunks)),
    )
    _print_diff(report, as_json)
    if not report.up_to_date:
        raise typer.Exit(1)


class ListedClaim(StoredClaim):
    """A stored claim with the corrections that overturn it."""

    superseded_by: list[CorrectionLink] = Field(
        default_factory=list, description="Each correction sentence that overturns the claim; empty while it stands."
    )


class ListedDocument(BaseModel):
    """One concept file in the database: its sections, claims and corrections."""

    concept: str = Field(description="The concept id: its path in the bundle without .md.")
    sections: int = Field(description="Sections stored for it.")
    claims_by_kind: dict[str, int] = Field(description="Claims per kind, after any --kind and --current filter.")
    superseded: int = Field(default=0, description="Claims a correction overturns, after any --kind filter.")
    claims: list[ListedClaim] = Field(default_factory=list, description="Its claims, when they were asked for.")
    corrected_without_claim: list[CorrectionLink] = Field(
        default_factory=list, description="Sentences a correction changes that hold no overturned claim."
    )


class ListReport(BaseModel):
    """What the database holds for a path."""

    database: str
    documents: list[ListedDocument]


def _listing(
    store: Store, scope: set[str] | None, kinds: set[str], with_claims: bool, current_only: bool
) -> list[ListedDocument]:
    """Return each stored document in scope with its section count, claims and correction links."""
    sections = Counter(c.concept for c in store.chunks(scope))
    links = store.correction_links()
    overturning: dict[tuple[str, str], list[CorrectionLink]] = {}
    for link in links:
        if link.claim_id is not None:
            overturning.setdefault((link.target_chunk, link.claim_id), []).append(link)
    by_concept: dict[str, list[ListedClaim]] = {}
    for claim in store.claims():
        if (scope is None or claim.concept in scope) and (not kinds or claim.claim_type in kinds):
            listed = ListedClaim(
                **claim.model_dump(), superseded_by=overturning.get((claim.chunk_id, claim.claim_id), [])
            )
            by_concept.setdefault(claim.concept, []).append(listed)
    documents = []
    for concept, count in sorted(sections.items()):
        claims = by_concept.get(concept, [])
        standing = [c for c in claims if not c.superseded_by]
        shown = standing if current_only else claims
        documents.append(
            ListedDocument(
                concept=concept,
                sections=count,
                claims_by_kind=dict(Counter(c.claim_type for c in shown).most_common()),
                superseded=len(claims) - len(standing),
                claims=shown if with_claims else [],
                corrected_without_claim=[
                    l for l in links if l.claim_id is None and l.target_chunk.partition("#")[0] == concept
                ]
                if with_claims
                else [],
            )
        )
    return documents


def _print_listing(report: ListReport, as_json: bool) -> None:
    """Print each document with its claim counts, and its claims when they were asked for."""
    if as_json:
        typer.echo(report.model_dump_json())
        return
    for doc in report.documents:
        total = sum(doc.claims_by_kind.values())
        kinds = ", ".join(f"{k} {v}" for k, v in doc.claims_by_kind.items())
        superseded = f", {doc.superseded} superseded by a correction" if doc.superseded else ""
        counts = f" ({kinds})" if kinds else ""
        typer.echo(f"{doc.concept}: {doc.sections} sections, {total} claims{counts}{superseded}")
        for claim in doc.claims:
            section = claim.chunk_id.partition("#")[2]
            mark = " [superseded]" if claim.superseded_by else ""
            typer.echo(f"  #{section} [{claim.sentence_n}] {claim.claim_type}{mark}: {claim.claim}")
            if claim.reason:
                typer.echo(f"      why: {claim.reason}")
            for link in claim.superseded_by:
                typer.echo(
                    f"      superseded by #{link.correction_chunk.partition('#')[2]} [{link.correction_n}]: {link.reason}"
                )
        for link in doc.corrected_without_claim:
            typer.echo(
                f"  #{link.target_chunk.partition('#')[2]} [{link.target_n}] corrected by "
                f"#{link.correction_chunk.partition('#')[2]} [{link.correction_n}], no claim overturned: {link.reason}"
            )
    claims = sum(sum(d.claims_by_kind.values()) for d in report.documents)
    typer.echo(f"{len(report.documents)} documents, {claims} claims in {report.database}")


@claims_app.command(
    "list",
    epilog=(
        "Examples:\n\n  audit claims list\n\n  audit claims list .okf/manifesto.md\n\n"
        "  audit claims list . --claims --kind point --kind structural\n\n"
        "Lists the documents the project's database holds, each with its sections and claims per kind. For one "
        "concept file, or with --claims, it lists each claim too: section, sentence number, kind, text and the "
        "model's reason, and each correction that overturns a claim or changes a sentence. --current leaves out claims "
        "a correction overturns. Reads only; needs no model or key. A project with nothing extracted lists nothing.\n\n"
        "Exit 0 when the listing was printed; 2 when the path or settings are wrong."
    ),
)
def list_command(
    path: Annotated[
        plb.Path,
        typer.Argument(
            help="Whose claims: any folder in the repository (all of them), or a bundle or concept file to narrow them.",
            show_default=False,
        ),
    ] = plb.Path("."),
    config_path: Annotated[plb.Path | None, _CONFIG_OPTION] = None,
    with_claims: Annotated[
        bool, typer.Option("--claims", help="List every claim, not only the counts. On by default for one file.")
    ] = False,
    kind: Annotated[
        list[str] | None,
        typer.Option(
            "--kind", help="Only claims of this kind: point, structural, broad, subjective or external. Repeatable."
        ),
    ] = None,
    current: Annotated[bool, typer.Option("--current", help="Leave out claims a correction overturns.")] = False,
    as_json: Annotated[bool, _JSON_OPTION] = False,
    debug: Annotated[bool, _DEBUG_OPTION] = False,
) -> None:
    """List the documents and claims the database holds."""
    target, config = _load("claims list", path, config_path, debug, resolve=resolve_project)
    database = config.database_path(target.project_root)
    documents: list[ListedDocument] = []
    if database.exists():
        with Store(database) as store:
            documents = _listing(
                store, _scope(target), set(kind or []), with_claims or target.files is not None, current
            )
    log.info("list_done", path=str(path), documents=len(documents), database=str(database))
    _print_listing(ListReport(database=str(database), documents=documents), as_json)


@app.command(
    epilog=(
        "Examples:\n\n  audit init\n\n  audit init --path ../other-repo\n\n"
        "Writes audit.toml with every setting at its default and a comment on each. The CLI finds it in the "
        "repository root or the current folder. Exit 2 when the folder does not exist, or the file exists and "
        "--force is not given."
    )
)
def init(
    path: Annotated[
        plb.Path, typer.Option(help="The folder to write audit.toml in. Default: the current folder.")
    ] = plb.Path("."),
    force: Annotated[bool, typer.Option("--force", help="Overwrite an existing audit.toml.")] = False,
) -> None:
    """Write a starting audit.toml."""
    if not path.is_dir():
        raise _refuse("init", f"{path} is not a folder")
    target = path / DEFAULT_CONFIG_NAME
    if target.exists() and not force:
        raise _refuse("init", f"{target} exists; pass --force to overwrite it")
    target.write_text(DEFAULT_TOML)
    typer.echo(f"wrote {target}")


attach(app, _load, _refuse, _scope)


def main() -> None:
    """Run the CLI."""
    app()
