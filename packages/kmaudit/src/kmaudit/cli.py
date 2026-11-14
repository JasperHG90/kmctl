"""kmaudit's command line: audit what a folder of markdown docs claims about its repository."""

import json
import sqlite3
import sys
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
from typing import Annotated

import typer


def next_step(*steps: str) -> str:
    """The one ``Next:`` line a verb that writes files ends with; the last step is a kmaudit verb."""
    return "Next: " + ", then ".join(steps)


def _print_version(value: bool) -> None:
    """Print ``kmaudit X.Y.Z`` and exit when ``--version`` is given."""
    if value:
        typer.echo(f"kmaudit {version('kmaudit')}")
        raise typer.Exit()


app = typer.Typer(
    help=(
        "Audit what a folder of markdown docs claims about its repository. Groups: claims "
        "(extract them), checks (test them; needs claims from kmaudit claims). "
        "Verbs: judge (an optional decision model's opinion; off by default), "
        "ui (a local page to review claims and checks and give feedback), "
        "coverage (how much of the code the checks match), "
        "mcp (serve these verbs as MCP tools over stdio). "
        "kmaudit calls no model except judge: a coding agent reads what these "
        "verbs hand out and submits its answers. Each audited folder is a namespace "
        "with its own store under .kmaudit/, which ignores itself in git; namespaces "
        "lists them. Needs a git repository."
    ),
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.callback()
def _root(
    show_version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=_print_version,
        is_eager=True,
        help="Print the kmaudit version and exit, as kmaudit X.Y.Z.",
    ),
) -> None:
    """kmaudit: audit what a folder of markdown docs claims about its repository."""


claims_app = typer.Typer(
    help=(
        "Extract a folder's claims through an agent. Verbs: todo (sections to "
        "read), submit (store the agent's verdicts), list (read claims back)."
    ),
    no_args_is_help=True,
)
app.add_typer(claims_app, name="claims")

#: What a path means, shared by every verb's help.
_PATH_MEANING = (
    "The folder of markdown docs to audit (its namespace), or a folder or page "
    "inside one to narrow the scope. A path inside an audited folder means that "
    "folder; the repository root holding .okf/ means .okf. Default: the current "
    "directory."
)
_AUDIT_PATH_ARGUMENT = typer.Argument(
    metavar="[docs|.okf|docs/guide.md]", help=_PATH_MEANING
)
_STORE_PATH_OPTION = typer.Option(
    "--path",
    metavar="docs",
    exists=True,
    help=(
        "The namespace whose store to use, as todo printed it in namespace and "
        "next. " + _PATH_MEANING
    ),
)


def _refuse(verb: str, message: str) -> None:
    """Print one refusal line for ``kmaudit VERB`` on stderr and exit 1."""
    typer.echo(f"kmaudit {verb}: refused: {message}", err=True)
    raise typer.Exit(1)


@claims_app.command(
    "todo",
    epilog=(
        "Examples:\n\n"
        "  kmaudit claims todo\n\n"
        "  kmaudit claims todo .okf/manifesto.md --json\n\n"
        "  kmaudit claims todo --limit 5 --json\n\n"
        "  kmaudit claims todo .okf --limit 5 --brief --json\n\n"
        "It cuts each live concept into header sections with numbered "
        "sentences, refreshes the store's sections, drops the claims of "
        "sections whose text changed or that are gone, and lists the sections "
        "with no extraction for their current key. A section's key covers its "
        "text, its concept's id, title, status and type, the earlier sections "
        "and the extraction instructions, so changing any of them hands it out "
        "again, and editing one section also hands out the sections after it. Deprecated concepts, index.md, log.md and prototypes/ are "
        "skipped. With --json it prints the instructions once, the counts and "
        "each section (id, key, concept, title, section, sentences, earlier, "
        "corrections): answer each per the instructions and pipe the answers "
        "to kmaudit claims submit -. It writes only .kmaudit/."
    ),
)
def claims_todo(
    path: Annotated[Path, _AUDIT_PATH_ARGUMENT] = Path("."),
    limit: Annotated[
        int | None,
        typer.Option(
            "--limit",
            metavar="5",
            min=1,
            help="Hand out at most this many sections; the counts still cover all. Default: every one.",
        ),
    ] = None,
    brief: Annotated[
        bool,
        typer.Option(
            "--brief",
            help="Leave the instructions out of --json, for the rounds after the first.",
        ),
    ] = False,
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Print one JSON object (instructions, counts, concepts, sections, next), for an agent.",
        ),
    ] = False,
) -> None:
    """List the bundle's sections that have no claims extracted for their current text."""
    from kmaudit import AuditError
    from kmaudit.verbs import todo

    try:
        result = todo(path, limit, brief)
    except (AuditError, sqlite3.Error) as error:
        _refuse("claims todo", str(error))
        return
    if as_json:
        typer.echo(result.model_dump_json(exclude_none=brief))
        return
    c = result.counts
    typer.echo(
        f"{c.up_to_date} up to date, {c.pending} to extract "
        f"({c.new} new, {c.changed} changed), {c.removed} removed"
    )
    for pc in result.concepts:
        typer.echo(f"pending {pc.path}  ({pc.sections} sections)")
    if c.pending:
        typer.echo(
            next_step(
                "kmaudit claims todo --json, then answer each section",
                "kmaudit claims submit -",
            )
        )


@claims_app.command(
    "submit",
    epilog=(
        "Examples:\n\n"
        "  kmaudit claims submit answers.json\n\n"
        "  cat answers.json | kmaudit claims submit - --json\n\n"
        "  kmaudit claims submit - --by kmctl-claims-extractor\n\n"
        "The input is one section answer or a JSON list of them: section and key "
        "as kmaudit claims todo gave them, and sentences, one verdict per "
        "numbered sentence (n, how_to_check, reason, kind, claims). It refuses a "
        "section whose key is stale (run todo again), an answer that leaves a "
        "sentence without a verdict (naming the numbers), a kind other than none "
        "with no claim, and a malformed answer, each as one stderr line with the "
        "fix; the good sections in the same input are still stored. Exit 1 when "
        "any section is refused. It writes only .kmaudit/."
    ),
)
def claims_submit(
    file: Annotated[
        str,
        typer.Argument(
            metavar="[answers.json|-]",
            help="The file holding the answers, or - to read them from stdin. Default: -.",
        ),
    ] = "-",
    path: Annotated[
        Path,
        _STORE_PATH_OPTION,
    ] = Path("."),
    by: Annotated[
        str,
        typer.Option(
            "--by",
            metavar="kmctl-claims-extractor",
            help="Who wrote the answers, recorded with each section. Default: agent.",
        ),
    ] = "agent",
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Print one JSON object (stored: section, claims; refused: section, reason), for scripts.",
        ),
    ] = False,
) -> None:
    """Store an agent's verdicts and claims for sections that todo handed out."""
    from kmaudit import AuditError
    from kmaudit.verbs import submit

    try:
        text = (
            sys.stdin.read() if file == "-" else Path(file).read_text(encoding="utf-8")
        )
    except OSError as error:
        _refuse(
            "claims submit",
            f"cannot read {file} ({error.strerror}); give a file or - for stdin",
        )
        return
    try:
        result = submit(path, text, by)
    except (AuditError, sqlite3.Error) as error:
        _refuse("claims submit", str(error))
        return
    for refused in result.refused:
        typer.echo(f"kmaudit claims submit: refused: {refused.reason}", err=True)
    if as_json:
        typer.echo(result.model_dump_json())
    else:
        for stored in result.stored:
            typer.echo(f"stored {stored.section} ({stored.claims} claims)")
        if result.stored:
            typer.echo(
                next_step(
                    "kmaudit claims todo for what is left",
                    "kmaudit claims list",
                )
            )
    if result.refused:
        raise typer.Exit(1)


@claims_app.command(
    "list",
    epilog=(
        "Examples:\n\n"
        "  kmaudit claims list\n\n"
        "  kmaudit claims list .okf/manifesto.md --claims\n\n"
        "  kmaudit claims list --kind point --claims --json\n\n"
        "It reads only the store (creating it when absent). By default it shows each concept's sections, "
        "how many are extracted at their current text, and its claims per "
        "kind; run kmaudit claims todo first to bring the store in line "
        "with the bundle."
    ),
)
def claims_list(
    path: Annotated[Path, _AUDIT_PATH_ARGUMENT] = Path("."),
    kind: Annotated[
        str | None,
        typer.Option(
            "--kind",
            metavar="point",
            help="Only claims of this kind: point, structural, broad, subjective or external.",
        ),
    ] = None,
    each: Annotated[
        bool,
        typer.Option(
            "--claims",
            help="List each claim with its sentence, kind, quantifier, how to check and reason.",
        ),
    ] = False,
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help=(
                "Print one JSON object: documents (concept, sections, extracted, claims per kind) "
                "and totals, or claims with --claims, for scripts."
            ),
        ),
    ] = False,
) -> None:
    """Show the stored claims: counts per concept and kind, or each claim."""
    from kmaudit import AuditError
    from kmaudit.models import KINDS
    from kmaudit.verbs import list_claims

    if kind is not None and kind not in KINDS:
        _refuse(
            "claims list",
            f"unknown kind {kind!r} from --kind; use one of {', '.join(KINDS)}",
        )
    try:
        result = list_claims(path, kind, each)
    except (AuditError, sqlite3.Error) as error:
        _refuse("claims list", str(error))
        return
    if as_json:
        typer.echo(result.model_dump_json(exclude_none=True))
        return
    if result.claims is not None:
        for c in result.claims:
            typer.echo(f"{c.id}  {c.kind}/{c.quantifier}  {c.section} [{c.n}]")
            typer.echo(f"    {c.claim}")
            if c.how_to_check:
                typer.echo(f"    check: {c.how_to_check}")
        if not result.claims:
            typer.echo("no claims stored; run kmaudit claims todo")
        return
    for d in result.documents or []:
        kinds = (
            ", ".join(f"{k} {n}" for k, n in sorted(d.claims.items())) or "no claims"
        )
        typer.echo(f"{d.concept}  {d.extracted}/{d.sections} sections  {kinds}")
    totals = result.totals or {}
    total = sum(totals.values())
    typer.echo(
        f"{total} claims"
        + (
            f" ({', '.join(f'{k} {n}' for k, n in sorted(totals.items()))})"
            if total
            else ""
        )
    )


checks_app = typer.Typer(
    help=(
        "Turn stored claims into checks kmaudit reruns with no model. Verbs: todo "
        "(claims to check, with the lines they are about), try (test a draft), "
        "submit (store checks and reasons), run (rerun what changed), list. "
        "Needs claims from kmaudit claims submit."
    ),
    no_args_is_help=True,
)
app.add_typer(checks_app, name="checks")

_ANSWERS_ARGUMENT = typer.Argument(
    metavar="[answers.json|-]",
    help="The file holding the answers (one JSON object or a list), or - to read them from stdin. Default: -.",
)


def _read_answers(verb: str, file: str) -> str:
    """The answers text from ``file`` or stdin; refuses an unreadable file."""
    try:
        return (
            sys.stdin.read() if file == "-" else Path(file).read_text(encoding="utf-8")
        )
    except OSError as error:
        _refuse(
            verb, f"cannot read {file} ({error.strerror}); give a file or - for stdin"
        )
        raise


@checks_app.command(
    "todo",
    epilog=(
        "Examples:\n\n"
        "  kmaudit checks todo\n\n"
        "  kmaudit checks todo .okf/manifesto.md --json\n\n"
        "  kmaudit checks todo --limit 5 --json\n\n"
        "  kmaudit checks todo .okf/manifesto.md --limit 5 --brief --json\n\n"
        "It lists the stored point, structural and broad claims with no check, "
        "and those whose reason is stale because a file its lines came from "
        "changed. A claim's id follows its text, so a changed claim loses its "
        "check and comes back here. With --json each claim carries its "
        "sentence, its anchors (each backticked span resolved to a path, "
        "command, flag or name) and the lines around them, or keyword windows "
        "from its concept's sources; the instructions and the answer_schema come "
        "once. Draft each answer, test it with kmaudit checks try -, then "
        "kmaudit checks submit -. It writes only .kmaudit/."
    ),
)
def checks_todo(
    path: Annotated[Path, _AUDIT_PATH_ARGUMENT] = Path("."),
    limit: Annotated[
        int | None,
        typer.Option(
            "--limit",
            metavar="5",
            min=1,
            help="Hand out at most this many claims; the counts still cover all. Default: every one.",
        ),
    ] = None,
    brief: Annotated[
        bool,
        typer.Option(
            "--brief",
            help="Leave the instructions and answer_schema out of --json, for the rounds after the first.",
        ),
    ] = False,
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Print one JSON object (instructions, answer_schema, counts, concepts, claims, next), for an agent.",
        ),
    ] = False,
) -> None:
    """List the stored claims that have no check or current reason, with the lines they are about."""
    from kmaudit import AuditError
    from kmaudit.check_verbs import todo

    try:
        result = todo(path, limit, brief)
    except (AuditError, sqlite3.Error) as error:
        _refuse("checks todo", str(error))
        return
    if as_json:
        typer.echo(result.model_dump_json(exclude_none=brief))
        return
    c = result.counts
    typer.echo(
        f"{c.claims} checkable claims: {c.checks} checks, {c.reasons} reasons, {c.pending} to check"
        + (f" ({c.pruned} answers dropped with their claims)" if c.pruned else "")
        + (f" ({c.carried} answers moved to reworded claims)" if c.carried else "")
    )
    for pc in result.concepts:
        typer.echo(f"pending {pc.path}  ({pc.claims} claims)")
    if c.pending:
        typer.echo(
            next_step(
                "kmaudit checks todo --json",
                "kmaudit checks try -",
                "kmaudit checks submit -",
            )
        )


@checks_app.command(
    "try",
    epilog=(
        "Examples:\n\n"
        "  kmaudit checks try draft.json\n\n"
        "  cat draft.json | kmaudit checks try - --json\n\n"
        "It validates each draft against the answer schema, runs its steps and, "
        "when it holds, changes the lines it matched in memory (flip a boolean, "
        "change a number or string, negate a condition, delete a statement) to "
        "see whether it notices. weak means it noticed none, or matched only "
        "comments or docstrings; kmaudit checks submit refuses such a check. "
        "It writes nothing, not even the store. Exit 0 whatever the drafts do."
    ),
)
def checks_try(
    file: Annotated[str, _ANSWERS_ARGUMENT] = "-",
    path: Annotated[Path, _STORE_PATH_OPTION] = Path("."),
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Print a JSON list: per draft its claim, kind, holds, steps, weak, mutants, killed, missed, error.",
        ),
    ] = False,
) -> None:
    """Run draft checks and show whether each holds and which changes it would miss."""
    from pydantic import TypeAdapter

    from kmaudit import AuditError
    from kmaudit.check_verbs import Tried, try_answers

    text = _read_answers("checks try", file)
    try:
        tried = try_answers(path, text)
    except AuditError as error:
        _refuse("checks try", str(error))
        return
    if as_json:
        typer.echo(TypeAdapter(list[Tried]).dump_json(tried).decode())
        return
    for t in tried:
        if t.kind != "check":
            typer.echo(f"{t.claim}  {t.kind}" + (f": {t.error}" if t.error else ""))
            continue
        verdict = "holds" if t.holds else "fails"
        if t.holds:
            verdict += f", {'weak' if t.weak else 'not weak'} ({t.killed}/{t.mutants} changes noticed)"
        typer.echo(f"{t.claim}  {verdict}")
        for n, s in enumerate(t.steps, 1):
            typer.echo(
                f"    step {n}: {'holds' if s.holds else 'fails'}: {s.detail[:160]}"
            )
        for m in t.missed[:5]:
            typer.echo(f"    missed: {m}")


@checks_app.command(
    "submit",
    epilog=(
        "Examples:\n\n"
        "  kmaudit checks submit answers.json\n\n"
        "  cat answers.json | kmaudit checks submit - --json\n\n"
        "  kmaudit checks submit - --by kmctl-check-writer\n\n"
        "Each answer is a check (claim, steps, strength exact or proxy, why, and "
        "drift with one sentence when the check fails because the claim is "
        "wrong) or a reason no check fits (claim, reason). It runs each check "
        "and measures it as try does, then refuses a weak check (naming the "
        "changes it missed, or that it matched only comments or docstrings), a "
        "failing check without drift, a holding check with drift, an unknown "
        "or stale claim id, a code or query step whose library is missing, and a "
        "malformed answer, each as one stderr line with the fix. The rest are "
        "stored, reasons included. Exit 1 when any answer is refused. It "
        "writes only .kmaudit/."
    ),
)
def checks_submit(
    file: Annotated[str, _ANSWERS_ARGUMENT] = "-",
    path: Annotated[Path, _STORE_PATH_OPTION] = Path("."),
    by: Annotated[
        str,
        typer.Option(
            "--by",
            metavar="kmctl-check-writer",
            help="Who wrote the answers, recorded with each. Default: agent.",
        ),
    ] = "agent",
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Print one JSON object (stored: claim, kind, status, mutants, killed; refused: claim, reason).",
        ),
    ] = False,
) -> None:
    """Store checks and reasons for claims, refusing weak and failing checks."""
    from kmaudit import AuditError
    from kmaudit.check_verbs import submit

    text = _read_answers("checks submit", file)
    try:
        result = submit(path, text, by)
    except (AuditError, sqlite3.Error) as error:
        _refuse("checks submit", str(error))
        return
    for refused in result.refused:
        typer.echo(f"kmaudit checks submit: refused: {refused.reason}", err=True)
    if as_json:
        typer.echo(result.model_dump_json())
    else:
        for s in result.stored:
            score = f", {s.killed}/{s.mutants} changes noticed" if s.mutants else ""
            typer.echo(f"stored {s.claim} ({s.kind}, {s.status}{score})")
        if result.stored:
            typer.echo(
                next_step(
                    "kmaudit checks todo for what is left",
                    "kmaudit checks list",
                )
            )
    if result.refused:
        raise typer.Exit(1)


@checks_app.command(
    "run",
    epilog=(
        "Examples:\n\n"
        "  kmaudit checks run\n\n"
        "  kmaudit checks run --all --json\n\n"
        "It reruns each stored check whose files changed: the content of a file "
        "it reads, or the files its globs match. With --all it reruns every "
        "one. A holding check is measured again when its steps or reads moved. "
        "A check that failed only because the extra was missing reruns too. It "
        "calls no model. Statuses: holds, not measured (holds, but had no change "
        "to try), weak, fails, drift (fails and the check says the claim is "
        "wrong), skipped (needs ast-grep or jmespath), reason, stale reason (a file its "
        "lines came from changed; todo hands it out again), no check. Exit 0 whatever the checks find (audits report only, ADR "
        "0005), 1 only when it cannot run. It writes only .kmaudit/."
    ),
)
def checks_run(
    path: Annotated[Path, _AUDIT_PATH_ARGUMENT] = Path("."),
    everything: Annotated[
        bool,
        typer.Option(
            "--all",
            help="Rerun every stored check, not only those whose files changed.",
        ),
    ] = False,
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Print one JSON object (counts, rerun, measured, claims: claim, concept, status, rerun, measured, detail).",
        ),
    ] = False,
) -> None:
    """Rerun the stored checks whose files changed, with no model, and report each claim's status."""
    from kmaudit import AuditError
    from kmaudit.check_verbs import run

    try:
        result = run(path, everything)
    except (AuditError, sqlite3.Error) as error:
        _refuse("checks run", str(error))
        return
    if as_json:
        typer.echo(result.model_dump_json())
        return
    for r in result.claims:
        if r.status in ("fails", "drift", "weak", "skipped"):
            typer.echo(f"{r.status:8}  {r.claim}  {r.concept}  {r.detail}")
    counts = (
        ", ".join(f"{k} {v}" for k, v in sorted(result.counts.items()))
        or "no checkable claims"
    )
    typer.echo(f"{counts}; {result.rerun} rerun, {result.measured} measured")


@checks_app.command(
    "list",
    epilog=(
        "Examples:\n\n"
        "  kmaudit checks list\n\n"
        "  kmaudit checks list .okf/manifesto.md --status fails\n\n"
        "  kmaudit checks list --json\n\n"
        "It reads the store as the last kmaudit checks run or submit left "
        "it; run kmaudit checks run first for the current state."
    ),
)
def checks_list(
    path: Annotated[Path, _AUDIT_PATH_ARGUMENT] = Path("."),
    status: Annotated[
        str | None,
        typer.Option(
            "--status",
            metavar="fails",
            help="Only claims with this status: holds, not measured, weak, fails, drift, skipped, reason, "
            "stale reason, no check, not run.",
        ),
    ] = None,
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Print one JSON object (counts, claims: claim, concept, text, status, strength, why, drift, reason, quality).",
        ),
    ] = False,
) -> None:
    """Show each claim's check status, strength and why."""
    from typing import get_args

    from kmaudit import AuditError
    from kmaudit.check_verbs import Status, list_checks

    if status is not None and status not in get_args(Status):
        _refuse(
            "checks list",
            f"unknown status {status!r} from --status; use one of {', '.join(get_args(Status))}",
        )
    try:
        result = list_checks(path, status)
    except (AuditError, sqlite3.Error) as error:
        _refuse("checks list", str(error))
        return
    if as_json:
        typer.echo(result.model_dump_json(exclude_none=True))
        return
    for r in result.claims:
        extra = r.drift or r.reason or r.why or ""
        q = f" [{r.quality}]" if r.quality else ""
        typer.echo(f"{r.status:8}  {r.claim}  {r.text[:90]}{q}")
        if extra:
            typer.echo(f"          {extra[:120]}")
    typer.echo(
        ", ".join(f"{k} {v}" for k, v in sorted(result.counts.items()))
        or "no checkable claims"
    )


@app.command(
    "judge",
    epilog=(
        "Examples:\n\n"
        "  kmaudit judge failure 3acd0efc57ab --json\n\n"
        "  kmaudit judge link 3acd0efc57ab 5daa573f16f0\n\n"
        "  cat lines.txt | kmaudit judge claim 0369c52d377b --json\n\n"
        "The one model call kmaudit makes, and only when you switch a question on "
        "in the per-user settings file, $XDG_CONFIG_HOME/kmctl/audit.toml "
        "(~/.config/kmctl/audit.toml when unset), or the file --config or "
        "KMCTL_AUDIT_CONFIG names:\n\n"
        "  \\[decisions.providers.clef]\n"
        '  base_url = "https://gateway.example/v1/decisions"\n'
        '  api_key_env = "CLEF_API_KEY"\n\n'
        "  \\[decisions.failure]\n"
        "  enabled = true\n"
        '  provider = "clef"\n'
        '  model = "jev-latest"\n\n'
        "\\[decisions] also takes timeout (seconds, default 60) and max_calls "
        "(calls in flight, default 4). failure asks whether a failed check "
        "shows the claim is false (chance, cause: claim_false, check_wrong or "
        "unclear); claim asks whether the lines on stdin show a claim true "
        "(chance, verdict: true, false or not_shown); link asks whether a "
        "check tests its claim (score 0 to 1, level: unrelated, keyword, "
        "nearby or the claim). Each answer is kept in the namespace's store under "
        "a hash of the question, model and state, so asking again sends nothing "
        "until the check, its result or the model changes. The key is read only "
        "from the variable api_key_env names and is never printed. Set "
        "LANGSMITH_TRACING=true to trace each call to LangSmith (needs the "
        "kmaudit[tracing] extra). Exit 1 when a question is refused or fails."
    ),
)
def audit_judge(
    question: Annotated[
        str,
        typer.Argument(
            metavar="failure|claim|link",
            help="What to ask: failure and link take check ids, claim takes one claim id with the lines on stdin.",
        ),
    ],
    ids: Annotated[
        list[str],
        typer.Argument(
            metavar="ID...",
            help="Check ids from kmaudit checks list, or a claim id from kmaudit claims list --claims.",
        ),
    ],
    path: Annotated[Path, _STORE_PATH_OPTION] = Path("."),
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            metavar="audit.toml",
            help="The settings file to read instead of the per-user one or KMCTL_AUDIT_CONFIG, for CI.",
        ),
    ] = None,
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Print a JSON list: per id its question, id, model, cached, and chance and cause, chance and "
            "verdict, or score and level.",
        ),
    ] = False,
) -> None:
    """Ask the configured decision model one question about stored checks or a claim."""
    import asyncio

    from pydantic import TypeAdapter

    from kmaudit import AuditError
    from kmaudit.judge import Judgement, run_judge

    try:
        lines = sys.stdin.read() if question == "claim" else ""
        result = asyncio.run(run_judge(path, question, ids, lines, config))
    except (AuditError, sqlite3.Error) as error:
        _refuse("judge", str(error))
        return
    answered = [e.judgement for e in result.entries if e.judgement is not None]
    failed = [e for e in result.entries if e.judgement is None]
    for entry in failed:
        typer.echo(f"kmaudit judge: refused: {entry.id}: {entry.error}", err=True)
    if as_json:
        typer.echo(
            TypeAdapter(list[Judgement]).dump_json(answered, exclude_none=True).decode()
        )
    else:
        for j in answered:
            if j.question == "failure":
                what = f"claim false {j.chance} ({j.cause})"
            elif j.question == "claim":
                what = f"shown true {j.chance} ({j.verdict})"
            else:
                what = f"tests its claim {j.score} ({j.level})"
            typer.echo(
                f"{j.question} {j.id}: {what}" + ("  [cached]" if j.cached else "")
            )
    if failed:
        raise typer.Exit(1)


@app.command(
    "coverage",
    epilog=(
        "Examples:\n\n"
        "  kmaudit coverage\n\n"
        "  kmaudit coverage --files 10\n\n"
        "  kmaudit coverage --json\n\n"
        "A line is covered when the last run of a stored check matched it: a "
        "grep line, the whole node a code pattern matched, a definition or an "
        "import. A file a check only reads (file, query and help steps) is read, "
        "not covered. The code is every file a check may read, without tests, "
        "fixtures, evals, lock files and the folders harnesses install packages "
        "into; blank lines do not count. A check whose files changed since its "
        "last run is stale and its lines are not counted until kmaudit "
        "checks run reruns it. Run kmaudit checks run --all once when checks "
        "were stored before kmaudit recorded matched lines. kmaudit "
        "audit ui shows the same numbers line by line."
    ),
)
def audit_coverage(
    path: Annotated[
        Path,
        typer.Argument(
            metavar="[docs|.okf]",
            help="The namespace to measure. " + _PATH_MEANING,
        ),
    ] = Path("."),
    files: Annotated[
        int,
        typer.Option(
            "--files",
            metavar="10",
            min=0,
            help="How many of the largest files with no matched line to list. Default: 5.",
        ),
    ] = 5,
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Print one JSON object: lines, covered, files, files_read, stale, and by_file with "
            "each file's lines, covered, hits per line and read_by.",
        ),
    ] = False,
) -> None:
    """Show how much of the repository's code the claims' checks match, line by line."""
    from kmaudit import AuditError
    from kmaudit.coverage import coverage

    try:
        measured = coverage(path)
    except AuditError as error:
        _refuse("coverage", str(error))
        return
    if as_json:
        typer.echo(measured.model_dump_json())
        return
    typer.echo(
        f"{measured.covered:,} of {measured.lines:,} lines of code matched by a check "
        f"({measured.share:.1%}); {measured.files_read} of {measured.files} files read by one"
    )
    if measured.stale:
        typer.echo(
            f"{measured.stale} checks ran on files that changed since, so their lines are not "
            "counted; run kmaudit checks run to rerun them"
        )
    bare = sorted(
        (f for f in measured.by_file if not f.covered), key=lambda f: -f.lines
    )
    for f in bare[:files]:
        typer.echo(f"no line matched  {f.path}  ({f.lines} lines)")


@app.command(
    "ui",
    epilog=(
        "Examples:\n\n"
        "  kmaudit ui\n\n"
        "  kmaudit ui .okf --port 0 --no-open\n\n"
        "  kmaudit ui --by human:sam --config ci-audit.toml\n\n"
        "Serves a page on 127.0.0.1 that shows each document with its claims, "
        "their checks and how sure each check is, read from the namespace's store. "
        "On the page you give a claim or its check a thumbs up or down and a "
        "note, and say whether the claim holds or is false. A thumbs down, or a "
        "verdict the check disagrees with, sends the work back: kmaudit "
        "claims todo hands out the section again and kmaudit checks todo "
        "the claim again, each with your note, and the agent's next submit "
        "marks it answered. A note alone waits for the next time the item is "
        "handed out. A verdict lasts while the files it was given on are "
        "unchanged, and outranks the check in what the page marks. Thumbs-up "
        "answers are shown to agents as examples. The Second opinion button "
        "asks the decision model kmaudit judge uses (link for a check that "
        "holds, failure for one that fails, claim for a reason); it needs the "
        "question switched on in audit.toml. The "
        "server answers only requests from this machine. Stop it with Ctrl-C."
    ),
)
def audit_ui(
    path: Annotated[
        Path,
        typer.Argument(
            metavar="[docs|.okf]",
            help="The namespace to show. " + _PATH_MEANING,
        ),
    ] = Path("."),
    port: Annotated[
        int,
        typer.Option(
            "--port",
            metavar="8765",
            min=0,
            max=65535,
            help="The port on 127.0.0.1 to serve on; 0 picks any free one. Default: 8765.",
        ),
    ] = 8765,
    by: Annotated[
        str,
        typer.Option(
            "--by",
            metavar="human:sam",
            help="The name your feedback is stored under. Default: human.",
        ),
    ] = "human",
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            metavar="audit.toml",
            help="The decision model settings for Second opinion, instead of the per-user file or "
            "KMCTL_AUDIT_CONFIG.",
        ),
    ] = None,
    no_open: Annotated[
        bool,
        typer.Option("--no-open", help="Print the address without opening a browser."),
    ] = False,
) -> None:
    """Serve a local page to review claims and checks and give feedback on them."""
    from kmaudit import AuditError
    from kmaudit.ui import serve

    try:
        server = serve(path, port, by, config, open_browser=not no_open)
    except AuditError as error:
        _refuse("ui", str(error))
        return
    typer.echo(f"Serving the audit page at {server.url} (Ctrl-C stops it)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


@app.command(
    "guard",
    epilog=(
        "Examples:\n\n"
        "  kmaudit guard --allow claims\n\n"
        "  kmaudit guard --allow checks\n\n"
        "A Claude Code PreToolUse hook for the kmctl-claims-extractor and "
        "kmctl-check-writer agents, set in their front matter. It reads the "
        "hook's JSON on stdin and lets a Bash call through only when it is one "
        "kmaudit GROUP command, optionally after cd DIR &&, optionally fed "
        "by one quoted heredoc (<<'ANSWERS') whose body is data. A pipe, "
        "redirect, second command or substitution is refused: exit 2, which "
        "blocks the call, with the reason on stderr. Other tools pass. "
        "Antigravity and OpenCode have no per-agent hook, so there the "
        "agents' instructions hold the same rule (ADR 0040)."
    ),
)
def audit_guard(
    allow: Annotated[
        str,
        typer.Option(
            "--allow",
            metavar="claims",
            help="The kmaudit group the agent may run: claims or checks.",
        ),
    ],
) -> None:
    """Allow a Bash call only when it is one kmaudit command, as a PreToolUse hook."""
    from kmaudit.guard import GROUPS, refusal

    if allow not in GROUPS:
        typer.echo(
            f"kmaudit guard: refused: unknown group {allow!r} from --allow; use claims or checks",
            err=True,
        )
        raise typer.Exit(2)
    reason = refusal(sys.stdin.read(), allow)
    if reason is not None:
        typer.echo(f"kmaudit guard: blocked: {reason}", err=True)
        raise typer.Exit(2)


@app.command(
    "mcp",
    epilog=(
        "Examples:\n\n"
        "  kmaudit mcp\n\n"
        "A harness that speaks MCP starts this command and talks to it over "
        "stdin and stdout; you do not run it by hand. Its tools mirror the "
        "verbs: namespaces, claims_todo, claims_submit, claims_list, "
        "checks_todo, checks_try, checks_submit, checks_run, checks_list, "
        "coverage and judge. Each takes folder, absolute or relative to the "
        "directory the harness starts it in, and returns the JSON the verb's "
        "--json prints; the todo tools hand out 5 items unless given limit. A "
        "refused call comes back as a tool error naming the fix. See the "
        "README for each harness's setup."
    ),
)
def audit_mcp() -> None:
    """Serve kmaudit's verbs as MCP tools over stdio, for a harness that speaks MCP."""
    from kmaudit.mcp_server import server

    server.run("stdio")


@app.command(
    "namespaces",
    epilog=(
        "Examples:\n\n"
        "  kmaudit namespaces\n\n"
        "  kmaudit namespaces --json\n\n"
        "Each audited folder is a namespace, named by its path below the "
        "repository root, with its own store under .kmaudit/. A repository "
        "whose audit predates namespaces lists its old .kmctl/audit.sqlite as "
        ".okf until the first verb on .okf copies it. It writes nothing."
    ),
)
def list_namespaces(
    path: Annotated[
        Path,
        typer.Argument(
            metavar="[.]",
            help="A path in the repository whose namespaces to list. Default: the current directory.",
        ),
    ] = Path("."),
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Print one JSON object, {namespaces: [{namespace, folder, sections, claims, checks}]}, for scripts.",
        ),
    ] = False,
) -> None:
    """List the repository's namespaces: each audited folder with its counts."""
    from kmaudit.namespaces import listing

    rows = listing(path)
    if as_json:
        typer.echo(json.dumps({"namespaces": [asdict(r) for r in rows]}))
        return
    if not rows:
        typer.echo("no namespaces yet; audit a folder with kmaudit claims todo FOLDER")
        return
    for r in rows:
        typer.echo(
            f"{r.namespace}: {r.sections} sections, {r.claims} claims, {r.checks} checks ({r.folder})"
        )


@app.command(
    "briefing",
    epilog=(
        "Examples:\n\n"
        "  kmaudit briefing\n\n"
        "  kmaudit briefing --json\n\n"
        "For a session-start hook: per namespace, its sections and how many "
        "are pending, its claims, its checks by status and its open notes, then "
        "the one thing to do next. It changes no store: it opens each read-only "
        "and cuts the pages to count pending sections, where claims todo would "
        "refresh and drop changed sections' claims. With no namespace it prints "
        "nothing (with --json, an empty list); on any error it prints one line "
        "saying the briefing is unavailable (with --json, an unavailable key). "
        "It always exits 0, so a hook never blocks a session."
    ),
)
def audit_briefing(
    path: Annotated[
        Path,
        typer.Argument(
            metavar="[.]",
            help="A path in the repository to brief on. Default: the current directory.",
        ),
    ] = Path("."),
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help=(
                "Print one JSON object, {namespaces: [{namespace, sections, pending, "
                "claims, checks, feedback, next}]}, plus unavailable: REASON on an "
                "error, for scripts."
            ),
        ),
    ] = False,
) -> None:
    """Print each namespace's audit state and the next step, changing nothing."""
    from kmaudit.briefing import brief, render

    try:
        briefs = brief(path)
    except Exception as error:  # noqa: BLE001 - a session-start hook must never fail
        first = str(error).splitlines()[0] if str(error) else type(error).__name__
        if as_json:
            typer.echo(json.dumps({"namespaces": [], "unavailable": first}))
        else:
            typer.echo(f"kmaudit briefing: unavailable ({first})")
        return
    if as_json:
        typer.echo(json.dumps({"namespaces": [asdict(b) for b in briefs]}))
    elif briefs:
        typer.echo(render(briefs))


def main() -> None:
    """Run the kmaudit CLI."""
    app()
