"""``scripts/smoke_wheel.py``: a wheel installs in a fresh venv and works as shipped (ADR 0012)."""

from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from scripts.smoke_wheel import version_matches, wheel_version

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "smoke_wheel.py"
PLUGIN_MANIFEST = "kmctl/_plugin/.claude-plugin/plugin.json"


def _wheel(tmp_path: Path, version: str, prints: str, plugin: bool = True) -> Path:
    """Write a dependency-free kmctl wheel whose ``kmctl --version`` prints ``prints``.

    It installs without reaching an index, so the smoke script's checks run offline.
    """
    info = f"kmctl-{version}.dist-info"
    files = {
        "kmctl/__init__.py": f"def main() -> None:\n    print({prints!r})\n",
        f"{info}/METADATA": f"Metadata-Version: 2.1\nName: kmctl\nVersion: {version}\n",
        f"{info}/WHEEL": "Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
        f"{info}/entry_points.txt": "[console_scripts]\nkmctl = kmctl:main\n",
    }
    if plugin:
        files[PLUGIN_MANIFEST] = '{"name": "kmctl"}\n'
    files[f"{info}/RECORD"] = "".join(
        f"{name},,\n" for name in [*files, f"{info}/RECORD"]
    )
    wheel = tmp_path / f"kmctl-{version}-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as zf:
        for name, text in files.items():
            zf.writestr(name, text)
    return wheel


def _smoke(wheel: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run the smoke script on ``wheel``."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(wheel), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_a_wheel_at_the_release_version_with_its_plugin_passes(tmp_path: Path) -> None:
    """A wheel that reports the version asked for and holds the plugin manifest passes."""
    res = _smoke(_wheel(tmp_path, "0.2.0", "kmctl 0.2.0"), "--version", "0.2.0")

    assert res.returncode == 0, res.stderr


def test_a_wheel_reporting_another_version_fails(tmp_path: Path) -> None:
    """A wheel whose ``kmctl --version`` is not ``--version`` fails, naming both."""
    res = _smoke(_wheel(tmp_path, "0.2.0", "kmctl 0.2.0"), "--version", "0.2.1")

    assert res.returncode == 1
    assert "'kmctl 0.2.0', not 0.2.1" in res.stderr


def test_the_version_defaults_to_the_wheel_file_name(tmp_path: Path) -> None:
    """Without ``--version``, the wheel must report the version in its file name."""
    res = _smoke(_wheel(tmp_path, "0.2.0", "kmctl 0.1.0"))

    assert res.returncode == 1
    assert "not 0.2.0" in res.stderr


def test_a_wheel_without_the_plugin_manifest_fails(tmp_path: Path) -> None:
    """A wheel that installs no plugin manifest fails, naming the missing file."""
    res = _smoke(
        _wheel(tmp_path, "0.2.0", "kmctl 0.2.0", plugin=False), "--version", "0.2.0"
    )

    assert res.returncode == 1
    assert "_plugin/.claude-plugin/plugin.json" in res.stderr


def test_wheel_version_reads_the_file_name() -> None:
    """The version is the wheel file name's second field."""
    assert wheel_version(Path("kmctl-0.2.0a1-py3-none-any.whl")) == "0.2.0a1"


@pytest.mark.parametrize(
    ("printed", "expect", "ok"),
    [
        ("kmctl 0.2.1\n", "0.2.1", True),
        ("kmctl 0.2.10\n", "0.2.1", False),
        ("kmctl 10.2.1\n", "0.2.1", False),
        ("kmctl 0.2.1a1\n", "0.2.1", False),
    ],
)
def test_version_matches_exactly(printed: str, expect: str, ok: bool) -> None:
    """The smoke check compares the version token exactly, never as a substring."""
    assert version_matches(printed, expect) is ok


@pytest.mark.integration
def test_the_wheel_built_from_this_tree_passes(tmp_path: Path) -> None:
    """The real kmctl wheel passes both wheel checks; installing it fetches typer and pyyaml."""
    build = subprocess.run(
        ["uv", "build", "-q", "--wheel", "-o", str(tmp_path), str(ROOT)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert build.returncode == 0, build.stderr
    (wheel,) = tmp_path.glob("*.whl")

    checked = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_wheel.py"), str(wheel)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    smoked = _smoke(wheel)

    assert checked.returncode == 0, checked.stderr
    assert smoked.returncode == 0, smoked.stderr
