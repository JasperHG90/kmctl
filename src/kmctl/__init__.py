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
from kmctl.kinds import KINDS, schema
from kmctl.plugin import (
    APM_CLI,
    DEFAULT_SOURCE,
    HARNESSES,
    PluginError,
    PluginStatus,
    Scope,
    parse_harnesses,
)
from kmctl.plugin import install as install_plugin
from kmctl.plugin import status as plugin_status
from kmctl.review_due import review_due
from kmctl.scaffold import AGENT_FILES, scaffold
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


_INIT_EPILOG = (
    "Examples:\n\n"
    "  kmctl init\n\n"
    "  kmctl init --path ../other-repo --json\n\n"
    "It writes docs/README.md; .okf/index.md, log.md and manifesto.md; a kmctl "
    "block (where knowledge lives and the agent's duties) in each CLAUDE.md and "
    "AGENTS.md; a new CLAUDE.md when there is none, holding only @AGENTS.md "
    "when AGENTS.md exists (Claude Code then reads AGENTS.md and its block "
    "once) and the block otherwise; and the first decision, Keep project "
    "knowledge in an OKF bundle, when no record has that title. It writes no "
    "rules: the knowledge rules come with kmctl's skills from kmctl plugin "
    "install.\n\n"
    "A CLAUDE.md with an @AGENTS.md line, beside an AGENTS.md, gets no block. "
    "A CLAUDE.md or AGENTS.md symlink that is dangling or points outside the "
    "repository is left alone with a warning naming it and its target; when "
    "AGENTS.md is such a link and there is no CLAUDE.md, init writes no "
    "CLAUDE.md. A symlink inside the repository is written through.\n\n"
    "Run it again at any time, or as kmctl update after upgrading kmctl: a "
    "file that already exists is kept, with two exceptions. The kmctl block "
    "between <!-- kmctl:start --> and <!-- kmctl:end --> is added or replaced, "
    "and no other text in the file changes. Writing the first decision into a "
    "kept bundle adds its index entry and log line."
)


@app.command(epilog=_INIT_EPILOG)
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
            help="Print one JSON object with created, skipped, updated and warnings lists, for scripts.",
        ),
    ] = False,
) -> None:
    """Create docs/, a starter .okf/ bundle and a CLAUDE.md block; re-run to refresh the block."""
    result = scaffold(path)
    if as_json:
        typer.echo(json.dumps(asdict(result)))
        return
    for rel in result.created:
        typer.echo(f"created {rel}")
    for rel in result.updated:
        why = (
            "kmctl block" if Path(rel).name in AGENT_FILES else "first decision's entry"
        )
        typer.echo(f"updated {rel} ({why})")
    for rel in result.skipped:
        typer.echo(f"kept    {rel} (already there)")
    for warning in result.warnings:
        typer.echo(f"warning: {warning}", err=True)
    if result.created or result.updated:
        typer.echo(
            next_step(
                "kmctl plugin install --harness claude for the skills and the "
                "knowledge rules",
                "fill the purpose and invariants in .okf/manifesto.md (its values "
                "are the operator's to write)",
                "add a diagram page to .okf/architecture/ once there is code",
                "record each choice as you make it with kmctl new decision",
            )
        )
    else:
        typer.echo("Nothing to do: every file already exists.")


app.command(
    "update",
    epilog=_INIT_EPILOG,
    help="Same as kmctl init. Run it after upgrading kmctl to refresh the CLAUDE.md block.",
)(init)


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
    """Add ``kmctl new KIND`` for one .okf/ section; handoffs also take ``--key``, other kinds ``--source``."""

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
        stale_after: Annotated[
            str | None,
            typer.Option(
                "--stale-after",
                metavar="30d|2027-01-15",
                help=(
                    "When kmctl review due lists the concept as due: a duration from "
                    "now (30d days, 12w weeks, 6m calendar months, 1y calendar years) "
                    "or a date (2027-01-15 is its midnight UTC, or 2027-01-15T08:00:00Z). "
                    "It must be in the future. Default: 14d for a handoff, none for "
                    "the rest."
                ),
            ),
        ] = None,
        sources: Annotated[
            list[str] | None,
            typer.Option(
                "--source",
                metavar="src/app.py",
                help=(
                    "Not for handoffs: a file or folder the concept describes; repeat "
                    "for more. It must exist: a path from the repository root, from "
                    "the concept's folder, or from .okf/ with a leading /. kmctl review "
                    "due lists the concept once a commit changes it after the last "
                    "verify."
                ),
            ),
        ] = None,
    ) -> None:
        try:
            result = new_concept(
                path,
                kind,
                title,
                description,
                key=key,
                stale_after=stale_after,
                sources=sources,
            )
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
            f"  kmctl new {kind} '{example}' --description 'One sentence.' "
            f"{'--stale-after 3d' if kind == 'handoff' else '--source src/app.py --stale-after 6m'}\n\n"
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
            "--json",
            help="Print one JSON object (routing, state, rules, skills), for scripts.",
        ),
    ] = False,
) -> None:
    """Print the session briefing: where knowledge lives, what is due, and the rules."""
    result = build_briefing(path)
    typer.echo(json.dumps(as_dict(result)) if as_json else render(result))


@app.command(
    "schema",
    epilog=(
        "Examples:\n\n"
        "  kmctl schema\n\n"
        "  kmctl schema decision\n\n"
        "  kmctl schema architecture\n\n"
        "The schema is JSON Schema (draft 2020-12) for the kind's front matter, "
        "built from kmctl's own table of kinds when you run it, so it is what "
        "kmctl writes: the fields by their OKF names, which are required, the "
        "legal values and what each one means. x-kmctl-sections gives the body: "
        'a list of the ## sections in order, {"pattern": REGEX} when every '
        'heading has one form, {"last": NAME} for free sections ending with '
        "NAME, or null for no fixed sections. A kind with no front matter allows "
        "no properties. Read it before you write a concept or a page by hand; "
        "nothing checks a file against it yet."
    ),
)
def schema_cmd(
    kind: Annotated[
        str | None,
        typer.Argument(
            metavar="decision",
            help=(
                "The kind whose schema to print, one of the names kmctl schema "
                f"lists with no name: {', '.join(KINDS)}. Leave it out for the list."
            ),
        ),
    ] = None,
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help=(
                "With no kind, print the list as one JSON object of kind to where "
                "it lives and what it is for, for scripts. A kind's schema is JSON "
                "either way."
            ),
        ),
    ] = False,
) -> None:
    """Print the JSON Schema of one document kind, or list the kinds there are."""
    if kind is None:
        purposes = {name: f"{k.where}, {k.purpose}" for name, k in KINDS.items()}
        if as_json:
            typer.echo(json.dumps(purposes))
            return
        width = max(map(len, purposes))
        for name, purpose in purposes.items():
            typer.echo(f"{name:<{width}}  {purpose}")
        return
    if kind not in KINDS:
        typer.echo(
            f"kmctl schema: refused: no kind {kind!r}; give one of "
            f"{', '.join(KINDS)}, as kmctl schema lists them",
            err=True,
        )
        raise typer.Exit(1)
    typer.echo(json.dumps(schema(kind), indent=2))


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
        "Install kmctl's skills, audit agent, knowledge rules and session hook for an "
        "agent harness, through APM (Agent Package Manager). Verbs: install, update, "
        "status. Needs uv on PATH: kmctl runs APM with uvx."
    ),
    no_args_is_help=True,
)
app.add_typer(plugin_app, name="plugin")

_SCOPE_OPTION = typer.Option(
    "--scope",
    metavar="project",
    help=(
        "project (this repository: apm.yml, .claude/ and .mcp.json here; the default) "
        "or user (every repository: ~/.apm/apm.yml, and Claude Code's folder, "
        "$CLAUDE_CONFIG_DIR or ~/.claude)."
    ),
)
_HARNESS_OPTION = typer.Option(
    "--harness",
    metavar="claude",
    help=(
        "The agent harnesses to install for, as a comma list. Accepted: "
        f"{', '.join(HARNESSES)}. Default: claude."
    ),
)
_SOURCE_OPTION = typer.Option(
    "--source",
    metavar="https://host/owner/repo.git",
    show_default=False,
    help=(
        "The git URL of the repository holding the kmctl package (its apm/ folder, "
        "at the tag v<this kmctl's version>). Default: kmctl's GitHub repository, "
        "named below. Set it for a fork or a local git server; an http:// URL is "
        "allowed as insecure."
    ),
)
_FORCE_OPTION = typer.Option(
    "--force",
    help=(
        "Let APM replace skill folders it did not write. It replaces each folder "
        "whole, deleting any file you added there. Use it when the install says "
        "APM left files in place."
    ),
)
_PLUGIN_JSON_OPTION = typer.Option(
    "--json",
    help="Print the resulting status and notes as one JSON object, for scripts.",
)
_INSTALL_EPILOG = (
    "Examples:\n\n"
    "  kmctl plugin {verb} --harness claude\n\n"
    "  kmctl plugin {verb} --harness claude --scope user --json\n\n"
    "  kmctl plugin {verb} --source http://127.0.0.1:8080/o/kmctl.git\n\n"
    f"The default --source is {DEFAULT_SOURCE}\n\n"
    "In order: runs apm uninstall on an apm.yml entry that names "
    "JasperHG90/Knowledge-management/apm another way; writes the kmctl entry "
    "{{git: SOURCE, path: apm, ref: vVERSION}} and the harnesses as targets "
    "into apm.yml, keeping its other entries; runs "
    f"uvx --from {APM_CLI} apm install --target HARNESSES; once that worked, "
    "removes the old claude plugin kmctl@kmctl from this repository (skipped "
    "when the claude CLI is not on PATH); writes one "
    "SessionStart hook that runs kmctl briefing into .claude/settings.json; and "
    "declares okf's MCP server okf-bundle in .mcp.json (at user scope, with "
    "claude mcp add-json), unless an okf server is already there. Running it "
    "again changes nothing. It refuses, and names the fix, when APM leaves in "
    "place a skill folder it did not write."
)


def _report(
    result: PluginStatus, as_json: bool, notes: list[str] | None = None
) -> None:
    """Print a status: one JSON object, or a summary line and one line per problem."""
    if as_json:
        data = asdict(result)
        if notes is not None:
            data["notes"] = notes
        typer.echo(json.dumps(data))
        return
    for note in notes or []:
        typer.echo(f"note: {note}")
    typer.echo(
        f"kmctl {result.cli_version}; package {result.package_ref or 'not installed'} "
        f"({result.scope} scope); hook {'present' if result.hook else 'missing'}"
    )
    for problem in result.problems:
        typer.echo(f"problem: {problem}")


def _install(
    verb: str, harness: str, scope: Scope, source: str, force: bool, as_json: bool
) -> None:
    """Run ``kmctl plugin install`` or ``update``: map a PluginError to a refusal."""
    try:
        result = install_plugin(
            Path.cwd(), parse_harnesses(harness), scope, source=source, force=force
        )
    except PluginError as error:
        typer.echo(f"kmctl plugin {verb}: refused: {error}", err=True)
        raise typer.Exit(1) from error
    _report(result.status, as_json, result.notes)
    if not as_json:
        scope_flag = " --scope user" if scope == "user" else ""
        typer.echo(
            next_step(
                "start a new Claude Code session", f"kmctl plugin status{scope_flag}"
            )
        )


@plugin_app.command("install", epilog=_INSTALL_EPILOG.format(verb="install"))
def plugin_install(
    harness: Annotated[str, _HARNESS_OPTION] = "claude",
    scope: Annotated[Scope, _SCOPE_OPTION] = "project",
    source: Annotated[str, _SOURCE_OPTION] = DEFAULT_SOURCE,
    force: Annotated[bool, _FORCE_OPTION] = False,
    as_json: Annotated[bool, _PLUGIN_JSON_OPTION] = False,
) -> None:
    """Install kmctl's APM package, its session hook and okf's MCP server for a harness."""
    _install("install", harness, scope, source, force, as_json)


@plugin_app.command("update", epilog=_INSTALL_EPILOG.format(verb="update"))
def plugin_update(
    harness: Annotated[str, _HARNESS_OPTION] = "claude",
    scope: Annotated[Scope, _SCOPE_OPTION] = "project",
    source: Annotated[str, _SOURCE_OPTION] = DEFAULT_SOURCE,
    force: Annotated[bool, _FORCE_OPTION] = False,
    as_json: Annotated[bool, _PLUGIN_JSON_OPTION] = False,
) -> None:
    """Reinstall kmctl's APM package at this kmctl's version; run it after upgrading kmctl."""
    _install("update", harness, scope, source, force, as_json)


@plugin_app.command(
    "status",
    epilog=(
        "Examples:\n\n"
        "  kmctl plugin status\n\n"
        "  kmctl plugin status --scope user --json\n\n"
        "It reads apm.lock.yaml and settings.json and changes nothing. Exits 0 "
        "either way; each problem names the command that fixes it."
    ),
)
def plugin_status_cmd(
    scope: Annotated[Scope, _SCOPE_OPTION] = "project",
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help=(
                "Print one JSON object (cli_version, scope, package_ref, hook, "
                "problems), for scripts."
            ),
        ),
    ] = False,
) -> None:
    """Report the installed kmctl package's version and the session hook, and what to fix."""
    _report(plugin_status(Path.cwd(), scope), as_json)


def main() -> None:
    """Run the kmctl CLI."""
    app()
