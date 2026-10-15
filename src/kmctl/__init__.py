"""kmctl: knowledge management for repositories that keep docs/ and an OKF bundle."""

import json
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
from typing import Annotated

import typer

from kmctl.checks import run_checks
from kmctl.scaffold import scaffold

app = typer.Typer(
    help="kmctl: keep a repository's docs/ and .okf/ knowledge current.",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)


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
        typer.echo("Next: write .okf/manifesto.md, then commit docs/ and .okf/")
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
    """Check that docs/ and .okf/ indexes agree with their folders."""
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


def main() -> None:
    """Run the kmctl CLI."""
    app()
