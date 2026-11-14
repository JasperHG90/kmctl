"""The audit left kmctl for its own package, kmaudit (ADR 0043): kmctl holds and advertises none of it."""

import subprocess
from importlib.metadata import metadata
from pathlib import Path

from typer.testing import CliRunner

from kmctl import app

ROOT = Path(__file__).resolve().parents[1]
#: Where `kmctl audit` may still be written: loop history, the bundle's log and
#: prototypes, decision records (accepted ones keep their history notes,
#: superseded ones their text), and the Action's own audit-mode refusal, which
#: is kmctl's CI audit, not the audit that moved.
ALLOWED = (
    ":(exclude).loop",
    ":(exclude).okf/log.md",
    ":(exclude).okf/prototypes",
    ":(exclude).okf/decisions",
    ":(exclude)action.yml",
    ":(exclude)docs/how-to/install-the-plugin-and-the-ci-action.md",
    ":(exclude)tests/test_no_audit.py",
)


def test_kmctl_has_no_audit_group() -> None:
    result = CliRunner().invoke(app, ["audit", "--help"])

    assert result.exit_code == 2
    assert "No such command 'audit'" in result.output


def test_kmctl_has_no_audit_extra() -> None:
    extras = metadata("kmctl").get_all("Provides-Extra") or []

    assert "audit" not in extras


def test_no_file_mentions_kmctl_audit_outside_history() -> None:
    found = subprocess.run(
        [
            "git",
            "grep",
            "-n",
            "-e",
            "kmctl audit",
            "-e",
            "kmctl\\[audit\\]",
            "--",
            ".",
            *ALLOWED,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout

    assert found == ""


def test_readme_mentions_both_packages_and_links_kmaudit() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "packages/kmaudit/README.md" in readme
