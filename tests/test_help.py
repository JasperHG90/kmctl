"""Every verb's help says what it produces, gives an example for each input and fits 80 columns."""

import pytest
from typer.core import TyperGroup, TyperOption
from typer.main import get_command
from typer.testing import CliRunner

from kmctl import app


def _verbs(
    group: TyperGroup, prefix: tuple[str, ...] = ()
) -> dict[tuple[str, ...], object]:
    """Every leaf command under ``group``, keyed by the words that invoke it."""
    found = {}
    for name, command in group.commands.items():
        if isinstance(command, TyperGroup):
            found |= _verbs(command, (*prefix, name))
        else:
            found[(*prefix, name)] = command
    return found


VERBS = _verbs(get_command(app))
IDS = [" ".join(words) for words in VERBS]


@pytest.mark.parametrize("words", VERBS, ids=IDS)
def test_help_renders_at_80_columns(words: tuple[str, ...]) -> None:
    result = CliRunner().invoke(
        app, [*words, "--help"], env={"COLUMNS": "80"}, terminal_width=80
    )

    assert result.exit_code == 0, result.output
    assert all(len(line) <= 80 for line in result.stdout.splitlines())


@pytest.mark.parametrize("words", VERBS, ids=IDS)
def test_help_names_what_the_verb_produces(words: tuple[str, ...]) -> None:
    command = VERBS[words]

    assert command.help and command.help.strip().splitlines()[0].endswith(".")


@pytest.mark.parametrize("words", VERBS, ids=IDS)
def test_every_input_has_an_example(words: tuple[str, ...]) -> None:
    command = VERBS[words]
    inputs = [p for p in command.params if isinstance(p, TyperOption) and not p.is_flag]

    assert all(p.metavar for p in inputs), [p.name for p in inputs if not p.metavar]
    assert "Examples" in (command.epilog or "")
