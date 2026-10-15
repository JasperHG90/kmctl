"""kmctl plugin install, update and status against a real claude CLI with an isolated config.

These need the claude CLI and network access to add the scaccogatto marketplace
from GitHub, so they are skipped where claude is not on PATH.
"""

import json
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest
from typer.testing import CliRunner, Result

from kmctl import app

ROOT = Path(__file__).resolve().parents[1]
needs_claude = pytest.mark.skipif(
    shutil.which("claude") is None, reason="needs the claude CLI on PATH"
)


@pytest.fixture
def isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A scratch git repository as the working directory, with its own claude config and data dir."""
    project = tmp_path / "proj"
    project.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "claude-config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.chdir(project)
    return project


def _kmctl(*args: str) -> Result:
    return CliRunner().invoke(app, list(args))


def _listed() -> dict[str, dict]:
    out = subprocess.run(
        ["claude", "plugin", "list", "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    return {p["id"]: p for p in json.loads(out.stdout)}


@needs_claude
def test_install_pulls_okf(isolated: Path) -> None:
    result = _kmctl("plugin", "install", "--scope", "project")

    assert result.exit_code == 0, result.output
    listed = _listed()
    for plugin_id in ("kmctl@kmctl", "okf@scaccogatto"):
        assert listed[plugin_id]["scope"] == "project", plugin_id
        assert Path(listed[plugin_id]["projectPath"]).resolve() == isolated.resolve(), (
            plugin_id
        )


@needs_claude
def test_install_twice_changes_nothing(isolated: Path, tmp_path: Path) -> None:
    first = _kmctl("plugin", "install", "--scope", "project")
    assert first.exit_code == 0, first.output
    before = _listed()
    staged = tmp_path / "data" / "kmctl" / "marketplace"
    files_before = {p: p.read_bytes() for p in staged.rglob("*") if p.is_file()}

    result = _kmctl("plugin", "install", "--scope", "project")

    assert result.exit_code == 0, result.output
    assert {k: (p["version"], p["scope"]) for k, p in _listed().items()} == {
        k: (p["version"], p["scope"]) for k, p in before.items()
    }
    assert {p: p.read_bytes() for p in staged.rglob("*") if p.is_file()} == files_before


@needs_claude
def test_staged_version_matches_cli(isolated: Path, tmp_path: Path) -> None:
    from importlib.metadata import version

    _kmctl("plugin", "install", "--scope", "project")
    manifest = tmp_path / "data/kmctl/marketplace/plugin/.claude-plugin/plugin.json"

    assert json.loads(manifest.read_text())["version"] == version("kmctl")
    assert _listed()["kmctl@kmctl"]["version"] == version("kmctl")


@needs_claude
def test_update_after_bump(isolated: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _kmctl("plugin", "install", "--scope", "project")
    markets = subprocess.run(
        ["claude", "plugin", "marketplace", "list", "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    path_before = {m["name"]: m.get("path") for m in json.loads(markets.stdout)}[
        "kmctl"
    ]
    monkeypatch.setattr("kmctl.plugin.cli_version", lambda: "99.0.0")

    result = _kmctl("plugin", "update", "--scope", "project")

    assert result.exit_code == 0, result.output
    markets = subprocess.run(
        ["claude", "plugin", "marketplace", "list", "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert {m["name"]: m.get("path") for m in json.loads(markets.stdout)}[
        "kmctl"
    ] == path_before
    assert _listed()["kmctl@kmctl"]["version"] == "99.0.0"


@needs_claude
def test_status_reports_mismatch_and_missing_path(
    isolated: Path, tmp_path: Path
) -> None:
    _kmctl("plugin", "install", "--scope", "project")
    manifest = tmp_path / "data/kmctl/marketplace/plugin/.claude-plugin/plugin.json"
    data = json.loads(manifest.read_text())
    data["version"] = "0.0.1"
    manifest.write_text(json.dumps(data))

    mismatch = _kmctl("plugin", "status")
    shutil.rmtree(tmp_path / "data/kmctl/marketplace")
    missing = _kmctl("plugin", "status")

    assert "mismatch" in mismatch.stdout
    assert "kmctl plugin install" in missing.stdout


def test_wheel_carries_plugin(tmp_path: Path) -> None:
    subprocess.run(
        ["uv", "build", "-q", "--wheel", "-o", str(tmp_path)],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    [wheel] = tmp_path.glob("kmctl-*.whl")
    names = set(zipfile.ZipFile(wheel).namelist())

    assert "kmctl/_plugin/.claude-plugin/plugin.json" in names
    assert "kmctl/_plugin/hooks/hooks.json" in names
    assert "kmctl/_marketplace.json" in names


@needs_claude
def test_install_declares_okf_in_each_repository(
    isolated: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _kmctl("plugin", "install", "--scope", "project")
    second = tmp_path / "second"
    second.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=second, check=True)
    monkeypatch.chdir(second)

    result = _kmctl("plugin", "install", "--scope", "project")

    assert result.exit_code == 0, result.output
    settings = json.loads((second / ".claude" / "settings.json").read_text())
    assert "scaccogatto" in settings.get("extraKnownMarketplaces", {})


@needs_claude
def test_status_ignores_other_repositories(
    isolated: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _kmctl("plugin", "install", "--scope", "project")
    other = tmp_path / "other"
    other.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=other, check=True)
    monkeypatch.chdir(other)

    out = _kmctl("plugin", "status").stdout

    assert "not installed here" in out
    assert "installed plugin" not in out


@needs_claude
def test_installed_version_check_after_upgrade(
    isolated: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _kmctl("plugin", "install", "--scope", "project")
    monkeypatch.setattr("kmctl.plugin.cli_version", lambda: "99.0.0")

    status = _kmctl("plugin", "status").stdout
    plain = _kmctl("plugin", "install", "--scope", "project")
    fixed = _kmctl("plugin", "update", "--scope", "project")

    assert "installed plugin" in status
    assert "kmctl plugin update" in status
    assert "kmctl plugin install" not in status
    assert plain.exit_code == 1
    assert "run kmctl plugin update" in plain.stderr
    assert fixed.exit_code == 0, fixed.output
    assert "problem" not in _kmctl("plugin", "status").stdout
