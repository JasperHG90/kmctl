"""kmctl's session hook (invariant I1) and okf's MCP launcher, which kmctl's package ships.

The hook tests are invariant I1's: the package's one SessionStart hook exits
0 when kmctl is missing or fails (ADR 0004). HOME points at a scratch
folder, so nothing reaches the real one. kmctl plugin patch is tested in
test_plugin_patch.py.
"""

from __future__ import annotations

import json
import re
import subprocess
from importlib.metadata import version
from pathlib import Path

import pytest
from fixtures.fake_tools import FakeTools
from typer.testing import CliRunner, Result

from kmctl import app, plugin

ROOT = Path(__file__).resolve().parents[3]
SKILLS = ROOT / "packages" / "kmctl" / "apm" / ".apm" / "skills"
REF = f"v{version('kmctl')}"
APM = ["--from", "apm-cli==0.33.0", "apm"]
GITHUB = "https://github.com/JasperHG90/kmctl.git"


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
    """kmctl's own hook is one SessionStart entry relaying kmctl briefing (I1), shipped in packages/kmctl/apm/claude/."""
    shipped = json.loads(
        (ROOT / "packages/kmctl/apm/claude/.apm/hooks/hooks.json").read_text()
    )

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


def test_install_hint_names_release(repo: Path, tmp_path: Path) -> None:
    """Both install hints name the release in packages/kmctl/apm/apm.yml, in hooks.json and hook_entry() alike, and the hook still exits 0."""
    manifest = (ROOT / "packages/kmctl/apm/apm.yml").read_text()
    [apm_version] = re.findall(r"(?m)^version: (\S+)$", manifest)
    install = plugin.hook_install(apm_version)
    shipped = json.loads(
        (ROOT / "packages/kmctl/apm/claude/.apm/hooks/hooks.json").read_text()
    )
    [group] = shipped["hooks"]["SessionStart"]
    [hook] = group["hooks"]
    command = plugin.hook_entry()["command"]

    assert hook["command"] == command
    assert command.count(install) == 2
    result = _run_hook(command, tmp_path, "/usr/bin:/bin")
    assert result.returncode == 0
    assert install in result.stdout


def test_read_manifest_and_read_lock_refuse_non_utf8_as_they_do_bad_yaml(
    tmp_path: Path,
) -> None:
    """A non-UTF-8 apm.yml raises PluginError naming it; a non-UTF-8 lock reads as no lock."""
    (tmp_path / "apm.yml").write_bytes(b"\xff\xfe name: x\n")
    (tmp_path / "apm.lock.yaml").write_bytes(b"\xff\xfe dependencies: []\n")

    with pytest.raises(plugin.PluginError, match="apm.yml is not valid UTF-8 YAML"):
        plugin.read_manifest(tmp_path / "apm.yml")
    assert plugin.read_lock(tmp_path, "project") is None


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


@pytest.mark.parametrize(
    ("version", "fragment"),
    [
        ("0.12.1", ""),
        ("0.12.2", ""),
        ("0.12.3rc1", "#subdirectory=packages/kmctl"),
        ("0.13.0", "#subdirectory=packages/kmctl"),
        # A dev build is not a release tag: it is a commit after the move.
        ("0.13.0.dev3+gabc", "#subdirectory=packages/kmctl"),
    ],
)
def test_hook_install_subdirectory_only_after_the_cutoff(
    version: str, fragment: str
) -> None:
    """The hook hint builds from packages/kmctl only for a release after v0.12.2 (ADR 0044)."""
    assert plugin.hook_install(version) == (
        f"git+https://github.com/JasperHG90/kmctl@v{version}{fragment}"
    )


def test_hook_install_is_this_release_s() -> None:
    """HOOK_INSTALL is the hint for this CLI's own version."""
    assert plugin.HOOK_INSTALL == plugin.hook_install(plugin.package_ref()[1:])


# apm-per-package: the package moved to packages/kmctl/apm (ADR 0045) ----------


@pytest.mark.parametrize(
    ("cli", "path"),
    [
        ("0.12.1", "apm"),
        ("0.12.2", "apm"),
        ("0.12.3rc1", "packages/kmctl/apm"),
        ("0.13.0", "packages/kmctl/apm"),
        # A dev build is not a release tag: it is a commit after the move.
        ("0.13.0.dev3+gabc", "packages/kmctl/apm"),
    ],
)
def test_new_entry_names_the_package_folder_of_this_cli_s_release(
    monkeypatch: pytest.MonkeyPatch, cli: str, path: str
) -> None:
    """new_entry writes path packages/kmctl/apm for a CLI after v0.12.2, and apm for one at or before it."""
    monkeypatch.setattr(plugin, "cli_version", lambda: cli)

    assert plugin.new_entry() == {"git": GITHUB, "path": path, "ref": f"v{cli}"}


def _lock(path: str) -> plugin.Lock:
    """A lock holding kmctl's package at ``path``, its two sub-packages under it, and okf."""

    def dep(name: str, virtual: str | None, files: list[str]) -> dict[str, object]:
        return {
            "repo_url": "JasperHG90/kmctl" if virtual else "scaccogatto/okf-skills",
            "name": name,
            "resolved_ref": REF,
            "virtual_path": virtual,
            "deployed_files": files,
            "deployed_file_hashes": {f: "h" for f in files},
        }

    return plugin.Lock.model_validate(
        {
            "dependencies": [
                dep("kmctl", path, [".claude/skills/audit"]),
                dep("kmctl-claude", f"{path}/claude", [".claude/rules/a.md"]),
                dep("kmctl-antigravity", f"{path}/antigravity", [".agents/rules/a.md"]),
                dep("okf", None, [".claude/skills/okf"]),
            ]
        }
    )


@pytest.mark.parametrize("path", ["packages/kmctl/apm", "apm"])
def test_kmctl_package_and_sub_packages_are_found_under_either_path(path: str) -> None:
    """The lock's kmctl entry and its claude and antigravity sub-packages count as kmctl's under either path."""
    lock = _lock(path)

    package = plugin.kmctl_package(lock)
    files = plugin.kmctl_files(lock)

    assert package is not None and package.virtual_path == path
    assert files is not None
    assert files.deployed_files == [
        ".claude/skills/audit",
        ".claude/rules/a.md",
        ".agents/rules/a.md",
    ]


def test_kmctl_files_keeps_another_path_s_sub_packages_out() -> None:
    """Sub-packages under the other path are not folded into the package the lock names."""
    lock = _lock("packages/kmctl/apm")
    for dep in lock.dependencies:
        if dep.virtual_path and dep.virtual_path.endswith("/claude"):
            dep.virtual_path = "apm/claude"

    files = plugin.kmctl_files(lock)

    assert files is not None
    assert ".claude/rules/a.md" not in files.deployed_files


@pytest.mark.parametrize("path", ["packages/kmctl/apm", "apm"])
def test_uninstall_name_ends_with_the_entry_s_path(path: str) -> None:
    """apm uninstall gets HOST/OWNER/REPO/PATH for an entry under either path."""
    entry = {"git": GITHUB, "path": path, "ref": "v0.12.2"}

    assert plugin.uninstall_name(entry) == f"github.com/JasperHG90/kmctl/{path}"
