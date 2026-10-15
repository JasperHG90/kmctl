"""kmctl plugin install, update and status against a real claude CLI with an isolated config.

These need the claude CLI and network access to add the scaccogatto marketplace
from GitHub, so they are skipped where claude is not on PATH.
"""

import json
import os
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


def _settings(path: Path, source: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"extraKnownMarketplaces": {"scaccogatto": {"source": source}}})
    )
    return path


@pytest.fixture
def settings_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """An empty user config folder and managed settings folder that kmctl reads."""
    user = tmp_path / "user-config"
    managed = tmp_path / "managed"
    user.mkdir()
    managed.mkdir()
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(user))
    monkeypatch.setattr("kmctl.plugin._managed_dir", lambda: managed)
    return user, managed


@pytest.mark.parametrize(
    ("source", "argument"),
    [
        ({"source": "github", "repo": "me/okf"}, "me/okf"),
        ({"source": "github", "repo": "me/okf", "ref": "v1"}, "me/okf#v1"),
        ({"source": "git", "url": "https://x.org/okf.git"}, "https://x.org/okf.git"),
        (
            {"source": "git", "url": "https://x.org/okf.git", "ref": "main"},
            "https://x.org/okf.git#main",
        ),
        ({"source": "url", "url": "https://x.org/m.json"}, "https://x.org/m.json"),
        ({"source": "directory", "path": "/opt/okf"}, "/opt/okf"),
    ],
)
def test_okf_source_from_settings(
    settings_dirs: tuple[Path, Path], source: dict, argument: str
) -> None:
    from kmctl.plugin import okf_source

    user, _ = settings_dirs
    file = _settings(user / "settings.json", source)

    assert okf_source() == (argument, file)


def test_okf_source_default_without_entry(settings_dirs: tuple[Path, Path]) -> None:
    from kmctl.plugin import OKF_SOURCE, okf_source

    assert okf_source() == (OKF_SOURCE, None)


def test_okf_source_managed_wins(settings_dirs: tuple[Path, Path]) -> None:
    from kmctl.plugin import okf_source

    user, managed = settings_dirs
    _settings(user / "settings.json", {"source": "github", "repo": "user/okf"})
    _settings(
        managed / "managed-settings.json", {"source": "github", "repo": "base/okf"}
    )
    assert okf_source()[0] == "base/okf", "a managed entry beats the user entry"

    _settings(
        managed / "managed-settings.d" / "10-a.json",
        {"source": "github", "repo": "a/okf"},
    )
    last = _settings(
        managed / "managed-settings.d" / "20-b.json",
        {"source": "github", "repo": "b/okf"},
    )

    assert okf_source() == ("b/okf", last), "the last managed file wins"


def test_okf_source_skips_dot_files(settings_dirs: tuple[Path, Path]) -> None:
    from kmctl.plugin import okf_source

    _, managed = settings_dirs
    base = _settings(
        managed / "managed-settings.json", {"source": "github", "repo": "base/okf"}
    )
    _settings(
        managed / "managed-settings.d" / ".hidden.json",
        {"source": "github", "repo": "hidden/okf"},
    )

    assert okf_source() == ("base/okf", base), "a dot-file is not read"


@pytest.mark.parametrize(
    "source",
    [
        {"source": "github", "repo": "me/okf", "path": "sub"},
        {"source": "url", "url": "https://x.org/m.json", "headers": {"A": "b"}},
        {"source": "url", "url": "https://x.org/m.json", "headersHelper": "x"},
        {"source": "npm", "package": "okf"},
    ],
)
def test_okf_source_unknown_kind(
    settings_dirs: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    source: dict,
) -> None:
    from kmctl.plugin import PluginError, install

    user, _ = settings_dirs
    file = _settings(user / "settings.json", source)
    calls: list[list[str]] = []
    monkeypatch.setattr("kmctl.plugin._claude", lambda args, cwd: calls.append(args))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))

    with pytest.raises(PluginError) as err:
        install("project", tmp_path)

    assert str(file) in str(err.value)
    assert calls == [], "claude must not run"


def _isolated_home(isolated: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = isolated.parent / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(
        "kmctl.plugin._managed_dir", lambda: isolated.parent / "no-managed"
    )
    return Path(os.environ["CLAUDE_CONFIG_DIR"]) / "settings.json"


@needs_claude
def test_install_with_settings_declared_okf(
    isolated: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(
        _isolated_home(isolated, monkeypatch),
        {"source": "git", "url": "https://github.com/scaccogatto/okf-skills.git"},
    )
    before = settings.read_text()

    result = _kmctl("plugin", "install", "--scope", "project")

    assert result.exit_code == 0, result.output
    assert "okf@scaccogatto" in _listed()
    assert settings.read_text() == before


@needs_claude
def test_install_reports_refused_entry(
    isolated: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = _settings(
        _isolated_home(isolated, monkeypatch),
        {"source": "git", "url": "https://github.com/scaccogatto/okf-skills"},
    )
    before = settings.read_text()

    result = _kmctl("plugin", "install", "--scope", "project")

    assert result.exit_code != 0
    assert str(settings) in result.output
    assert "https://github.com/scaccogatto/okf-skills" in result.output
    assert settings.read_text() == before


@pytest.mark.parametrize(
    "entry",
    [
        {},
        {"source": "github"},
        {"source": {"source": "github"}},
        {"source": {"repo": "x/y"}},
    ],
)
def test_okf_source_ignores_broken_entry(
    settings_dirs: tuple[Path, Path], entry: object
) -> None:
    from kmctl.plugin import OKF_SOURCE, okf_source

    user, managed = settings_dirs
    broken = {"extraKnownMarketplaces": {"scaccogatto": entry}}
    (user / "settings.json").write_text(json.dumps(broken))
    assert okf_source() == (OKF_SOURCE, None), "claude ignores it, so kmctl does too"

    earlier = _settings(
        managed / "managed-settings.json", {"source": "github", "repo": "base/okf"}
    )
    (managed / "managed-settings.d").mkdir()
    (managed / "managed-settings.d" / "10.json").write_text(json.dumps(broken))
    assert okf_source() == ("base/okf", earlier), "a broken later entry hides nothing"
