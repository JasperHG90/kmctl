"""kmctl's session hook (invariant I1) and okf's MCP launcher, which kmctl's package ships.

The hook tests are invariant I1's: the package's one SessionStart hook exits
0 when kmctl is missing or fails (ADR 0004). HOME points at a scratch
folder, so nothing reaches the real one. kmctl plugin patch is tested in
test_plugin_patch.py.
"""

from __future__ import annotations

import json
import subprocess
from importlib.metadata import version
from pathlib import Path

import pytest
from fixtures.fake_tools import FakeTools
from typer.testing import CliRunner, Result

from kmctl import app, plugin

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "apm" / ".apm" / "skills"
REF = f"v{version('kmctl')}"
APM = ["--from", "apm-cli==0.33.0", "apm"]
GITHUB = "https://github.com/JasperHG90/Knowledge-management.git"


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A scratch HOME, with CLAUDE_CONFIG_DIR and XDG_DATA_HOME under it."""
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home / ".claude"))
    monkeypatch.setenv("XDG_DATA_HOME", str(home / ".local" / "share"))
    return home


@pytest.fixture
def repo(tmp_path: Path, home: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A scratch repository as the working folder."""
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.chdir(repo)
    return repo


def _kmctl(*args: str) -> Result:
    """Run kmctl in-process with ``args``."""
    return CliRunner().invoke(app, list(args))


def test_hook_the_package_ships_is_one_sessionstart_entry() -> None:
    """kmctl's own hook is one SessionStart entry relaying kmctl briefing (I1), shipped in apm/claude/."""
    shipped = json.loads((ROOT / "apm/claude/.apm/hooks/hooks.json").read_text())

    assert list(shipped["hooks"]) == ["SessionStart"]
    [group] = shipped["hooks"]["SessionStart"]
    assert group["hooks"] == [
        {
            "type": "command",
            "description": plugin.HOOK_DESCRIPTION,
            "command": plugin.HOOK_COMMAND,
            "timeout": 10,
        }
    ]


def _installed_hook_command(repo: Path) -> str:
    """The command of the SessionStart hook kmctl's package ships."""
    return plugin.hook_entry()["command"]


def _run_hook(command: str, cwd: Path, path: str) -> subprocess.CompletedProcess[str]:
    """Run a hook command in ``cwd`` with only ``path`` on PATH."""
    return subprocess.run(
        ["/bin/sh", "-c", command],
        env={"PATH": path, "HOME": str(cwd)},
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def test_hook_without_kmctl_exits_zero_with_hint(repo: Path, tmp_path: Path) -> None:
    result = _run_hook(_installed_hook_command(repo), tmp_path, "/usr/bin:/bin")

    assert result.returncode == 0
    assert "uv tool install" in result.stdout


def test_hook_exits_zero_when_kmctl_fails(repo: Path, tmp_path: Path) -> None:
    command = _installed_hook_command(repo)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "kmctl"
    fake.write_text("#!/bin/sh\nexit 3\n")
    fake.chmod(0o755)

    result = _run_hook(command, tmp_path, f"{bin_dir}:/usr/bin:/bin")

    assert result.returncode == 0
    assert "kmctl briefing failed" in result.stdout


def _launcher_args(script: str, cwd: Path, tmp_path: Path) -> list[str]:
    """Run an MCP launcher in ``cwd`` with a fake uv; return the args uv got."""
    tools = FakeTools(tmp_path / "launcher", tools=("uv",))
    subprocess.run(["sh", "-c", script], cwd=cwd, env={"PATH": tools.path}, check=True)
    [call] = tools.calls("uv")
    return call.args


def test_mcp_launcher_finds_okf_from_subfolder(repo: Path, tmp_path: Path) -> None:
    (repo / ".okf").mkdir()
    deep = repo / "src" / "pkg"
    deep.mkdir(parents=True)

    args = _launcher_args(plugin.okf_mcp_launcher(), deep, tmp_path)

    assert args == ["run", plugin.okf_mcp_url(), str((repo / ".okf").resolve())]


def test_mcp_launcher_without_okf_passes_dot_okf(tmp_path: Path) -> None:
    lonely = tmp_path / "lonely"
    lonely.mkdir()

    args = _launcher_args(plugin.okf_mcp_launcher(), lonely, tmp_path)

    assert args == ["run", plugin.okf_mcp_url(), ".okf"]


def test_mcp_launcher_tries_each_start_in_order(repo: Path, tmp_path: Path) -> None:
    (repo / ".okf").mkdir()
    (repo / "sub").mkdir()
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    script = plugin.okf_mcp_launcher(
        starts=('"$UNSET_START"', f'"{tmp_path}/missing"', f'"{repo}/sub"', '"$PWD"')
    )

    args = _launcher_args(script, elsewhere, tmp_path)

    assert args == ["run", plugin.okf_mcp_url(), str((repo / ".okf").resolve())]
