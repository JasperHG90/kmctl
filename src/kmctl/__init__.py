"""kmctl: knowledge management for repositories that keep docs/ and an OKF bundle."""

import json
import sqlite3
import sys
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
from typing import Annotated, Literal, cast

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
from kmctl.mv import mv as move_concept
from kmctl.pin import add_notices, briefing_notices, hand_off
from kmctl.plugin import APM_CLI, PatchResult, PluginError, Scope
from kmctl.plugin import patch as patch_plugin
from kmctl.plugin import unpatch as unpatch_plugin
from kmctl.review_due import review_due
from kmctl.scaffold import AGENT_FILES, scaffold
from kmctl.summary import SUMMARY_ID
from kmctl.summary import ack as ack_summary
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
        help=(
            "Print the kmctl version and exit, as kmctl X.Y.Z. In a project whose "
            "apm.lock.yaml pins another release, it prints the pinned version, "
            "followed by (pinned by apm.lock.yaml; kmctl X.Y.Z is on PATH). Set "
            "KMCTL_PINNED=1 for the bare line, as scripts need."
        ),
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
    "knowledge in an OKF bundle, when .okf/decisions/ holds no decision record "
    "(no .md file but index.md, in it or a folder inside it). It writes no "
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
        "  kmctl check --strict\n\n"
        "Exit 0 when nothing fails, 1 when a check fails. A warning (such as "
        "docs/README.md not linking a docs/ folder, or a summary over 500 words) "
        "is printed but does not fail, unless --strict is given. "
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
    strict: Annotated[
        bool,
        typer.Option(
            "--strict",
            help=(
                "Fail (exit 1) on warnings too, such as a summary over 500 words or "
                "behind its concepts. Default: off, so warnings print and pass."
            ),
        ),
    ] = False,
) -> None:
    """Check indexes agree with their folders, decision numbers, docs front matter, prototype READMEs and links."""
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
            if strict:
                summary += " (failing: --strict)"
        typer.echo(summary)
    if errors or (strict and warnings):
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
        "Commit order decides, not dates (ADR 0032): a source changed or edited "
        "after verification counts when a commit after the one that holds the "
        "newest verified entry changes the source, or the file outside verified "
        "and stale_after. A verified entry that is not committed yet counts "
        "nothing as changed. A docs page with no verified entry is compared "
        "with its own last commit.\n\n"
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
        "id then stays off kmctl review due until its stale_after passes, or a "
        "commit after the one holding the entry changes one of its sources or "
        "the file itself outside verified and stale_after. A verified entry does not clear "
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
    """Add ``kmctl new KIND`` for one .okf/ section; handoffs also take ``--key``, decisions ``--draft``, other kinds ``--source``."""

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
        draft: Annotated[
            bool,
            typer.Option(
                "--draft",
                help=(
                    "Decisions only: write status draft instead of stable, for a choice "
                    "written down but not yet accepted (ADR 0031). Once it is accepted, "
                    "set status to stable and add a log.md line that says so."
                ),
            ),
        ] = False,
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
                draft=draft,
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
            + (
                f"  kmctl new {kind} '{example}' --description 'One sentence.' --draft\n\n"
                if kind == "decision"
                else ""
            )
            + "Writes the structure; you write the prose. The first one creates its section."
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
        "concepts. Verbs: ack."
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
        "writes checked (at: the UTC time to the second, against: those ids, less "
        "any deleted since) into the "
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
        f"checked {result.path} at {result.at} against "
        f"{', '.join(result.against) or 'none'}"
    )
    typer.echo(next_step("kmctl review due"))


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


@app.command(
    "mv",
    epilog=(
        "Examples:\n\n"
        "  kmctl mv decisions/0008-use-a-queue decisions/0007-use-a-queue\n\n"
        "  kmctl mv practices/measure-first practices/measure-twice --json\n\n"
        "  kmctl mv prototypes/parser-speed prototypes/parser-timing\n\n"
        "It renames the file (a prototype's folder) in its folder, then rewrites "
        "every link to it in .okf/ and docs/, the section index entry among "
        "them, as kmctl check finds links: outside code, with the anchor kept. "
        "A decision whose number changes gets the new number in its title, its "
        "# heading and the ADR NNNN text of each link to it. The summary's "
        "checked.against names the new id. It appends a line to .okf/log.md "
        "and never rewrites an earlier one.\n\n"
        "It then lists, as not rewritten, each line anywhere in the repository "
        "but .okf/log.md that still holds the old id or file name, or for a "
        "renumbered decision its old ADR NNNN: a path in AGENTS.md, a skill or a script, "
        "or a mention in prose. Fix those by hand.\n\n"
        "It refuses when NEW exists or, for a decision, when another record "
        "holds its number. To renumber a run of decisions, move each one to the "
        "lowest free number, in order: with 0006 free, move 0007 to 0006, then "
        "0008 to 0007, fixing the listed lines after each move.\n\n"
        "Exit 1, with the reason on stderr, when kmctl refuses; nothing is "
        "written then."
    ),
)
def mv_concept(
    old: Annotated[
        str,
        typer.Argument(
            metavar="decisions/0008-x",
            help=(
                "The concept to rename, by its id as kmctl review due prints it: "
                "its path under .okf/ without .md (a prototype's folder)."
            ),
        ),
    ],
    new: Annotated[
        str,
        typer.Argument(
            metavar="decisions/0007-x",
            help=(
                "Its new id, in the same folder, in kebab-case. A decision's name "
                "starts with a four-digit number no other record holds."
            ),
        ),
    ],
    path: Annotated[Path, _PATH_OPTION] = Path("."),
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help=(
                "Print one JSON object (old, new, path, updated, mentions: "
                "[{file, line, text}]), for scripts."
            ),
        ),
    ] = False,
) -> None:
    """Rename a concept in .okf/ and rewrite the links to it in .okf/ and docs/."""
    try:
        result = move_concept(path, old, new)
    except ConceptError as error:
        typer.echo(f"kmctl mv: refused: {error}", err=True)
        raise typer.Exit(1) from error
    if as_json:
        typer.echo(json.dumps(asdict(result)))
        return
    typer.echo(f"moved {result.old} to {result.new} ({result.path})")
    for rel in result.updated:
        typer.echo(f"updated {rel}")
    for m in result.mentions:
        typer.echo(f"not rewritten  {m.file}:{m.line}  {m.text}")
    if result.mentions:
        typer.echo(
            next_step("fix or keep each line listed as not rewritten", "kmctl check")
        )
    else:
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
    "nor APM on PATH. For claude it removes the SessionStart hook an older "
    "kmctl wrote itself (the package ships it now) and the old claude plugin "
    "kmctl@kmctl; it leaves every MCP server alone. For antigravity (project scope only) it writes "
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
    "briefing to each session. apm install puts APM's agents back, so run "
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
    "It prints one line per check on stdout: ok   ID: DETAIL, warn ID: "
    "WHAT IS WRONG; THE FIX, or fail ID: WHAT IS WRONG; THE FIX. A warning is "
    "for what doctor cannot judge from here. Exit 0 when no check fails (a "
    "warning fails nothing), 1 when any fails, 2 for a usage error.\n\n"
    "The checks, by id: kmctl.version (this kmctl's version); dep.uv, "
    "dep.git (on PATH); dep.apm (APM "
    f"{APM_CLI.split('==')[1]} runs from uv's cache, with uv tool run "
    "--offline); dep.claude, dep.agy, dep.opencode (on PATH, for each harness "
    "installed; they warn, not fail, since only someone who uses that harness "
    "needs its CLI); "
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
    "hook in settings.json); claude.old-plugin (no settings file enables "
    "kmctl@kmctl or okf@scaccogatto; at project scope it also reads the user "
    "settings.json in $CLAUDE_CONFIG_DIR). antigravity.plugin (every file in "
    ".agents/plugins/kmctl/ is what this kmctl writes); antigravity.hook "
    "(.agents/hooks.json holds kmctl's SessionStart hook and okf's Stop "
    "check); antigravity.apm-hooks (.agents/hooks.json does not run APM's "
    "copy of okf's Stop check, which fails there); antigravity.trust (when "
    "agy is on PATH, the "
    "repository is in trustedWorkspaces of "
    "~/.gemini/antigravity-cli/settings.json; it warns, not fails, since "
    "doctor does not check trust given in the Antigravity IDE); "
    "antigravity.okf-mcp-url "
    "(--online only). opencode.agents (the agents in .opencode/agents/ are in "
    "OpenCode's format, not APM's Claude-format copies; opencode.files and "
    "opencode.okf-skills skip them); opencode.rules (.opencode/rules/ holds "
    "kmctl's rules and opencode.json's instructions lists them); "
    "opencode.okf-mcp (opencode.json declares okf's MCP server); opencode.hook "
    "(.opencode/plugins/kmctl.js is the briefing plugin this kmctl writes).\n\n"
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
                "Print one JSON object, {ok, checks: [{id, harness, status, ok, "
                "detail, fix}]}, for scripts; status is ok, warn or fail, ok is "
                "true unless status is fail, and fix is null for a passed check."
            ),
        ),
    ] = False,
) -> None:
    """Check kmctl's tools, its installed package per harness and the kmctl init files."""
    result = run_doctor(path, scope, online)
    typer.echo(doctor_json(result) if as_json else render_doctor(result))
    if not result.ok:
        raise typer.Exit(1)


audit_app = typer.Typer(
    help=(
        "Audit what the .okf/ bundle claims about the repository. Groups: claims "
        "(extract them), checks (test them; needs claims from kmctl audit claims). "
        "Verbs: judge (an optional decision model's opinion; off by default), "
        "ui (a local page to review claims and checks and give feedback), "
        "coverage (how much of the code the checks match). "
        "kmctl calls no model except judge: a coding agent reads what these "
        "verbs hand out and submits its answers. State lives in .kmctl/audit.sqlite, which "
        "ignores itself in git. Needs a repository with an .okf/ bundle (kmctl init)."
    ),
    no_args_is_help=True,
)
app.add_typer(audit_app, name="audit")

claims_app = typer.Typer(
    help=(
        "Extract a bundle's claims through an agent. Verbs: todo (sections to "
        "read), submit (store the agent's verdicts), list (read claims back)."
    ),
    no_args_is_help=True,
)
audit_app.add_typer(claims_app, name="claims")

_AUDIT_PATH_ARGUMENT = typer.Argument(
    metavar="[.|.okf|.okf/manifesto.md]",
    help=(
        "What to work on: a repository holding .okf/, a bundle folder, or one "
        "concept file to narrow the scope. Default: the current directory."
    ),
)


def _refuse(verb: str, message: str) -> None:
    """Print one refusal line for ``kmctl audit VERB`` on stderr and exit 1."""
    typer.echo(f"kmctl audit {verb}: refused: {message}", err=True)
    raise typer.Exit(1)


@claims_app.command(
    "todo",
    epilog=(
        "Examples:\n\n"
        "  kmctl audit claims todo\n\n"
        "  kmctl audit claims todo .okf/manifesto.md --json\n\n"
        "  kmctl audit claims todo --limit 5 --json\n\n"
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
        "to kmctl audit claims submit -. It writes only .kmctl/."
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
    as_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Print one JSON object (instructions, counts, concepts, sections, next), for an agent.",
        ),
    ] = False,
) -> None:
    """List the bundle's sections that have no claims extracted for their current text."""
    from kmctl.claims import AuditError
    from kmctl.claims.verbs import todo

    try:
        result = todo(path, limit)
    except (AuditError, sqlite3.Error) as error:
        _refuse("claims todo", str(error))
        return
    if as_json:
        typer.echo(result.model_dump_json())
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
                "kmctl audit claims todo --json, then answer each section",
                "kmctl audit claims submit -",
            )
        )


@claims_app.command(
    "submit",
    epilog=(
        "Examples:\n\n"
        "  kmctl audit claims submit answers.json\n\n"
        "  cat answers.json | kmctl audit claims submit - --json\n\n"
        "  kmctl audit claims submit - --by kmctl-claims-extractor\n\n"
        "The input is one section answer or a JSON list of them: section and key "
        "as kmctl audit claims todo gave them, and sentences, one verdict per "
        "numbered sentence (n, how_to_check, reason, kind, claims). It refuses a "
        "section whose key is stale (run todo again), an answer that leaves a "
        "sentence without a verdict (naming the numbers), a kind other than none "
        "with no claim, and a malformed answer, each as one stderr line with the "
        "fix; the good sections in the same input are still stored. Exit 1 when "
        "any section is refused. It writes only .kmctl/."
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
        typer.Option(
            "--path",
            metavar="../other-repo",
            exists=True,
            help="The repository whose store to write: it or a path in it. Default: the current directory.",
        ),
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
    from kmctl.claims import AuditError
    from kmctl.claims.verbs import submit

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
        typer.echo(f"kmctl audit claims submit: refused: {refused.reason}", err=True)
    if as_json:
        typer.echo(result.model_dump_json())
    else:
        for stored in result.stored:
            typer.echo(f"stored {stored.section} ({stored.claims} claims)")
        if result.stored:
            typer.echo(
                next_step(
                    "kmctl audit claims todo for what is left",
                    "kmctl audit claims list",
                )
            )
    if result.refused:
        raise typer.Exit(1)


@claims_app.command(
    "list",
    epilog=(
        "Examples:\n\n"
        "  kmctl audit claims list\n\n"
        "  kmctl audit claims list .okf/manifesto.md --claims\n\n"
        "  kmctl audit claims list --kind point --claims --json\n\n"
        "It reads only the store (creating it when absent). By default it shows each concept's sections, "
        "how many are extracted at their current text, and its claims per "
        "kind; run kmctl audit claims todo first to bring the store in line "
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
    from kmctl.claims import AuditError
    from kmctl.claims.models import KINDS
    from kmctl.claims.verbs import list_claims

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
            typer.echo("no claims stored; run kmctl audit claims todo")
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
        "Turn stored claims into checks kmctl reruns with no model. Verbs: todo "
        "(claims to check, with the lines they are about), try (test a draft), "
        "submit (store checks and reasons), run (rerun what changed), list. "
        "Needs claims from kmctl audit claims submit. Code and query steps need "
        "the kmctl\\[audit] extra."
    ),
    no_args_is_help=True,
)
audit_app.add_typer(checks_app, name="checks")

_ANSWERS_ARGUMENT = typer.Argument(
    metavar="[answers.json|-]",
    help="The file holding the answers (one JSON object or a list), or - to read them from stdin. Default: -.",
)
_STORE_PATH_OPTION = typer.Option(
    "--path",
    metavar="../other-repo",
    exists=True,
    help="The repository whose store to use: it or a path in it. Default: the current directory.",
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
        "  kmctl audit checks todo\n\n"
        "  kmctl audit checks todo .okf/manifesto.md --json\n\n"
        "  kmctl audit checks todo --limit 5 --json\n\n"
        "  kmctl audit checks todo .okf/manifesto.md --limit 5 --brief --json\n\n"
        "It lists the stored point, structural and broad claims with no check, "
        "and those whose reason is stale because a file its lines came from "
        "changed. A claim's id follows its text, so a changed claim loses its "
        "check and comes back here. With --json each claim carries its "
        "sentence, its anchors (each backticked span resolved to a path, "
        "command, flag or name) and the lines around them, or keyword windows "
        "from its concept's sources; the instructions and the answer_schema come "
        "once. Draft each answer, test it with kmctl audit checks try -, then "
        "kmctl audit checks submit -. It writes only .kmctl/."
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
    from kmctl.claims import AuditError
    from kmctl.claims.check_verbs import todo

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
                "kmctl audit checks todo --json",
                "kmctl audit checks try -",
                "kmctl audit checks submit -",
            )
        )


@checks_app.command(
    "try",
    epilog=(
        "Examples:\n\n"
        "  kmctl audit checks try draft.json\n\n"
        "  cat draft.json | kmctl audit checks try - --json\n\n"
        "It validates each draft against the answer schema, runs its steps and, "
        "when it holds, changes the lines it matched in memory (flip a boolean, "
        "change a number or string, negate a condition, delete a statement) to "
        "see whether it notices. weak means it noticed none, or matched only "
        "comments or docstrings; kmctl audit checks submit refuses such a check. "
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

    from kmctl.claims import AuditError
    from kmctl.claims.check_verbs import Tried, try_answers

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
        "  kmctl audit checks submit answers.json\n\n"
        "  cat answers.json | kmctl audit checks submit - --json\n\n"
        "  kmctl audit checks submit - --by kmctl-check-writer\n\n"
        "Each answer is a check (claim, steps, strength exact or proxy, why, and "
        "drift with one sentence when the check fails because the claim is "
        "wrong) or a reason no check fits (claim, reason). It runs each check "
        "and measures it as try does, then refuses a weak check (naming the "
        "changes it missed, or that it matched only comments or docstrings), a "
        "failing check without drift, a holding check with drift, an unknown "
        "or stale claim id, a code or query step without kmctl\\[audit], and a "
        "malformed answer, each as one stderr line with the fix. The rest are "
        "stored, reasons included. Exit 1 when any answer is refused. It "
        "writes only .kmctl/."
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
    from kmctl.claims import AuditError
    from kmctl.claims.check_verbs import submit

    text = _read_answers("checks submit", file)
    try:
        result = submit(path, text, by)
    except (AuditError, sqlite3.Error) as error:
        _refuse("checks submit", str(error))
        return
    for refused in result.refused:
        typer.echo(f"kmctl audit checks submit: refused: {refused.reason}", err=True)
    if as_json:
        typer.echo(result.model_dump_json())
    else:
        for s in result.stored:
            score = f", {s.killed}/{s.mutants} changes noticed" if s.mutants else ""
            typer.echo(f"stored {s.claim} ({s.kind}, {s.status}{score})")
        if result.stored:
            typer.echo(
                next_step(
                    "kmctl audit checks todo for what is left",
                    "kmctl audit checks list",
                )
            )
    if result.refused:
        raise typer.Exit(1)


@checks_app.command(
    "run",
    epilog=(
        "Examples:\n\n"
        "  kmctl audit checks run\n\n"
        "  kmctl audit checks run --all --json\n\n"
        "It reruns each stored check whose files changed: the content of a file "
        "it reads, or the files its globs match. With --all it reruns every "
        "one. A holding check is measured again when its steps or reads moved. "
        "A check that failed only because the extra was missing reruns too. It "
        "calls no model. Statuses: holds, not measured (holds, but had no change "
        "to try), weak, fails, drift (fails and the check says the claim is "
        "wrong), skipped (needs kmctl\\[audit]), reason, stale reason (a file its "
        "lines came from changed; todo hands it out again), no check. Exit 0 whatever the checks find (audits report only, ADR "
        "0005), 1 only when it cannot run. It writes only .kmctl/."
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
    from kmctl.claims import AuditError
    from kmctl.claims.check_verbs import run

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
        "  kmctl audit checks list\n\n"
        "  kmctl audit checks list .okf/manifesto.md --status fails\n\n"
        "  kmctl audit checks list --json\n\n"
        "It reads the store as the last kmctl audit checks run or submit left "
        "it; run kmctl audit checks run first for the current state."
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

    from kmctl.claims import AuditError
    from kmctl.claims.check_verbs import Status, list_checks

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


@audit_app.command(
    "judge",
    epilog=(
        "Examples:\n\n"
        "  kmctl audit judge failure 3acd0efc57ab --json\n\n"
        "  kmctl audit judge link 3acd0efc57ab 5daa573f16f0\n\n"
        "  cat lines.txt | kmctl audit judge claim 0369c52d377b --json\n\n"
        "The one model call kmctl makes, and only when you switch a question on "
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
        "nearby or the claim). Each answer is kept in .kmctl/audit.sqlite under "
        "a hash of the question, model and state, so asking again sends nothing "
        "until the check, its result or the model changes. The key is read only "
        "from the variable api_key_env names and is never printed. Set "
        "LANGSMITH_TRACING=true to trace each call to LangSmith. Needs the "
        "kmctl\\[audit] extra. Exit 1 when a question is refused or fails."
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
            help="Check ids from kmctl audit checks list, or a claim id from kmctl audit claims list --claims.",
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
    import importlib.util

    from pydantic import TypeAdapter

    from kmctl.audit_settings import QUESTIONS, Question, load, settings_path
    from kmctl.claims import AuditError
    from kmctl.claims.sections import resolve_target
    from kmctl.claims.store import Store
    from kmctl.judge import INSTALL, Judgement, judge
    from kmctl.tracing import tracing_on

    if question not in QUESTIONS:
        _refuse("judge", f"unknown question {question!r}; use failure, claim or link")
    if question == "claim" and len(ids) != 1:
        _refuse(
            "judge", "the claim question takes one claim id, with its lines on stdin"
        )
    if importlib.util.find_spec("tenacity") is None:
        _refuse("judge", f"kmctl audit judge needs the kmctl[audit] extra; {INSTALL}")
    if tracing_on() and importlib.util.find_spec("langsmith") is None:
        _refuse(
            "judge",
            f"LANGSMITH_TRACING=true needs langsmith from the kmctl[audit] extra; {INSTALL}",
        )
    try:
        settings = load(config)
        if not settings.decisions.question(cast(Question, question)).enabled:
            raise AuditError(
                f"the {question} question is off; switch it on under [decisions.{question}] "
                f"(enabled, provider, model) in {settings.source or settings_path(config)}"
            )
        lines = sys.stdin.read() if question == "claim" else ""
        target = resolve_target(path)
        with Store(target.root) as store:
            results = asyncio.run(
                judge(store, settings, cast(Question, question), ids, lines)
            )
    except (AuditError, sqlite3.Error) as error:
        _refuse("judge", str(error))
        return
    answered = [r for r in results if isinstance(r, Judgement)]
    failed = [
        (i, r)
        for i, r in zip(ids, results, strict=True)
        if not isinstance(r, Judgement)
    ]
    for subject, error in failed:
        typer.echo(f"kmctl audit judge: refused: {subject}: {error}", err=True)
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


@audit_app.command(
    "coverage",
    epilog=(
        "Examples:\n\n"
        "  kmctl audit coverage\n\n"
        "  kmctl audit coverage --files 10\n\n"
        "  kmctl audit coverage --json\n\n"
        "A line is covered when the last run of a stored check matched it: a "
        "grep line, the whole node a code pattern matched, a definition or an "
        "import. A file a check only reads (file, query and help steps) is read, "
        "not covered. The code is every file a check may read, without tests, "
        "fixtures, evals, lock files and the folders harnesses install packages "
        "into; blank lines do not count. A check whose files changed since its "
        "last run is stale and its lines are not counted until kmctl audit "
        "checks run reruns it. Run kmctl audit checks run --all once when checks "
        "were stored before kmctl recorded matched lines. kmctl "
        "audit ui shows the same numbers line by line."
    ),
)
def audit_coverage(
    path: Annotated[
        Path,
        typer.Argument(
            metavar="[.|.okf]",
            help="The repository to measure: it, its bundle or a path in it. Default: the current directory.",
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
    from kmctl.claims import AuditError
    from kmctl.claims.coverage import coverage

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
            "counted; run kmctl audit checks run to rerun them"
        )
    bare = sorted(
        (f for f in measured.by_file if not f.covered), key=lambda f: -f.lines
    )
    for f in bare[:files]:
        typer.echo(f"no line matched  {f.path}  ({f.lines} lines)")


@audit_app.command(
    "ui",
    epilog=(
        "Examples:\n\n"
        "  kmctl audit ui\n\n"
        "  kmctl audit ui .okf --port 0 --no-open\n\n"
        "  kmctl audit ui --by human:sam --config ci-audit.toml\n\n"
        "Serves a page on 127.0.0.1 that shows each document with its claims, "
        "their checks and how sure each check is, read from .kmctl/audit.sqlite. "
        "On the page you give a claim or its check a thumbs up or down and a "
        "note, and say whether the claim holds or is false. A thumbs down, or a "
        "verdict the check disagrees with, sends the work back: kmctl audit "
        "claims todo hands out the section again and kmctl audit checks todo "
        "the claim again, each with your note, and the agent's next submit "
        "marks it answered. A note alone waits for the next time the item is "
        "handed out. A verdict lasts while the files it was given on are "
        "unchanged, and outranks the check in what the page marks. Thumbs-up "
        "answers are shown to agents as examples. The Second opinion button "
        "asks the decision model kmctl audit judge uses (link for a check that "
        "holds, failure for one that fails, claim for a reason); it needs the "
        "kmctl\\[audit] extra and the question switched on in audit.toml. The "
        "server answers only requests from this machine. Stop it with Ctrl-C."
    ),
)
def audit_ui(
    path: Annotated[
        Path,
        typer.Argument(
            metavar="[.|.okf]",
            help="The repository to show: it, its bundle or a path in it. Default: the current directory.",
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
    from kmctl.claims import AuditError
    from kmctl.claims.ui import serve

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


@audit_app.command(
    "guard",
    epilog=(
        "Examples:\n\n"
        "  kmctl audit guard --allow claims\n\n"
        "  kmctl audit guard --allow checks\n\n"
        "A Claude Code PreToolUse hook for the kmctl-claims-extractor and "
        "kmctl-check-writer agents, set in their front matter. It reads the "
        "hook's JSON on stdin and lets a Bash call through only when it is one "
        "kmctl audit GROUP command, optionally after cd DIR &&, optionally fed "
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
            help="The kmctl audit group the agent may run: claims or checks.",
        ),
    ],
) -> None:
    """Allow a Bash call only when it is one kmctl audit command, as a PreToolUse hook."""
    from kmctl.claims.guard import GROUPS, refusal

    if allow not in GROUPS:
        typer.echo(
            f"kmctl audit guard: refused: unknown group {allow!r} from --allow; use claims or checks",
            err=True,
        )
        raise typer.Exit(2)
    reason = refusal(sys.stdin.read(), allow)
    if reason is not None:
        typer.echo(f"kmctl audit guard: blocked: {reason}", err=True)
        raise typer.Exit(2)


def main() -> None:
    """Run the kmctl CLI, or the project's pinned kmctl when its lock pins another release."""
    code = hand_off(sys.argv[1:])
    if code is not None:
        raise SystemExit(code)
    app()
