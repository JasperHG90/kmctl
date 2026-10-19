"""kmctl: knowledge management for repositories that keep docs/ and an OKF bundle."""

import json
import sys
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
from typing import Annotated, Literal

import typer

from kmctl.briefing import (
    as_antigravity,
    as_dict,
    build_briefing,
    hook_workspace,
    render,
)
from kmctl.checks import run_checks
from kmctl.concepts import ConceptError, Kind, new_concept
from kmctl.docs import DocType, new_doc
from kmctl.docs_index import fix_folder_indexes
from kmctl.doctor import as_json as doctor_json
from kmctl.doctor import render as render_doctor
from kmctl.doctor import run_doctor
from kmctl.handoffs import live_handoffs
from kmctl.kinds import KINDS, schema
from kmctl.pin import add_notices, briefing_notices, hand_off
from kmctl.plugin import APM_CLI, PatchResult, PluginError, Scope
from kmctl.plugin import patch as patch_plugin
from kmctl.plugin import unpatch as unpatch_plugin
from kmctl.review_due import review_due
from kmctl.scaffold import AGENT_FILES, scaffold
from kmctl.summary import SUMMARY_ID, BadPayload, as_claude, find_root, payload_cwd
from kmctl.summary import Nudge as NudgeResult
from kmctl.summary import ack as ack_summary
from kmctl.summary import nudge as nudge_summary
from kmctl.supersede import supersede
from kmctl.verify import verify as verify_concept

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
    "It writes docs/README.md; .okf/index.md, log.md, manifesto.md and "
    "summary.md (the bundle's first page, at most 500 words); a kmctl "
    "block (where knowledge lives and the agent's duties) in each CLAUDE.md and "
    "AGENTS.md; a new CLAUDE.md when there is none, holding only @AGENTS.md "
    "when AGENTS.md exists (Claude Code then reads AGENTS.md and its block "
    "once) and the block otherwise; and the first decision, Keep project "
    "knowledge in an OKF bundle, when no record has that title. It writes no "
    "rules: the knowledge rules come with kmctl's skills in its APM package, "
    "which apm install installs (then kmctl plugin patch).\n\n"
    "A CLAUDE.md with an @AGENTS.md line, beside an AGENTS.md, gets no block. "
    "A CLAUDE.md or AGENTS.md symlink that is dangling or points outside the "
    "repository is left alone with a warning naming it and its target; when "
    "AGENTS.md is such a link and there is no CLAUDE.md, init writes no "
    "CLAUDE.md. A symlink inside the repository is written through.\n\n"
    "Run it again at any time, or as kmctl update after upgrading kmctl: a "
    "file that already exists is kept, with these exceptions. The kmctl block "
    "between <!-- kmctl:start --> and <!-- kmctl:end --> is added or replaced, "
    "and no other text in the file changes. Writing the first decision into a "
    "kept bundle adds its index entry and log line, and writing a manifesto or "
    "summary into one adds its entry to the kept .okf/index.md and a line to "
    ".okf/log.md, so kmctl check passes after it."
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
            help=(
                "Print one JSON object with created, skipped, updated, warnings and "
                "linked (new pages it added to a kept .okf/index.md) lists, for scripts."
            ),
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
    first = any(
        r.startswith(".okf/decisions/") and r != ".okf/decisions/index.md"
        for r in result.created
    )
    for rel in result.updated:
        if Path(rel).name in AGENT_FILES:
            why = "kmctl block"
        elif rel.startswith("docs/"):
            why = "generated index"
        elif rel in (".okf/index.md", ".okf/log.md") and result.linked:
            names = " and ".join(Path(p).stem for p in result.linked)
            why = f"entry for the new {names}"
            if first:
                why += " and the first decision's"
        else:
            why = "first decision's entry"
        typer.echo(f"updated {rel} ({why})")
    logged = ", with a line in .okf/log.md" if ".okf/log.md" in result.updated else ""
    for rel in result.linked:
        typer.echo(f"linked   {rel} from .okf/index.md{logged}")
    for rel in result.skipped:
        typer.echo(f"kept    {rel} (already there)")
    for warning in result.warnings:
        typer.echo(f"warning: {warning}", err=True)
    if result.created or result.updated:
        typer.echo(
            next_step(
                "install kmctl's package with APM for the skills and the knowledge "
                "rules (the kmctl README's install section: an apm.yml entry, apm "
                "install, kmctl plugin patch)",
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
        "  kmctl check --fix\n\n"
        "  kmctl check --path ../other-repo --json\n\n"
        "Exit 0 when nothing fails, 1 when a check fails. A warning (such as "
        "docs/README.md not linking a docs/ folder) is printed but does not fail. "
        "A missing docs/ or .okf/ is reported as skipped, not failed. The "
        "kmctl-check pre-commit hook runs this command."
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
            help=(
                "Print a JSON list of findings (check, file, line, message, level: "
                "error, warning or skipped), for scripts."
            ),
        ),
    ] = False,
    fix: Annotated[
        bool,
        typer.Option(
            "--fix",
            help=(
                "First write each docs/ folder README.md index kmctl generates that is "
                "missing or out of date, then check. It changes no other file."
            ),
        ),
    ] = False,
) -> None:
    """Check indexes agree with their folders, docs front matter, prototype READMEs and links."""
    if fix:
        created, updated = fix_folder_indexes(path)
        for rel in created + updated:
            typer.echo(f"fixed {rel}", err=as_json)
    findings = run_checks(path)
    errors = [f for f in findings if f.level == "error"]
    warnings = [f for f in findings if f.level == "warning"]
    if as_json:
        typer.echo(json.dumps([asdict(f) for f in findings]))
    else:
        for f in findings:
            where = f.file if f.line is None else f"{f.file}:{f.line}"
            typer.echo(f"{f.level}  {f.check}  {where}  {f.message}")
        summary = f"{len(errors)} failed" if errors else "all checks passed"
        if warnings:
            summary += f", {len(warnings)} warning{'s' if len(warnings) > 1 else ''}"
        typer.echo(summary)
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
        "resolves to no tracked file or folder is listed as a notice, not a reason.\n\n"
        "An id leaves the list once a person has read it and confirms it: "
        "kmctl verify ID --by human:<id> records that. A verified entry does not "
        "clear stale_after passed, so add --stale-after for those. Fix a drifted "
        "concept's body before verifying it.\n\n"
        "The summary, .okf/summary.md, is never verified: it is listed only with "
        "concepts changed: ID, ..., and leaves the list once you update it or "
        "run kmctl summary ack."
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
    """List the concepts in .okf/ and the pages in docs/ that are due for review, with the reason for each."""
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
    if result.due:
        steps = []
        if any(d.id == SUMMARY_ID for d in result.due):
            steps.append(
                "update .okf/summary.md, or kmctl summary ack when it still holds"
            )
        if any(d.id != SUMMARY_ID for d in result.due):
            steps.append(
                "once a person has read one and confirms it, "
                "kmctl verify ID --by human:<their id> (add --stale-after 6m "
                "for stale_after passed)"
            )
        typer.echo(next_step(*steps))


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


@app.command(
    "verify",
    epilog=(
        "Examples:\n\n"
        "  kmctl verify decisions/0001-keep-project-knowledge-in-an-okf-bundle "
        "--by human:jasper\n\n"
        "  kmctl verify manifesto --by human:jasper --stale-after 6m --json\n\n"
        "  kmctl verify docs/how-to/install --by human:jasper\n\n"
        "It appends {by, at} to the file's verified list, with at the current "
        "UTC time, changes no other line, and logs a concept in .okf/log.md. The "
        "id then stays off kmctl review due until its stale_after passes or one "
        "of its sources is committed again. A verified entry does not clear "
        "stale_after passed: when it has passed, give --stale-after, or the verb "
        "refuses.\n\n"
        "Only a person verifies (ADR 0023). An agent runs this only when the "
        "person named in --by has read the content and asked for it, never on an "
        "audit verdict alone (ADR 0005). Handoffs are never verified."
    ),
)
def verify(
    concept: Annotated[
        str,
        typer.Argument(
            metavar="decisions/0001-x",
            help=(
                "The id to mark checked, as kmctl review due prints it: a concept "
                "under .okf/ without .md (decisions/0001-x, manifesto) or a docs "
                "page (docs/how-to/install)."
            ),
        ),
    ],
    by: Annotated[
        str,
        typer.Option(
            "--by",
            metavar="human:jasper",
            help=(
                "The person who read it and confirms it, as human:<id>: a name or "
                "email address. Written as the entry's by; anything not starting "
                "human: is refused."
            ),
        ),
    ],
    stale_after: Annotated[
        str | None,
        typer.Option(
            "--stale-after",
            metavar="6m",
            help=(
                "A new stale_after for the file: a duration from now (30d, 12w, "
                "6m, 1y), a date (2027-01-15) or a UTC timestamp. Required when "
                "its stale_after has passed; optional otherwise."
            ),
        ),
    ] = None,
    path: Annotated[Path, _PATH_OPTION] = Path("."),
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Print one JSON object (id, path, by, at, stale_after), for scripts.",
        ),
    ] = False,
) -> None:
    """Record that a person checked a concept or docs page, so kmctl review due drops it."""
    try:
        result = verify_concept(path, concept, by, stale_after)
    except ConceptError as error:
        typer.echo(f"kmctl verify: refused: {error}", err=True)
        raise typer.Exit(1) from error
    if as_json:
        typer.echo(json.dumps(asdict(result)))
        return
    typer.echo(f"verified {result.id} by {result.by} at {result.at} ({result.path})")
    if result.stale_after:
        typer.echo(f"stale_after is now {result.stale_after}")
    typer.echo(next_step("kmctl review due"))


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
                help="Print one JSON object (id, path, created_section, updated), for scripts.",
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
        "Writes the page with front matter (description, stale_after three months "
        "ahead, empty sources) and its skeleton, then its folder's README.md index "
        "and a docs/README.md link to the folder; you write the prose."
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
            help="An optional line for the page's description front matter and its index entry.",
        ),
    ] = "",
    path: Annotated[Path, _PATH_OPTION] = Path("."),
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Print one JSON object (path, created_folder, warnings), for scripts.",
        ),
    ] = False,
) -> None:
    """Create a docs/ page in its Diataxis folder with front matter, a skeleton and its index entry."""
    try:
        result = new_doc(path, doc_type, title, description)
    except ConceptError as error:
        typer.echo(f"kmctl new doc: refused: {error}", err=True)
        raise typer.Exit(1) from error
    if as_json:
        typer.echo(json.dumps(asdict(result)))
        return
    for warning in result.warnings:
        typer.echo(f"warning: {warning}", err=True)
    typer.echo(f"created {result.path}")
    typer.echo(next_step(f"write the sections of {result.path}", "kmctl check"))


@app.command(
    epilog=(
        "Examples:\n\n"
        "  kmctl briefing\n\n"
        "  kmctl briefing --path ../other-repo --json\n\n"
        '  echo \'{"workspacePaths": ["/repo"]}\' | kmctl briefing --format '
        "antigravity\n\n"
        "The SessionStart hook in kmctl's package prints this: Claude "
        "Code's runs kmctl briefing, Antigravity's runs kmctl briefing --format "
        "antigravity. With --format antigravity the repository is "
        "workspacePaths[0] of the JSON object on stdin, which Antigravity sends "
        "every hook; when stdin is a terminal, empty or not that JSON, it is "
        "--path. In a project whose apm.lock.yaml pins another kmctl, the kmctl "
        "on PATH runs the pinned one if uv has it cached, and otherwise says to "
        "run just install. It adds a line when a newer kmctl release is out than "
        "the pin, read from kmctl/latest-release in the user's cache folder, "
        "which a background git ls-remote refreshes once a day; "
        "KMCTL_NO_UPDATE_CHECK=1 turns that off. It writes nothing in the "
        "repository."
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
            help=(
                "Print one JSON object (routing, setup, state, rules, skills), "
                "for scripts."
            ),
        ),
    ] = False,
    output_format: Annotated[
        Literal["text", "antigravity"],
        typer.Option(
            "--format",
            metavar="text",
            help=(
                "text (the briefing as text; the default) or antigravity (one "
                'JSON object, {"injectSteps": [{"systemMessage": {"systemMessage": '
                "TEXT}}]}, for Antigravity's SessionStart hook, with the "
                "repository read from the hook's stdin). Not with --json."
            ),
        ),
    ] = "text",
) -> None:
    """Print the session briefing: where knowledge lives, the skills, what is due, and the rule for reading knowledge."""
    if output_format == "antigravity":
        if as_json:
            raise typer.BadParameter(
                "--json prints the briefing's parts and --format antigravity the "
                "hook's JSON; give one of them",
                param_hint="'--format'",
            )
        root = hook_workspace(sys.stdin) or path
        out = as_antigravity(render(build_briefing(root)))
        typer.echo(add_notices(out, "antigravity", briefing_notices(root)))
        return
    result = build_briefing(path)
    out = json.dumps(as_dict(result)) if as_json else render(result)
    typer.echo(add_notices(out, "json" if as_json else "text", briefing_notices(path)))


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


summary_app = typer.Typer(
    help=(
        "Keep .okf/summary.md, the bundle's first page, in step with its "
        "concepts. Verbs: ack, nudge."
    ),
    no_args_is_help=True,
)
app.add_typer(summary_app, name="summary")


@summary_app.command(
    "ack",
    epilog=(
        "Examples:\n\n"
        "  kmctl summary ack\n\n"
        "  kmctl summary ack --path ../other-repo --json\n\n"
        "kmctl review due lists the summary, with reason concepts changed: ID, "
        "..., when a concept (the manifesto, a decision, practice, proposal, "
        "prototype README or architecture page) changed in a commit after the "
        "summary's last commit, or is changed in the working tree while the "
        "summary is not. Editing the summary clears that. When you have read "
        "the changed concepts and the summary still holds, run this instead: it "
        "writes checked (at: the UTC time to the second, against: those ids) into the "
        "summary's front matter, changes no other line and no other file, and "
        "the summary leaves the list. Commit it with the concepts. It is an "
        "agent's word, not a person's review, which is kmctl verify (ADR 0023, "
        "ADR 0027). When the summary is current it writes nothing.\n\n"
        "Exit 1, with the reason on stderr, when there is no .okf/summary.md, "
        "its front matter is unreadable or lacks type: summary, or there is no "
        "git history (not a repository, or a shallow clone)."
    ),
)
def summary_ack(
    path: Annotated[Path, _PATH_OPTION] = Path("."),
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help=(
                "Print one JSON object (path, at, against), for scripts; at is "
                "null when nothing was written."
            ),
        ),
    ] = False,
) -> None:
    """Record that .okf/summary.md still holds after the concepts that changed since it."""
    try:
        result = ack_summary(path)
    except ConceptError as error:
        typer.echo(f"kmctl summary ack: refused: {error}", err=True)
        raise typer.Exit(1) from error
    if as_json:
        typer.echo(json.dumps(asdict(result)))
        return
    if result.at is None:
        typer.echo(f"nothing to ack: {result.path} is current")
        return
    typer.echo(
        f"checked {result.path} at {result.at} against {', '.join(result.against)}"
    )
    typer.echo(next_step("kmctl review due"))


@summary_app.command(
    "nudge",
    epilog=(
        "Examples:\n\n"
        '  echo \'{"cwd": "/repo", "tool_name": "Bash"}\' | kmctl summary nudge '
        "--format claude\n\n"
        '  echo \'{"workspacePaths": ["/repo"]}\' | kmctl summary nudge '
        "--format antigravity\n\n"
        "  kmctl summary nudge --format opencode --path /repo\n\n"
        "  kmctl summary nudge --path ../other-repo\n\n"
        "  kmctl summary nudge --path ../other-repo --json\n\n"
        "kmctl's package runs this right after a tool call, with "
        "KMCTL_PINNED=1 so the kmctl on PATH runs it rather than handing it to "
        "the project's pin through uvx (ADR 0026): Claude Code's PostToolUse "
        "hook after every Write, Edit, MultiEdit and Bash call (--format "
        "claude), Antigravity's PostToolUse hook after every tool call "
        "(--format antigravity), and OpenCode's plugin, .opencode/plugins/"
        "kmctl.js, after every tool call (--format opencode, ADR 0028).\n\n"
        "Where the repository comes from. Given --path, it is --path and "
        "stdin is never read, so a script or an agent's shell that leaves "
        "stdin open cannot make it wait. Without --path (as the hooks run "
        "it): --format claude and text read the cwd of the JSON object on "
        "stdin; --format antigravity reads workspacePaths[0] (agy runs the "
        "hook in .agents/, so the current directory is not used); --format "
        "opencode never reads stdin and uses the current directory. Empty "
        "or bad stdin prints nothing, and a claude payload with no cwd uses "
        "the current directory. From a subfolder "
        "it walks up to the folder holding .okf/summary.md or .git.\n\n"
        "It nudges when the summary is behind, by the rule kmctl summary ack "
        "describes (a concept changed after the summary; never log.md, an "
        "index, a handoff or the summary itself), and names the concepts and "
        "both ways out: update .okf/summary.md, or kmctl summary ack. It uses "
        "git only. It remembers the set it last named as a hash in "
        "kmctl/summary-nudge under the git directory (git rev-parse --git-path), "
        "so the same set stays quiet and a grown one nudges again. It never "
        "writes .okf/.\n\n"
        "It always exits 0, except exit 2 for --json with --format claude or "
        "antigravity. When there is nothing to say, or anything fails (no git, "
        "no .okf/summary.md, bad stdin without --path), --format claude and "
        "antigravity print {} and --format text and opencode print nothing."
    ),
)
def summary_nudge(
    path: Annotated[
        Path | None,
        typer.Option(
            "--path",
            metavar="../other-repo",
            exists=True,
            file_okay=False,
            help=(
                "The repository to check: an existing folder. Given, it wins "
                "and stdin is never read. Not given, the hook's JSON on stdin "
                "names it (cwd for claude and text, workspacePaths[0] for "
                "antigravity) and --format opencode uses the current "
                "directory; empty or bad stdin prints nothing (with --format "
                "claude or antigravity, {})."
            ),
        ),
    ] = None,
    output_format: Annotated[
        Literal["text", "claude", "antigravity", "opencode"],
        typer.Option(
            "--format",
            metavar="claude",
            help=(
                "text (the nudge as one line, or nothing; the default); claude "
                '(one JSON object, {"hookSpecificOutput": {"hookEventName": '
                '"PostToolUse", "additionalContext": TEXT}}, or {} for no nudge, '
                "for Claude Code's PostToolUse hook); antigravity (one JSON "
                'object, {"injectSteps": [{"systemMessage": {"systemMessage": '
                "TEXT}}]}, or {}, for Antigravity's PostToolUse hook, the "
                "repository read from workspacePaths[0] on stdin); or opencode "
                "(the nudge as text, or nothing, for kmctl's OpenCode plugin; it "
                "reads no stdin and takes the repository from --path)."
            ),
        ),
    ] = "text",
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help=(
                "Print one JSON object, {behind, concepts, nudge}, for scripts: "
                "whether the summary is behind, the changed concept ids, and the "
                "nudge text, null when it stays quiet. Not with --format claude "
                "or antigravity."
            ),
        ),
    ] = False,
) -> None:
    """Print a nudge to update .okf/summary.md when a concept changed after it."""
    if as_json and output_format in ("claude", "antigravity"):
        raise typer.BadParameter(
            f"--json prints the nudge's parts and --format {output_format} the "
            "hook's JSON; give one of them",
            param_hint="'--format'",
        )
    found = NudgeResult(concepts=[], nudge=None)
    try:
        # An explicit --path wins and stdin is never read, so a script or an
        # agent's shell that leaves stdin an open pipe cannot make it hang.
        # The hooks never pass --path; they send their JSON on stdin.
        if path is not None or output_format == "opencode":
            root = path or Path(".")
        elif output_format == "antigravity":
            workspace = hook_workspace(sys.stdin)
            if workspace is None:
                raise BadPayload("the hook input names no workspace folder")
            root = workspace
        else:
            root = Path(".")
            if not sys.stdin.isatty():
                root = payload_cwd(sys.stdin.read()) or root
        found = nudge_summary(find_root(root))
    except (OSError, ValueError):  # BadPayload is a ValueError
        pass  # a hook never fails: say nothing
    if as_json:
        typer.echo(json.dumps(asdict(found)))
    elif output_format == "claude":
        typer.echo(as_claude(found.nudge))
    elif output_format == "antigravity":
        typer.echo("{}" if found.nudge is None else as_antigravity(found.nudge))
    elif found.nudge is not None:
        typer.echo(found.nudge)


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
        "Finish installing kmctl's APM package for an agent harness. APM (Agent "
        "Package Manager) installs the package from apm.yml: the skills, audit "
        "agent, knowledge rules, session hooks and okf's MCP server. Verb: "
        "patch, which adds what APM cannot install yet. kmctl doctor checks the "
        "install."
    ),
    no_args_is_help=True,
)
app.add_typer(plugin_app, name="plugin")

_PATCH_EPILOG = (
    "Examples:\n\n"
    "  kmctl plugin patch\n\n"
    "  kmctl plugin patch --scope user\n\n"
    "  kmctl plugin patch --json\n\n"
    "  kmctl plugin patch --undo\n\n"
    "Run it after apm install (and after apm update). It reads apm.lock.yaml "
    "(~/.apm/apm.lock.yaml with --scope user) to see which harnesses APM "
    "installed kmctl's package for, and never runs APM, so it needs neither uv "
    "nor APM on PATH. For claude it removes the SessionStart hook and okf-bundle "
    "MCP server an older kmctl wrote itself (the package ships them now; when "
    "it removes okf-bundle, run apm install again so APM writes it) and the old "
    "claude plugin kmctl@kmctl. For antigravity (project scope only) it writes "
    ".agents/plugins/kmctl/ with plugin.json and the agents translated from "
    "Claude Code's format (kmctl-auditor and okf's two, read from "
    "apm_modules/), which APM does not install for Antigravity yet, and takes "
    "APM's okf Stop handler, which cannot run there, out of .agents/hooks.json. "
    "Antigravity loads .agents/ only once you trust the repository folder. "
    "For opencode (project scope only) it rewrites the three agents APM copies "
    "into .opencode/agents/ in Claude Code's format, which OpenCode skips, into "
    "OpenCode's (mode: subagent and a permission map), writes kmctl's four "
    "rules to .opencode/rules/, adds .opencode/rules/*.md to the instructions "
    "list of opencode.json (keeping every other key) so OpenCode loads them in "
    "every session, and writes .opencode/plugins/kmctl.js, which adds kmctl "
    "briefing to each session and kmctl summary nudge's text to a tool's "
    "result after each tool call. apm install puts APM's agents back, so run "
    "patch after every apm install. Running it again changes nothing.\n\n"
    "It refuses, naming the fix, when apm.lock.yaml lists no kmctl package "
    "(add the entry to apm.yml and run apm install), or when apm.yml still names "
    "the package the way kmctl v0.3.0 and older did (it names the apm uninstall "
    "to run first), or when opencode.json is not a JSON object. --undo deletes "
    ".agents/plugins/kmctl/ and, for OpenCode, the agents it rewrote, the "
    "rules, the instructions entry and the plugin, and nothing else; to remove "
    "kmctl, run kmctl plugin patch --undo first, then apm uninstall on its "
    "entry (apm uninstall stops on an agent patch rewrote). With --scope user, "
    "--undo leaves this repository's .agents/plugins/kmctl/ and OpenCode files, "
    "which are patched at project scope only, and names them. "
    "Installing is in the README's install section."
)


def _report(result: PatchResult, as_json: bool) -> None:
    """Print what a patch did: one JSON object, or its notes and a summary line."""
    if as_json:
        typer.echo(json.dumps(asdict(result)))
        return
    for note in result.notes:
        typer.echo(f"note: {note}")
    if result.harnesses:
        typer.echo(
            f"patched kmctl's package {result.package_ref or ''} for "
            f"{', '.join(result.harnesses)} ({result.scope} scope)".replace("  ", " ")
        )


@plugin_app.command("patch", epilog=_PATCH_EPILOG)
def plugin_patch(
    scope: Annotated[
        Scope,
        typer.Option(
            "--scope",
            metavar="project",
            help=(
                "project (this repository's apm.lock.yaml, .claude/, .mcp.json, "
                ".agents/, .opencode/ and opencode.json; the default) or user "
                "(~/.apm/apm.lock.yaml and Claude Code's folder, "
                "$CLAUDE_CONFIG_DIR or ~/.claude, for a package installed with "
                "apm install -g). Antigravity and OpenCode are patched at "
                "project scope only."
            ),
        ),
    ] = "project",
    undo: Annotated[
        bool,
        typer.Option(
            "--undo",
            help=(
                "Delete what patch wrote, and nothing else: .agents/plugins/kmctl/, "
                "and for OpenCode the agents it rewrote, .opencode/rules/, the "
                "instructions entry in opencode.json and .opencode/plugins/kmctl.js. "
                "Run it before apm uninstall, which removes the rest. At user "
                "scope it deletes nothing here; the epilog says why."
            ),
        ),
    ] = False,
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Print one JSON object (scope, harnesses, package_ref, notes), for scripts.",
        ),
    ] = False,
) -> None:
    """Add what APM cannot install yet for kmctl's package; run it after apm install."""
    try:
        result = (
            unpatch_plugin(Path.cwd(), scope)
            if undo
            else patch_plugin(Path.cwd(), scope)
        )
    except PluginError as error:
        typer.echo(f"kmctl plugin patch: refused: {error}", err=True)
        raise typer.Exit(1) from error
    _report(result, as_json)
    if undo and not as_json and not result.notes:
        typer.echo("nothing to undo: kmctl wrote nothing here")
    if not as_json:
        steps = []
        if "claude" in result.harnesses:
            steps.append("start a new Claude Code session")
        if "antigravity" in result.harnesses and scope == "project":
            steps.append(
                "open this folder in Antigravity, trust it and start a new session"
            )
        if "opencode" in result.harnesses and scope == "project":
            steps.append("start a new OpenCode session")
        flags = " --scope user" if scope == "user" else ""
        typer.echo(next_step(*steps, f"kmctl doctor{flags}"))


_DOCTOR_EPILOG = (
    "Examples:\n\n"
    "  kmctl doctor\n\n"
    "  kmctl doctor --path ../other-repo --json\n\n"
    "  kmctl doctor --scope user\n\n"
    "  kmctl doctor --online\n\n"
    "It prints one line per check on stdout: ok   ID: DETAIL, or fail ID: "
    "WHAT IS WRONG; THE FIX. Exit 0 when every check is ok, 1 when any "
    "fails, 2 for a usage error.\n\n"
    "The checks, by id: kmctl.version (this kmctl's version); dep.uv, "
    "dep.git (on PATH); dep.apm (APM "
    f"{APM_CLI.split('==')[1]} runs from uv's cache, with uv tool run "
    "--offline); dep.claude, dep.agy, dep.opencode (on PATH, for each harness "
    "installed); "
    "init.okf, init.docs (.okf/index.md and docs/README.md, from kmctl "
    "init; project scope only); kmctl.harness (which harnesses are "
    "installed, from apm.yml targets, apm.lock.yaml, the hook, "
    ".agents/plugins/kmctl/ and .opencode/plugins/kmctl.js); claude.scope (no "
    "Claude Code install here, but one at user scope). Then per harness, "
    "claude., antigravity. or opencode.: "
    "lock (apm.lock.yaml names kmctl's package at v<this version>); files "
    "(every kmctl file the lock lists for the harness exists with its "
    "sha256); okf-skills (the same for okf's skills); okf-mcp (okf's MCP "
    "server as kmctl's package declares it). claude.hook (the SessionStart "
    "hook in settings.json); claude.nudge-hook (the PostToolUse hook that "
    "runs kmctl summary nudge, in settings.json); claude.old-plugin (no settings file enables "
    "kmctl@kmctl or okf@scaccogatto). antigravity.plugin (every file in "
    ".agents/plugins/kmctl/ is what this kmctl writes); antigravity.hook "
    "(.agents/hooks.json holds kmctl's SessionStart hook and okf's Stop "
    "check); antigravity.nudge-hook (.agents/hooks.json holds the "
    "PostToolUse hook that runs kmctl summary nudge, read inside APM's "
    "matcher groups); antigravity.apm-hooks (.agents/hooks.json does not run APM's "
    "copy of okf's Stop check, which fails there); antigravity.trust (when "
    "agy is on PATH, the "
    "repository is in trustedWorkspaces of "
    "~/.gemini/antigravity-cli/settings.json); antigravity.okf-mcp-url "
    "(--online only). opencode.agents (the agents in .opencode/agents/ are in "
    "OpenCode's format, not APM's Claude-format copies; opencode.files and "
    "opencode.okf-skills skip them); opencode.rules (.opencode/rules/ holds "
    "kmctl's rules and opencode.json's instructions lists them); "
    "opencode.okf-mcp (opencode.json declares okf's MCP server); opencode.hook "
    "(.opencode/plugins/kmctl.js is the briefing plugin this kmctl writes); "
    "opencode.nudge-hook (that plugin has the execute.after hook that runs "
    "kmctl summary nudge).\n\n"
    "It writes nothing and uses no network unless --online. The only "
    f"command it runs is uv tool run --offline --from {APM_CLI} apm "
    "--version; it never runs claude, agy or opencode."
)


@app.command("doctor", epilog=_DOCTOR_EPILOG)
def doctor_cmd(
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
    scope: Annotated[
        Scope,
        typer.Option(
            "--scope",
            metavar="project",
            help=(
                "project (the install in this repository; the default) or user "
                "(the install apm install -g made: "
                "~/.apm/ and $CLAUDE_CONFIG_DIR, by default ~/.claude)."
            ),
        ),
    ] = "project",
    online: Annotated[
        bool,
        typer.Option(
            "--online",
            help=(
                "Also check that okf's MCP script URL, which Antigravity's MCP "
                "server runs with uv, can be fetched. The only check that uses "
                "the network."
            ),
        ),
    ] = False,
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help=(
                "Print one JSON object, {ok, checks: [{id, harness, ok, detail, "
                "fix}]}, for scripts; fix is null for a passed check."
            ),
        ),
    ] = False,
) -> None:
    """Check kmctl's tools, its installed package per harness and the kmctl init files."""
    result = run_doctor(path, scope, online)
    typer.echo(doctor_json(result) if as_json else render_doctor(result))
    if not result.ok:
        raise typer.Exit(1)


def main() -> None:
    """Run the kmctl CLI, or the project's pinned kmctl when its lock pins another release."""
    code = hand_off(sys.argv[1:])
    if code is not None:
        raise SystemExit(code)
    app()
