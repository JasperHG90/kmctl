"""kmctl: knowledge management for repositories that keep docs/ and an OKF bundle."""

import json
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
from typing import Annotated

import typer

from kmctl.handoffs import live_handoffs
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


def main() -> None:
    """Run the kmctl CLI."""
    app()
