"""Every verb's help says what it produces, gives an example for each input and fits 80 columns."""

import pytest
from typer.core import TyperOption
from typer.main import get_command
from typer.testing import CliRunner

from kmctl import app

VERBS = sorted(get_command(app).commands)


@pytest.mark.parametrize("verb", VERBS)
def test_help_renders_at_80_columns(verb: str) -> None:
    result = CliRunner().invoke(
        app, [verb, "--help"], env={"COLUMNS": "80"}, terminal_width=80
    )

    assert result.exit_code == 0, result.output
    assert all(len(line) <= 80 for line in result.stdout.splitlines())


@pytest.mark.parametrize("verb", VERBS)
def test_help_names_what_the_verb_produces(verb: str) -> None:
    command = get_command(app).commands[verb]

    assert command.help and command.help.strip().splitlines()[0].endswith(".")


@pytest.mark.parametrize("verb", VERBS)
def test_every_input_has_an_example(verb: str) -> None:
    command = get_command(app).commands[verb]
    inputs = [p for p in command.params if isinstance(p, TyperOption) and not p.is_flag]

    assert all(p.metavar for p in inputs), [p.name for p in inputs if not p.metavar]
    assert "Examples" in (command.epilog or "")
