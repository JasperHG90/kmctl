"""``scripts/check_wheel.py``: a built wheel carries what pyproject force-includes (ADR 0012)."""

from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from scripts.check_wheel import expected_entries, missing_entries

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_wheel.py"
COMPLETE = [
    "kmctl/__init__.py",
    "kmctl/_skills/audit/SKILL.md",
    "kmctl/_skills/handoff/SKILL.md",
]


def _wheel(path: Path, names: list[str]) -> Path:
    """Write a zip with the given member names, standing in for a wheel."""
    with zipfile.ZipFile(path, "w") as zf:
        for name in names:
            zf.writestr(name, "x")
    return path


def _check(wheel: Path) -> subprocess.CompletedProcess[str]:
    """Run the script on ``wheel`` against this repository's pyproject.toml."""
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(wheel),
            "--pyproject",
            str(ROOT / "pyproject.toml"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_expected_entries_follow_pyproject() -> None:
    """The package's skills folder, as pyproject force-includes it."""
    assert expected_entries(ROOT / "pyproject.toml") == ["kmctl/_skills/"]


def test_a_complete_wheel_passes(tmp_path: Path) -> None:
    """A wheel holding the skills passes."""
    res = _check(_wheel(tmp_path / "kmctl-0.1.0-py3-none-any.whl", COMPLETE))

    assert res.returncode == 0, res.stderr


@pytest.mark.parametrize("dropped", ["kmctl/_skills/"])
def test_a_wheel_without_an_entry_fails(tmp_path: Path, dropped: str) -> None:
    """A wheel without the skills is named, and the script exits 1."""
    names = [n for n in COMPLETE if not n.startswith(dropped)]
    wheel = _wheel(tmp_path / "kmctl-0.1.0-py3-none-any.whl", names)

    res = _check(wheel)

    assert missing_entries(wheel, expected_entries(ROOT / "pyproject.toml")) == [
        dropped
    ]
    assert res.returncode == 1
    assert f"lacks {dropped}" in res.stderr
