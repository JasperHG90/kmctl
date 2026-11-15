"""kmaudit's command line: serve the MCP tools and the audit page, and read a store.

Agents drive the audit through the MCP tools ``kmaudit mcp`` serves, people
through the page ``kmaudit ui`` serves. The CLI keeps only those two, the
list commands and the session-start briefing; the verbs it used to carry
answer a typed name with the tool that replaced them.
"""

import json
import sqlite3
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
from typing import Annotated

import typer


def _print_version(value: bool) -> None:
    """Print ``kmaudit X.Y.Z`` and exit when ``--version`` is given."""
    if value:
        typer.echo(f"kmaudit {version('kmaudit')}")
        raise typer.Exit()


app = typer.Typer(
    help=(
        "Audit what a folder of markdown docs claims about its repository. Agents "
        "extract claims and write checks through the MCP tools (mcp serves them over "
        "stdio); people review them on a local page (ui), which also reruns stale "
        "checks. claims list and checks list read a store; namespaces lists the "
        "audited folders, each with its own store under .kmaudit/, which ignores "
        "itself in git; briefing prints each one's state for a session-start hook. "
        "kmaudit calls no model except the judge tool and the page's Second opinion. "
        "Needs a git repository."
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
        "Read a folder's stored claims. Verb: list. Agents extract claims with the "
        "claims_todo and claims_submit MCP tools (the /extract-claims skill)."
    ),
    no_args_is_help=True,
)
app.add_typer(claims_app, name="claims")

checks_app = typer.Typer(
    help=(
        "Read each claim's check status. Verb: list. Agents write checks with the "
        "checks_todo, checks_try and checks_submit MCP tools (the /write-checks "
        "skill); kmaudit ui's Rerun stale checks button or the checks_run tool "
        "reruns them."
    ),
    no_args_is_help=True,
)
app.add_typer(checks_app, name="checks")

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


def _refuse(verb: str, message: str) -> None:
    """Print one refusal line for ``kmaudit VERB`` on stderr and exit 1."""
    typer.echo(f"kmaudit {verb}: refused: {message}", err=True)
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
        "kind, as the last extraction left it; /extract-claims (the claims_todo "
        "and claims_submit MCP tools) brings the store in line with the pages."
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
            typer.echo("no claims stored; extract them with /extract-claims")
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


@checks_app.command(
    "list",
    epilog=(
        "Examples:\n\n"
        "  kmaudit checks list\n\n"
        "  kmaudit checks list .okf/manifesto.md --status fails\n\n"
        "  kmaudit checks list --json\n\n"
        "It reads the store as the last rerun or checks_submit left it; press "
        "Rerun stale checks in kmaudit ui, or call the checks_run MCP tool, "
        "first for the current state."
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
        "verdict the check disagrees with, sends the work back: the claims_todo "
        "MCP tool (/extract-claims) hands out the section again and checks_todo "
        "(/write-checks) the claim again, each with your note, and the agent's "
        "next submit marks it answered. A note alone waits for the next time the item is "
        "handed out. A verdict lasts while the files it was given on are "
        "unchanged, and outranks the check in what the page marks. Thumbs-up "
        "answers are shown to agents as examples. The Second opinion button "
        "asks the decision model the judge MCP tool uses (link for a check that "
        "holds, failure for one that fails, claim for a reason); it needs the "
        "question switched on in audit.toml. The Rerun stale checks button "
        "reruns the checks whose files changed, as the checks_run MCP tool "
        "does, and shows the result. The server answers only requests from this machine. Stop it with Ctrl-C."
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
    "mcp",
    epilog=(
        "Examples:\n\n"
        "  kmaudit mcp\n\n"
        "A harness that speaks MCP starts this command and talks to it over "
        "stdin and stdout; you do not run it by hand. Its tools are how an "
        "agent drives the audit: namespaces, claims_todo, claims_submit, "
        "claims_list, checks_todo, checks_try, checks_submit, checks_run, "
        "checks_list, coverage and judge. Each takes folder, absolute or "
        "relative to the directory the harness starts it in, and returns JSON; "
        "the todo tools hand out 5 items unless given limit. A refused call "
        "comes back as a tool error naming the fix. See the "
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
        typer.echo("no namespaces yet; audit a folder with /extract-claims FOLDER")
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
        "and cuts the pages to count pending sections, where the claims_todo tool would "
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


#: The verbs the CLI no longer carries, as (group or None, verb, what replaced it).
#: Typed anyway, each exits 2 with one line naming its replacement.
_DROPPED: list[tuple[str | None, str, str]] = [
    (
        "claims",
        "todo",
        "call the claims_todo MCP tool (kmaudit mcp), or run /extract-claims",
    ),
    (
        "claims",
        "submit",
        "call the claims_submit MCP tool (kmaudit mcp), or run /extract-claims",
    ),
    (
        "checks",
        "todo",
        "call the checks_todo MCP tool (kmaudit mcp), or run /write-checks",
    ),
    (
        "checks",
        "try",
        "call the checks_try MCP tool (kmaudit mcp), or run /write-checks",
    ),
    (
        "checks",
        "submit",
        "call the checks_submit MCP tool (kmaudit mcp), or run /write-checks",
    ),
    (
        "checks",
        "run",
        "call the checks_run MCP tool (kmaudit mcp), or press Rerun stale checks in kmaudit ui",
    ),
    (
        None,
        "judge",
        "call the judge MCP tool (kmaudit mcp), or press Second opinion in kmaudit ui",
    ),
    (None, "coverage", "call the coverage MCP tool (kmaudit mcp), or open kmaudit ui"),
    (
        None,
        "guard",
        "the hook is gone with it: kmaudit's agents call the MCP tools (kmaudit mcp) and have no shell to guard",
    ),
]


def _gone(group: str | None, verb: str, instead: str) -> None:
    """Register a hidden ``kmaudit [GROUP] VERB`` that prints what replaced it and exits 2.

    It takes any arguments and options, ``--help`` included, so whatever was
    typed after the verb gets the same one line.
    """
    owner = {"claims": claims_app, "checks": checks_app, None: app}[group]
    words = f"{group} {verb}" if group else verb

    @owner.command(
        verb,
        hidden=True,
        add_help_option=False,
        context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
    )
    def _dropped() -> None:
        typer.echo(f"kmaudit {words}: no longer a command; {instead}", err=True)
        raise typer.Exit(2)


for _dropped_verb in _DROPPED:
    _gone(*_dropped_verb)


def main() -> None:
    """Run the kmaudit CLI."""
    app()
