"""The slim CLI: only mcp, ui, namespaces, briefing and the two list commands, and no message names a dropped verb."""

import re
from pathlib import Path
from typing import Any

import pytest
import typer
from kmaudit.cli import app
from typer.testing import CliRunner

SOURCE = Path(__file__).resolve().parents[1] / "src" / "kmaudit"
ADR = (
    Path(__file__).resolve().parents[3]
    / ".okf"
    / "decisions"
    / "0043-the-audit-is-its-own-library-kmaudit-served-over-mcp.md"
)

#: Each dropped verb and the words its one line must hold: the tool that replaced it.
DROPPED = {
    ("claims", "todo"): "claims_todo",
    ("claims", "submit"): "claims_submit",
    ("checks", "todo"): "checks_todo",
    ("checks", "try"): "checks_try",
    ("checks", "submit"): "checks_submit",
    ("checks", "run"): "checks_run",
    ("judge",): "judge MCP tool",
    ("coverage",): "coverage MCP tool",
    ("guard",): "agents call the MCP tools",
}

#: A dropped verb written as a command: ``kmaudit judge`` or a bare ``claims todo``.
COMMAND = re.compile(
    r"kmaudit\s+(?:audit\s+)?(?:judge|coverage|guard)\b"
    r"|\b(?:claims\s+(?:todo|submit)|checks\s+(?:todo|try|submit|run))\b"
)


def _visible(group: Any) -> dict[str, Any]:
    """The commands ``--help`` lists for a click group, hidden ones left out."""
    return {n: c for n, c in group.commands.items() if not c.hidden}


def test_help_lists_exactly_the_kept_commands() -> None:
    shown = _visible(typer.main.get_command(app))

    assert set(shown) == {"mcp", "ui", "namespaces", "briefing", "claims", "checks"}
    for group in ("claims", "checks"):
        assert set(_visible(shown[group])) == {"list"}
    out = CliRunner().invoke(app, ["--help"]).stdout
    for name in ("judge", "coverage", "guard", "todo", "submit"):
        assert not re.search(rf"│ {name}\b", out)


@pytest.mark.parametrize("words", list(DROPPED), ids=" ".join)
@pytest.mark.parametrize(
    "extra", [[], ["--json", ".okf"], ["--help"]], ids=["bare", "args", "help"]
)
def test_a_dropped_verb_exits_2_naming_its_replacement(
    words: tuple[str, ...], extra: list[str]
) -> None:
    result = CliRunner().invoke(app, [*words, *extra], input="{}")

    assert result.exit_code == 2
    assert result.stdout == ""
    lines = result.stderr.strip().splitlines()
    assert len(lines) == 1
    assert lines[0].startswith(f"kmaudit {' '.join(words)}: no longer a command;")
    assert DROPPED[words] in lines[0]


def test_guard_says_the_hook_is_gone() -> None:
    result = CliRunner().invoke(app, ["guard", "--allow", "claims"], input="{}")

    assert result.exit_code == 2
    assert "gone" in result.stderr and "kmaudit mcp" in result.stderr


def _sources() -> list[Path]:
    return sorted(SOURCE.glob("*.py")) + [SOURCE / "ui.html"]


def test_names_no_dropped_verb_in_any_source_string() -> None:
    """Every string and comment in kmaudit's modules and ui.html: the MCP
    server's instructions and tool descriptions, the answer schema's field
    descriptions, refusals, next lines and docstrings.

    cli.py builds each dropped verb's refusal from its parts, so its table
    is not a command to run; the tests above check what those lines say.
    """
    found = [
        f"{path.name}:{n}: {line.strip()}"
        for path in _sources()
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if COMMAND.search(line)
    ]

    assert found == []


def test_names_the_pattern_catches_each_dropped_verb() -> None:
    """The pattern above is only as good as what it matches."""
    for text in (
        "run kmaudit claims todo",
        "pipe them to kmaudit claims submit -",
        "kmaudit checks todo --json",
        "kmaudit checks try -",
        "kmaudit checks submit -",
        "Run kmaudit checks run, then Reload.",
        "see kmaudit judge --help",
        "kmaudit coverage --json",
        "kmaudit guard --allow claims",
        "sends the claim back to ``checks todo``",
    ):
        assert COMMAND.search(text), text
    for text in ("claims_todo", "checks_run", "kmaudit claims list", "/write-checks"):
        assert not COMMAND.search(text), text


def test_names_the_guard_hook_as_gone_in_adr_0043() -> None:
    text = ADR.read_text(encoding="utf-8")
    stays = text.index("`kmaudit guard` stays in the CLI")
    later = text[stays:]

    assert re.search(r"`kmaudit\s+guard`\s+is\s+gone", later)
    assert re.search(r"guard\s+hook\s+ADR\s+0040\s+describes\s+is\s+gone", later)
