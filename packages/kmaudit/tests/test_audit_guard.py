"""kmaudit guard: the PreToolUse hook that holds the claims and checks agents to kmaudit commands."""

import json

import pytest
from kmaudit.cli import app
from typer.testing import CliRunner


def guard(command: str, allow: str = "claims", tool: str = "Bash") -> tuple[int, str]:
    payload = json.dumps(
        {"tool_name": tool, "tool_input": {"command": command}, "agent_type": "x"}
    )
    result = CliRunner().invoke(app, ["guard", "--allow", allow], input=payload)
    return result.exit_code, result.stderr


@pytest.mark.parametrize(
    "command",
    [
        "kmaudit claims todo .okf/manifesto.md --json",
        "cd /home/me/repo && kmaudit claims todo --json",
        (
            "kmaudit claims submit - --json --by kmctl-claims-extractor <<'ANSWERS'\n"
            '[{"section": "a#b", "key": "k", "sentences": [{"n": 1, "kind": "none", "reason": "x | y; $(z)"}]}]\n'
            "ANSWERS"
        ),
    ],
    ids=["plain", "cd-first", "heredoc-with-shell-characters-in-the-data"],
)
def test_kmaudit_commands_pass(command: str) -> None:
    assert guard(command) == (0, "")


@pytest.mark.parametrize(
    ("command", "words"),
    [
        ("kmaudit claims todo --json | python3 -c 'import sys'", "no pipes"),
        ("kmaudit claims todo --json > /tmp/x", "no pipes"),
        ("kmaudit claims todo --json; rm -rf .okf", "no pipes"),
        ("kmaudit claims todo $(cat x)", "no pipes"),
        ("grep -r foo src", "only kmaudit claims"),
        ("kmaudit checks todo --json", "only kmaudit claims"),
        ("kmaudit claims todo\nrm x", "one command per call"),
        (
            "kmaudit claims submit - <<'A'\n[]\nA\nrm -rf .okf\nA",
            "heredoc must end",
        ),
        ("kmaudit claims submit - <<A\n[]\nA", "one command per call"),
    ],
    ids=["pipe", "redirect", "chain", "substitution", "other-program", "other-group",
         "two-lines", "early-terminator", "unquoted-heredoc"],
)  # fmt: skip
def test_anything_else_is_blocked_with_exit_2(command: str, words: str) -> None:
    code, err = guard(command)

    assert code == 2
    assert words in err


def test_other_tools_pass() -> None:
    assert guard("", tool="Read") == (0, "")


def test_checks_group_for_the_check_writer() -> None:
    assert guard("kmaudit checks try - --json <<'D'\n[]\nD", allow="checks") == (
        0,
        "",
    )


def test_unknown_group_refuses() -> None:
    result = CliRunner().invoke(app, ["guard", "--allow", "everything"], input="{}")

    assert result.exit_code == 2
