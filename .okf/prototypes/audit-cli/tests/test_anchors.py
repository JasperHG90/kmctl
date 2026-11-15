"""Tests for resolving what a claim names and settling claims with no model, on a real git repository."""

import pathlib as plb
import subprocess

import pytest

from audit_cli.checks.anchors import Evidence, located, settle
from audit_cli.checks.steps import Repository

SCRIPT = '''import argparse
import os


def run_shell(cmd):
    """Run a command."""


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    publish = sub.add_parser("publish")
    publish.add_argument("--min-severity", default="high")
    publish.add_argument("--dry-run")
'''


def git(root: plb.Path, *args: str) -> None:
    """Run git quietly in ``root``."""
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


@pytest.fixture
def evidence(tmp_path: plb.Path) -> Evidence:
    """A repository with an argparse script, a file that was deleted in a commit, and a test that names it."""
    root = tmp_path / "anchored"
    (root / "action").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "action" / "agent.py").write_text(SCRIPT)
    (root / "action" / "old.sh").write_text("echo old\n")
    git(root, "init", "-q")
    git(root, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
    git(root, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "first")
    git(root, "rm", "-q", "action/old.sh")
    (root / "tests" / "test_gone.py").write_text("GONE = ['old_helper']\n")
    git(root, "add", "-A")
    return Evidence(Repository(root), walk_help=False)


@pytest.mark.parametrize(
    ("claim", "verdict", "rule"),
    [
        ("`action/old.sh` no longer exists in the repository.", True, "absent"),
        ("`action/agent.py` no longer exists in the repository.", False, "absent"),
        ("`old_helper` no longer exists.", True, "absent"),
        ("The default `--min-severity` is `high`.", True, "default"),
        ("The default `--min-severity` is `low`.", False, "default"),
        ("`action/agent.py` has a `run_shell` tool.", True, "has"),
        ("`action/agent.py` has a `run_bash` tool.", False, "has"),
        ("No import of json exists in `action/agent.py`.", True, "import"),
        ("No import of os exists in `action/agent.py`.", False, "import"),
        ("`action/agent.py` has a `--dry-run` flag.", True, "has flag"),
        ("The worker retries twice.", None, ""),
    ],
)
def test_settled_claims_and_the_rule_that_settled_them(
    evidence: Evidence, claim: str, verdict: bool | None, rule: str
) -> None:
    """A claim in a shape the anchors decide gets a verdict, a wrong one included; any other claim gets none."""
    settled = settle(evidence, claim)
    assert (settled.verdict, settled.rule) == (verdict, rule)


def test_anchors_say_where_each_named_thing_is(evidence: Evidence) -> None:
    """A path, a command's flag and a definition each resolve to the file that holds them."""
    anchors = settle(evidence, "`action/agent.py publish` takes `--min-severity`; `run_shell` runs commands.").anchors
    assert [(a.kind, a.status) for a in anchors] == [("command", "found"), ("flag", "found"), ("name", "defined")]
    assert located(anchors, evidence.repo) == ["action/agent.py"]


def test_the_help_walk_is_read_from_the_cache_while_its_code_is_unchanged(tmp_path: plb.Path) -> None:
    """With a cache that already holds the commands for this code, no CLI runs and the cached commands are used."""
    root = tmp_path / "cli"
    (root / "x").mkdir(parents=True)
    (root / "x" / "cli.py").write_text("def main(): pass\n")
    (root / "pyproject.toml").write_text('[project]\nname = "x"\n[project.scripts]\nx = "x.cli:main"\n')
    git(root, "init", "-q")
    git(root, "add", "-A")
    kept: dict[str, object] = {}
    repo = Repository(root)
    first = Evidence(repo, cache=(kept.get, kept.__setitem__), walk_help=True)
    assert len(kept) == 1  # walked once (x --help fails here, so x has no flags) and kept
    (key,) = kept
    kept[key] = [{"path": "x go", "flags": {"--fast": None}}]
    second = Evidence(Repository(root), cache=(kept.get, kept.__setitem__), walk_help=True)
    assert "x go" in second.commands and "x go" not in first.commands
    (root / "x" / "cli.py").write_text("def main(): return 1\n")
    third = Evidence(Repository(root), cache=(kept.get, kept.__setitem__), walk_help=True)
    assert "x go" not in third.commands and len(kept) == 2  # the code changed, so it walked again
