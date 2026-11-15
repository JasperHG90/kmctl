"""Which package a path belongs to, for its release notes and release-tag's late-commit check."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.release_paths import owns

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "release_paths.py"


@pytest.mark.parametrize(
    ("path", "kmctl", "kmaudit"),
    [
        ("packages/kmctl/src/kmctl/cli.py", True, False),
        ("packages/kmaudit/src/kmaudit/cli.py", False, True),
        ("docs/how-to/x.md", True, False),
        # kmaudit's pages in docs/ start with kmaudit-.
        ("docs/reference/kmaudit-commands.md", False, True),
        ("docs/how-to/kmaudit-x.md", False, True),
        ("docs/reference/commands.md", True, False),
        ("docs/reference/x-kmaudit-y.md", True, False),
        ("packages/kmctl/kmaudit-x.md", True, False),
        ("README.md", True, False),
        ("action.yml", True, False),
        (".github/workflows/release.yml", True, False),
        # Bookkeeping ships in no package.
        (".loop/tickets/x.json", False, False),
        (".okf/decisions/0001-x.md", False, False),
        (".claude/rules/x.md", False, False),
        ("uv.lock", False, False),
        ("packages/other/x.py", False, False),
    ],
)
def test_owns(path: str, kmctl: bool, kmaudit: bool) -> None:
    """kmaudit owns packages/kmaudit/ and docs pages named kmaudit-*, kmctl packages/kmctl/ and the rest outside packages/, and nobody the bookkeeping."""
    assert (owns("kmctl", path), owns("kmaudit", path)) == (kmctl, kmaudit)


@pytest.mark.parametrize(
    ("package", "paths", "code"),
    [
        ("kmctl", ".okf/summary.md\nuv.lock\n", 1),
        ("kmaudit", ".okf/summary.md\nuv.lock\n", 1),
        ("kmaudit", ".okf/summary.md\npackages/kmaudit/x.py\n", 0),
        ("kmctl", ".claude/rules/x.md\ndocs/y.md\n", 0),
        ("kmctl", "docs/reference/kmaudit-commands.md\n", 1),
        ("kmaudit", "docs/reference/kmaudit-commands.md\n", 0),
        ("kmctl", "", 1),
    ],
)
def test_the_command_exits_0_when_the_package_owns_any_path(
    package: str, paths: str, code: int
) -> None:
    """``release_paths.py PACKAGE`` reads paths on stdin and exits 0 when the package owns one."""
    res = subprocess.run(
        [sys.executable, str(SCRIPT), package],
        input=paths,
        capture_output=True,
        text=True,
        check=False,
    )

    assert res.returncode == code, res.stderr


def test_the_command_refuses_an_unknown_package() -> None:
    """An unknown package is a usage error, not a silent no."""
    res = subprocess.run(
        [sys.executable, str(SCRIPT), "kmfoo"],
        input="docs/x.md\n",
        capture_output=True,
        text=True,
        check=False,
    )

    assert res.returncode == 2


def test_the_command_reads_every_path_so_the_writer_never_dies_of_sigpipe(
    tmp_path: Path,
) -> None:
    """An owned path first, then 20000 more: the pipeline must succeed under pipefail.

    release-tag pipes git diff into the command under ``set -o pipefail``. A
    command that stopped reading at the first owned path would kill the
    writer with SIGPIPE, and the step would drop a commit the package owns.
    """
    paths = tmp_path / "paths.txt"
    paths.write_text(
        "docs/a.md\n" + "".join(f"packages/kmaudit/f{i}.py\n" for i in range(20000))
    )

    res = subprocess.run(
        [
            "bash",
            "-c",
            'set -euo pipefail; if cat "$1" | "$2" "$3" kmctl; then echo owned; else echo not; fi',
            "_",
            str(paths),
            sys.executable,
            str(SCRIPT),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert res.stdout.strip() == "owned", res.stderr
