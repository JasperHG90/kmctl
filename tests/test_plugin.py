"""The plugin has one hook, a SessionStart briefing that never blocks (ADR 0004, I1)."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HOOKS = json.loads((ROOT / "plugin/hooks/hooks.json").read_text())["hooks"]
MARKETPLACE = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())


def _hook_command() -> str:
    [entry] = HOOKS["SessionStart"]
    [hook] = entry["hooks"]
    return hook["command"]


def _run_hook(tmp_path: Path, path: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/sh", "-c", _hook_command()],
        env={"PATH": path, "HOME": str(tmp_path)},
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )


def test_plugin_has_one_sessionstart_hook() -> None:
    manifest = json.loads((ROOT / "plugin/.claude-plugin/plugin.json").read_text())

    assert "hooks" not in manifest
    assert list(HOOKS) == ["SessionStart"]
    assert "kmctl briefing" in _hook_command()


def test_hook_without_kmctl_exits_zero_with_hint(tmp_path: Path) -> None:
    result = _run_hook(tmp_path, "/usr/bin:/bin")

    assert result.returncode == 0
    assert "uv tool install" in result.stdout


def test_hook_exits_zero_when_kmctl_fails(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "kmctl"
    fake.write_text("#!/bin/sh\nexit 3\n")
    fake.chmod(0o755)

    result = _run_hook(tmp_path, f"{bin_dir}:/usr/bin:/bin")

    assert result.returncode == 0
    assert "kmctl briefing failed" in result.stdout


def test_marketplace_declares_okf_dependency() -> None:
    [plugin] = MARKETPLACE["plugins"]

    assert {"name": "okf", "marketplace": "scaccogatto"} in plugin["dependencies"]
    assert "scaccogatto" in MARKETPLACE["allowCrossMarketplaceDependenciesOn"]
    assert plugin["source"] == "./plugin"


@pytest.mark.skipif(
    shutil.which("claude") is None, reason="needs the claude CLI on PATH"
)
@pytest.mark.parametrize("target", ["plugin", "."])
def test_claude_plugin_validate_passes(target: str) -> None:
    result = subprocess.run(
        ["claude", "plugin", "validate", target],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
