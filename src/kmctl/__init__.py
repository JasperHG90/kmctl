"""kmctl: knowledge management for repositories that keep docs/ and an OKF bundle."""

import json
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
from typing import Annotated

import typer

from kmctl.briefing import as_dict, build_briefing, render
from kmctl.checks import run_checks
from kmctl.concepts import ConceptError, Kind, new_concept
from kmctl.docs import DocType, new_doc
from kmctl.handoffs import live_handoffs
from kmctl.plugin import PluginError, PluginStatus, Scope
from kmctl.plugin import install as install_plugin
from kmctl.plugin import status as plugin_status
from kmctl.review_due import review_due
from kmctl.scaffold import scaffold
from kmctl.supersede import supersede

app = typer.Typer(
    help="kmctl: keep a repository's docs/ and .okf/ knowledge current.",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)


def next_step(*steps: str) -> str:
    """The one ``Next:`` line a verb that writes files ends with; the last step is a kmctl verb."""
    return "Next: " + ", then ".join(steps)


def _print_version(value: bool) -> None:
    if value:
        typer.echo(f"kmctl {version('kmctl')}")
        raise typer.Exit()


@app.callback()
def _root(
    show_version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=_print_version,
        is_eager=True,
        help="Print the kmctl version and exit.",
    ),
) -> None:
    """kmctl: keep a repository's docs/ and .okf/ knowledge current."""


@app.command(
    epilog=(
        "Examples:\n\n"
        "  kmctl init\n\n"
        "  kmctl init --path ../other-repo --json\n\n"
        "Run it again at any time: a file that already exists is never changed."
    ),
)
def init(
    path: Annotated[
        Path,
        typer.Option(
            "--path",
            metavar="../other-repo",
            exists=True,
            file_okay=False,
            help="The repository to set up: an existing folder. Default: the current directory.",
        ),
    ] = Path("."),
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Print one JSON object with created, skipped and warnings lists, for scripts.",
        ),
    ] = False,
) -> None:
    """Create docs/README.md and a starter .okf/ bundle, keeping any file that exists."""
    result = scaffold(path)
    if as_json:
        typer.echo(json.dumps(asdict(result)))
        return
    for rel in result.created:
        typer.echo(f"created {rel}")
    for rel in result.skipped:
        typer.echo(f"kept    {rel} (already there)")
    for warning in result.warnings:
        typer.echo(f"warning: {warning}", err=True)
    if result.created:
        typer.echo(next_step("write .okf/manifesto.md", "kmctl check"))
    else:
        typer.echo("Nothing to do: every file already exists.")


@app.command(
    epilog=(
        "Examples:\n\n"
        "  kmctl check\n\n"
        "  kmctl check --path ../other-repo --json\n\n"
        "Exit 0 when nothing fails, 1 when a check fails. A missing docs/ or .okf/ "
        "is reported as skipped, not failed."
    ),
)
def check(
    path: Annotated[
        Path,
        typer.Option(
            "--path",
            metavar="../other-repo",
            exists=True,
            file_okay=False,
            help="The repository to check: an existing folder. Default: the current directory.",
        ),
    ] = Path("."),
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Print a JSON list of findings (check, file, line, message, level), for scripts.",
        ),
    ] = False,
) -> None:
    """Check indexes agree with their folders, prototypes have a README.md, and links resolve."""
    findings = run_checks(path)
    errors = [f for f in findings if f.level == "error"]
    if as_json:
        typer.echo(json.dumps([asdict(f) for f in findings]))
    else:
        for f in findings:
            where = f.file if f.line is None else f"{f.file}:{f.line}"
            typer.echo(f"{f.level}  {f.check}  {where}  {f.message}")
        typer.echo(f"{len(errors)} failed" if errors else "all checks passed")
    if errors:
        raise typer.Exit(1)


@app.command(
    epilog=(
        "Examples:\n\n"
        "  kmctl handoffs\n\n"
        "  kmctl handoffs --json\n\n"
        "Handoffs past their stale_after are left out; kmctl review due lists them."
    ),
)
def handoffs(
    path: Annotated[
        Path,
        typer.Option(
            "--path",
            metavar="../other-repo",
            exists=True,
            file_okay=False,
            help="The repository to read: an existing folder. Default: the current directory.",
        ),
    ] = Path("."),
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Print a JSON list of handoffs (id, path, title, description, date), for /continue.",
        ),
    ] = False,
) -> None:
    """List the live handoffs in .okf/handoffs/, newest first."""
    warnings: list[str] = []
    found = live_handoffs(path, warnings=warnings)
    for warning in warnings:
        typer.echo(f"warning: {warning}", err=True)
    if as_json:
        typer.echo(json.dumps([asdict(h) for h in found]))
        return
    if not found:
        typer.echo("no live handoffs in .okf/handoffs/")
        return
    for h in found:
        typer.echo(f"{h.date}  {h.title}  ({h.path})")
        if h.description:
            typer.echo(f"    {h.description}")


review_app = typer.Typer(
    help="Find knowledge that is due for review. Verbs: due.",
    no_args_is_help=True,
)
app.add_typer(review_app, name="review")


@review_app.command(
    "due",
    epilog=(
        "Examples:\n\n"
        "  kmctl review due\n\n"
        "  kmctl review due --path ../other-repo --json\n\n"
        "Always exits 0: being due is a report, not a failure. A source that "
        "resolves to no tracked file or folder is listed as a notice, not a reason."
    ),
)
def due(
    path: Annotated[
        Path,
        typer.Option(
            "--path",
            metavar="../other-repo",
            exists=True,
            file_okay=False,
            help="The repository to read: an existing folder. Default: the current directory.",
        ),
    ] = Path("."),
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Print one JSON object (due, notices, expired_handoffs, history_skipped), for scripts.",
        ),
    ] = False,
) -> None:
    """List concepts in .okf/ due for review, with the reason for each."""
    result = review_due(path)
    if as_json:
        typer.echo(json.dumps(asdict(result)))
        return
    if result.history_skipped:
        typer.echo(f"note: {result.history_skipped}")
    for d in result.due:
        typer.echo(f"due     {d.id}  ({'; '.join(d.reasons)})")
    for h in result.expired_handoffs:
        typer.echo(f"expired {h.id}  {h.title}")
    for n in result.notices:
        typer.echo(
            f"notice  {n.id}  {n.message}: {n.resource}"
            if n.resource
            else f"notice  {n.id}  {n.message}"
        )
    if not (result.due or result.expired_handoffs):
        typer.echo("nothing is due for review")


new_app = typer.Typer(
    help=(
        "Create a .okf/ concept or a docs/ page with its structure. Verbs: decision, "
        "practice, proposal, prototype, handoff, doc. Needs a repository set up by kmctl init."
    ),
    no_args_is_help=True,
)
app.add_typer(new_app, name="new")

_PATH_OPTION = typer.Option(
    "--path",
    metavar="../other-repo",
    exists=True,
    file_okay=False,
    help="The repository to write in: an existing folder. Default: the current directory.",
)


def _register_concept_verb(kind: Kind, example: str) -> None:
    """Add ``kmctl new KIND`` for one .okf/ section; handoffs also take ``--key``."""

    def command(
        title: Annotated[
            str,
            typer.Argument(
                metavar=f"'{example}'",
                help="The title; its kebab-case form names the file.",
            ),
        ],
        description: Annotated[
            str,
            typer.Option(
                "--description",
                metavar="'One sentence.'",
                help="One sentence for the front matter and the index entry.",
            ),
        ],
        path: Annotated[Path, _PATH_OPTION] = Path("."),
        as_json: Annotated[
            bool,
            typer.Option(
                "--json",
                help="Print one JSON object (id, path, created_section), for scripts.",
            ),
        ] = False,
        key: Annotated[
            str | None,
            typer.Option(
                "--key",
                metavar="$CLAUDE_CODE_SESSION_ID",
                help=(
                    "Handoffs only: a session key. A handoff with the same key is updated "
                    "in place instead of refused (ADR 0009)."
                ),
            ),
        ] = None,
    ) -> None:
        try:
            result = new_concept(path, kind, title, description, key=key)
        except ConceptError as error:
            typer.echo(f"kmctl new {kind}: refused: {error}", err=True)
            raise typer.Exit(1) from error
        if as_json:
            typer.echo(json.dumps(asdict(result)))
            return
        typer.echo(f"{'updated' if result.updated else 'created'} {result.path}")
        typer.echo(next_step(f"write the sections of {result.path}", "kmctl check"))

    command.__doc__ = f"Create a {kind} in .okf/ with its front matter, skeleton, index entry and log line."
    new_app.command(
        kind,
        epilog=(
            "Examples:\n\n"
            f"  kmctl new {kind} '{example}' --description 'One sentence.'\n\n"
            f"  kmctl new {kind} '{example}' --description 'One sentence.' --json\n\n"
            "Writes the structure; you write the prose. The first one creates its section."
        ),
    )(command)


_CONCEPT_VERBS: tuple[tuple[Kind, str], ...] = (
    ("decision", "Use a queue"),
    ("practice", "Measure first"),
    ("proposal", "Split the parser"),
    ("prototype", "Parser speed"),
    ("handoff", "Parser work"),
)
for _kind, _example in _CONCEPT_VERBS:
    _register_concept_verb(_kind, _example)


@new_app.command(
    "doc",
    epilog=(
        "Examples:\n\n"
        "  kmctl new doc how-to 'Install it'\n\n"
        "  kmctl new doc reference 'Config keys' --description 'Every key and its default.'\n\n"
        "Writes the page skeleton and its docs/README.md entry; you write the prose."
    ),
)
def new_doc_page(
    doc_type: Annotated[
        DocType,
        typer.Argument(
            metavar="tutorial|how-to|reference|explanation",
            help="The Diataxis type: a lesson, one task, facts, or why.",
        ),
    ],
    title: Annotated[
        str,
        typer.Argument(
            metavar="'Install it'",
            help="The page title; its kebab-case form names the file.",
        ),
    ],
    description: Annotated[
        str,
        typer.Option(
            "--description",
            metavar="'One line.'",
            help="An optional line for the index entry.",
        ),
    ] = "",
    path: Annotated[Path, _PATH_OPTION] = Path("."),
    as_json: Annotated[
        bool,
        typer.Option(
            "--json", help="Print one JSON object (path, created_folder), for scripts."
        ),
    ] = False,
) -> None:
    """Create a docs/ page in its Diataxis folder with a skeleton and its index entry."""
    try:
        result = new_doc(path, doc_type, title, description)
    except ConceptError as error:
        typer.echo(f"kmctl new doc: refused: {error}", err=True)
        raise typer.Exit(1) from error
    if as_json:
        typer.echo(json.dumps(asdict(result)))
        return
    typer.echo(f"created {result.path}")
    typer.echo(next_step(f"write the sections of {result.path}", "kmctl check"))


@app.command(
    epilog=(
        "Examples:\n\n"
        "  kmctl briefing\n\n"
        "  kmctl briefing --path ../other-repo --json\n\n"
        "The plugin's SessionStart hook prints this. It reads and never writes."
    ),
)
def briefing(
    path: Annotated[
        Path,
        typer.Option(
            "--path",
            metavar="../other-repo",
            exists=True,
            file_okay=False,
            help="The repository to brief on: an existing folder. Default: the current directory.",
        ),
    ] = Path("."),
    as_json: Annotated[
        bool,
        typer.Option(
            "--json", help="Print one JSON object (routing, state, rules), for scripts."
        ),
    ] = False,
) -> None:
    """Print the session briefing: where knowledge lives, what is due, and the rules."""
    result = build_briefing(path)
    typer.echo(json.dumps(as_dict(result)) if as_json else render(result))


decision_app = typer.Typer(
    help=(
        "Change decision records in .okf/decisions/. Verbs: supersede. "
        "Needs a bundle from kmctl init and both records from kmctl new decision."
    ),
    no_args_is_help=True,
)
app.add_typer(decision_app, name="decision")


@decision_app.command(
    "supersede",
    epilog=(
        "Examples:\n\n"
        "  kmctl decision supersede 3 --by 7\n\n"
        "  kmctl decision supersede 0003 --by 0007 --json\n\n"
        "The old record keeps its body: it gets status deprecated and an appended "
        "Correction section. Write the new record first with kmctl new decision."
    ),
)
def decision_supersede(
    old: Annotated[
        str,
        typer.Argument(metavar="3", help="The number of the decision being replaced."),
    ],
    by: Annotated[
        str,
        typer.Option(
            "--by", metavar="7", help="The number of the decision that replaces it."
        ),
    ],
    path: Annotated[
        Path,
        typer.Option(
            "--path",
            metavar="../other-repo",
            exists=True,
            file_okay=False,
            help="The repository to write in: an existing folder. Default: the current directory.",
        ),
    ] = Path("."),
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Print one JSON object (old, new) with both concept ids, for scripts.",
        ),
    ] = False,
) -> None:
    """Mark one decision superseded by another and link the two records both ways."""
    try:
        result = supersede(path, old, by)
    except ConceptError as error:
        typer.echo(f"kmctl decision supersede: refused: {error}", err=True)
        raise typer.Exit(1) from error
    if as_json:
        typer.echo(json.dumps(asdict(result)))
        return
    typer.echo(f"superseded {result.old} with {result.new}")
    typer.echo(next_step("kmctl check"))


plugin_app = typer.Typer(
    help=(
        "Install the Claude Code plugin that ships with this kmctl. Verbs: install, update, "
        "status. Needs the claude CLI on PATH."
    ),
    no_args_is_help=True,
)
app.add_typer(plugin_app, name="plugin")

_SCOPE_OPTION = typer.Option(
    "--scope",
    metavar="project",
    help="project (this repository, the default) or user (every repository).",
)


def _report(result: PluginStatus, as_json: bool) -> None:
    if as_json:
        typer.echo(json.dumps(asdict(result)))
        return
    typer.echo(
        f"kmctl {result.cli_version}; plugin {result.plugin_version or 'not installed'}"
    )
    for problem in result.problems:
        typer.echo(f"problem: {problem}")


def _install(scope: Scope, as_json: bool, reinstall: bool) -> None:
    try:
        result = install_plugin(scope, Path.cwd(), reinstall=reinstall)
    except PluginError as error:
        verb = "update" if reinstall else "install"
        typer.echo(f"kmctl plugin {verb}: refused: {error}", err=True)
        raise typer.Exit(1) from error
    _report(result, as_json)
    if not as_json:
        typer.echo(
            next_step(
                "start a new Claude Code session or run /reload-plugins",
                "kmctl plugin status",
            )
        )


@plugin_app.command(
    "install",
    epilog=(
        "Examples:\n\n"
        "  kmctl plugin install\n\n"
        "  kmctl plugin install --scope user --json\n\n"
        "Adds the scaccogatto marketplace for the okf dependency when it is missing. "
        "Running it again at the same version changes nothing."
    ),
)
def plugin_install(
    scope: Annotated[Scope, _SCOPE_OPTION] = "project",
    as_json: Annotated[
        bool,
        typer.Option(
            "--json", help="Print the resulting status as one JSON object, for scripts."
        ),
    ] = False,
) -> None:
    """Install the kmctl plugin and its okf dependency through the claude CLI."""
    _install(scope, as_json, reinstall=False)


@plugin_app.command(
    "update",
    epilog=(
        "Examples:\n\n"
        "  kmctl plugin update\n\n"
        "  kmctl plugin update --scope user\n\n"
        "Run it after upgrading kmctl: it restages the plugin and reinstalls it."
    ),
)
def plugin_update(
    scope: Annotated[Scope, _SCOPE_OPTION] = "project",
    as_json: Annotated[
        bool,
        typer.Option(
            "--json", help="Print the resulting status as one JSON object, for scripts."
        ),
    ] = False,
) -> None:
    """Reinstall the plugin from this kmctl release, replacing an older one."""
    _install(scope, as_json, reinstall=True)


@plugin_app.command(
    "status",
    epilog=(
        "Examples:\n\n"
        "  kmctl plugin status\n\n"
        "  kmctl plugin status --json\n\n"
        "Exits 0 either way; each problem names the command that fixes it."
    ),
)
def plugin_status_cmd(
    as_json: Annotated[
        bool, typer.Option("--json", help="Print one JSON object, for scripts.")
    ] = False,
) -> None:
    """Report the installed plugin's version against this kmctl, and what to fix."""
    try:
        result = plugin_status(Path.cwd())
    except PluginError as error:
        typer.echo(f"kmctl plugin status: refused: {error}", err=True)
        raise typer.Exit(1) from error
    _report(result, as_json)


def main() -> None:
    """Run the kmctl CLI."""
    app()
