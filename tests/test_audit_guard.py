"""kmctl audit guard: the PreToolUse hook that holds the claims and checks agents to kmctl audit commands."""

import json

import pytest
from typer.testing import CliRunner

from kmctl import app


def guard(command: str, allow: str = "claims", tool: str = "Bash") -> tuple[int, str]:
    payload = json.dumps(
        {"tool_name": tool, "tool_input": {"command": command}, "agent_type": "x"}
    )
    result = CliRunner().invoke(
        app, ["audit", "guard", "--allow", allow], input=payload
    )
    return result.exit_code, result.stderr


@pytest.mark.parametrize(
    "command",
    [
        "kmctl audit claims todo .okf/manifesto.md --json",
        "cd /home/me/repo && kmctl audit claims todo --json",
        (
            "kmctl audit claims submit - --json --by kmctl-claims-extractor <<'ANSWERS'\n"
            '[{"section": "a#b", "key": "k", "sentences": [{"n": 1, "kind": "none", "reason": "x | y; $(z)"}]}]\n'
            "ANSWERS"
        ),
    ],
    ids=["plain", "cd-first", "heredoc-with-shell-characters-in-the-data"],
)
def test_kmctl_audit_commands_pass(command: str) -> None:
    assert guard(command) == (0, "")


@pytest.mark.parametrize(
    ("command", "words"),
    [
        ("kmctl audit claims todo --json | python3 -c 'import sys'", "no pipes"),
        ("kmctl audit claims todo --json > /tmp/x", "no pipes"),
        ("kmctl audit claims todo --json; rm -rf .okf", "no pipes"),
        ("kmctl audit claims todo $(cat x)", "no pipes"),
        ("grep -r foo src", "only kmctl audit claims"),
        ("kmctl audit checks todo --json", "only kmctl audit claims"),
        ("kmctl audit claims todo\nrm x", "one command per call"),
        (
            "kmctl audit claims submit - <<'A'\n[]\nA\nrm -rf .okf\nA",
            "heredoc must end",
        ),
        ("kmctl audit claims submit - <<A\n[]\nA", "one command per call"),
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
    assert guard("kmctl audit checks try - --json <<'D'\n[]\nD", allow="checks") == (
        0,
        "",
    )


def test_unknown_group_refuses() -> None:
    result = CliRunner().invoke(
        app, ["audit", "guard", "--allow", "everything"], input="{}"
    )

    assert result.exit_code == 2
