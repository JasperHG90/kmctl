"""kmctl plugin install and update, with fake uvx, claude and uv on PATH (ADR 0014).

No test here runs the real APM or claude: ``FakeTools`` stands in for them,
records each run, and answers as a test tells it. HOME, CLAUDE_CONFIG_DIR and
XDG_DATA_HOME point at scratch folders, so nothing reaches the real ones. The
hook tests are invariant I1's: kmctl writes one SessionStart hook, and it exits
0 when kmctl is missing or fails (ADR 0004).
"""

from __future__ import annotations

import json
import subprocess
from importlib.metadata import version
from pathlib import Path

import pytest
import yaml
from conftest import plain
from fixtures.fake_tools import Call, FakeTools
from typer.testing import CliRunner, Result

import kmctl
from kmctl import app, plugin

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "apm" / ".apm" / "skills"
REF = f"v{version('kmctl')}"
APM = ["--from", "apm-cli==0.33.0", "apm"]
GITHUB = "https://github.com/JasperHG90/Knowledge-management.git"


def _lock(ref: str = REF, skip: tuple[str, ...] = (), prefix: str = ".claude") -> str:
    """An apm.lock.yaml holding the kmctl package at ``ref``, without the ``skip`` skills."""
    deployed = [f"{prefix}/agents/kmctl-auditor.md"]
    for skill in sorted(p.name for p in SKILLS.iterdir() if p.is_dir()):
        if skill not in skip:
            deployed += [
                f"{prefix}/skills/{skill}",
                f"{prefix}/skills/{skill}/SKILL.md",
            ]
    return yaml.safe_dump(
        {
            "lockfile_version": "1",
            "dependencies": [
                {
                    "repo_url": "JasperHG90/Knowledge-management",
                    "name": "kmctl",
                    "resolved_ref": ref,
                    "virtual_path": "apm",
                    "deployed_files": deployed,
                },
                {"repo_url": "scaccogatto/okf-skills", "name": "okf"},
            ],
        }
    )


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


def _fakes(
    root: Path, monkeypatch: pytest.MonkeyPatch, tools: tuple[str, ...]
) -> FakeTools:
    """Fake ``tools`` on PATH, alone with the system folders."""
    fakes = FakeTools(root, tools=tools)
    monkeypatch.setenv("PATH", fakes.path)
    return fakes


@pytest.fixture
def fakes(tmp_path: Path, home: Path, monkeypatch: pytest.MonkeyPatch) -> FakeTools:
    """Fake uvx and claude on PATH; ``apm install`` writes a lock at this CLI's ref."""
    tools = _fakes(tmp_path, monkeypatch, ("uvx", "claude"))
    tools.on("uvx", "apm install", write={"apm.lock.yaml": _lock()})
    return tools


@pytest.fixture
def bare(tmp_path: Path, home: Path, monkeypatch: pytest.MonkeyPatch) -> FakeTools:
    """Fake uvx and claude on PATH that answer only what a test tells them."""
    return _fakes(tmp_path, monkeypatch, ("uvx", "claude"))


def _kmctl(*args: str) -> Result:
    """Run kmctl in-process with ``args``."""
    return CliRunner().invoke(app, list(args))


def _install(*args: str) -> Result:
    """Run ``kmctl plugin install --harness claude`` with ``args``; fail the test unless it exits 0."""
    result = _kmctl("plugin", "install", "--harness", "claude", *args)
    assert result.exit_code == 0, result.output
    return result


def _settings(root: Path) -> dict:
    """The settings.json under ``root``/.claude, parsed."""
    return json.loads((root / ".claude" / "settings.json").read_text())


def _session_hooks(settings: dict) -> list[dict]:
    """Every SessionStart hook in parsed ``settings``."""
    return [h for g in settings["hooks"]["SessionStart"] for h in g["hooks"]]


def _kmctl_hooks(settings: dict) -> list[dict]:
    """The SessionStart hooks in ``settings`` that run kmctl briefing."""
    return [h for h in _session_hooks(settings) if "kmctl briefing" in h["command"]]


def _apm_calls(fakes: FakeTools, verb: str) -> list[Call]:
    """The fake uvx runs whose APM verb is ``verb``."""
    return [c for c in fakes.calls("uvx") if c.args[3:4] == [verb]]


# r3 and I1: the hook ----------------------------------------------------------


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


def test_hook_without_kmctl_exits_zero_with_hint(
    repo: Path, fakes: FakeTools, tmp_path: Path
) -> None:
    result = _run_hook(_installed_hook_command(repo), tmp_path, "/usr/bin:/bin")

    assert result.returncode == 0
    assert "uv tool install" in result.stdout


def test_hook_exits_zero_when_kmctl_fails(
    repo: Path, fakes: FakeTools, tmp_path: Path
) -> None:
    command = _installed_hook_command(repo)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "kmctl"
    fake.write_text("#!/bin/sh\nexit 3\n")
    fake.chmod(0o755)

    result = _run_hook(command, tmp_path, f"{bin_dir}:/usr/bin:/bin")

    assert result.returncode == 0
    assert "kmctl briefing failed" in result.stdout


def test_hook_refuses_settings_that_are_not_json(repo: Path, fakes: FakeTools) -> None:
    (repo / ".claude").mkdir()
    (repo / ".claude" / "settings.json").write_text("{not json")

    result = _kmctl("plugin", "install", "--harness", "claude")

    assert result.exit_code == 1
    assert "settings.json is not valid JSON" in result.stderr
    assert (repo / ".claude" / "settings.json").read_text() == "{not json"


# r4: apm.yml, the APM command, the next step ------------------------------------


def test_install_writes_apm_entry_and_targets(repo: Path, fakes: FakeTools) -> None:
    _install()

    manifest = yaml.safe_load((repo / "apm.yml").read_text())
    assert manifest["targets"] == ["claude"]
    assert manifest["dependencies"]["apm"] == [
        {"git": GITHUB, "path": "apm", "ref": REF}
    ]
    assert manifest["name"] == "repo"
    assert manifest["version"]


def test_install_keeps_other_apm_entries(repo: Path, fakes: FakeTools) -> None:
    (repo / "apm.yml").write_text(
        "# my packages\nname: mine\nversion: 1.2.3\ntargets: [copilot]\n"
        "dependencies:\n  apm:\n    - acme/rules#abc  # pinned\n"
        f"    - git: {GITHUB}\n      path: apm\n      ref: v0.0.1\n"
        "  mcp:\n    - io.github/server\n"
    )

    _install()

    text = (repo / "apm.yml").read_text()
    manifest = yaml.safe_load(text)
    assert "# my packages" in text and "# pinned" in text
    assert manifest["name"] == "mine" and manifest["version"] == "1.2.3"
    assert manifest["targets"] == ["copilot", "claude"]
    assert manifest["dependencies"]["apm"] == [
        "acme/rules#abc",
        {"git": GITHUB, "path": "apm", "ref": REF},
    ]
    assert manifest["dependencies"]["mcp"] == ["io.github/server"]


def test_install_runs_pinned_apm_command(repo: Path, fakes: FakeTools) -> None:
    _install()

    [call] = _apm_calls(fakes, "install")
    assert call.args == [*APM, "install", "--target", "claude"]
    assert Path(call.cwd) == repo
    assert f"ref: {REF}" in (call.apm_yml or "")


def test_install_source_option_names_the_git_url(repo: Path, fakes: FakeTools) -> None:
    _install("--source", "http://127.0.0.1:9/o/kmctl.git")

    [entry] = yaml.safe_load((repo / "apm.yml").read_text())["dependencies"]["apm"]
    assert entry == {
        "git": "http://127.0.0.1:9/o/kmctl.git",
        "path": "apm",
        "ref": REF,
        "allow_insecure": True,
    }
    [call] = _apm_calls(fakes, "install")
    assert call.args == [*APM, "install", "--target", "claude", "--allow-insecure"]


def test_install_ends_with_next_line(repo: Path, fakes: FakeTools) -> None:
    last = _install().stdout.strip().splitlines()[-1]

    assert last.startswith("Next: ")
    assert last.endswith(", then kmctl doctor")


def test_install_json_prints_what_it_installed_and_notes(
    repo: Path, fakes: FakeTools
) -> None:
    data = json.loads(_install("--json").stdout)

    assert data["scope"] == "project"
    assert data["harnesses"] == ["claude"]
    assert data["package_ref"] == REF
    assert isinstance(data["notes"], list)


def test_install_prints_the_installed_ref(repo: Path, fakes: FakeTools) -> None:
    out = _install().stdout

    assert f"installed kmctl's package {REF} for claude (project scope)" in out


@pytest.mark.parametrize("harness", ["codex", "claude,codex", ""])
def test_install_refuses_unknown_harness(
    repo: Path, fakes: FakeTools, harness: str
) -> None:
    result = _kmctl("plugin", "install", "--harness", harness)

    assert result.exit_code == 1
    assert "one of: claude" in result.stderr
    assert fakes.calls() == []
    assert not (repo / "apm.yml").exists()


def test_install_update_runs_the_same_steps(repo: Path, fakes: FakeTools) -> None:
    result = _kmctl("plugin", "update", "--harness", "claude")

    assert result.exit_code == 0, result.output
    [call] = _apm_calls(fakes, "install")
    assert call.args == [*APM, "install", "--target", "claude"]


@pytest.mark.parametrize("verb", ["install", "update"])
def test_install_help_names_every_option(verb: str) -> None:
    result = CliRunner().invoke(
        app, ["plugin", verb, "--help"], env={"COLUMNS": "80"}, terminal_width=80
    )
    text = " ".join(plain(result.stdout).split())

    for option in ("--harness", "--scope", "--source", "--force", "--json"):
        assert option in text
    assert "github.com/JasperHG90/Knowledge-management" in text


# r5: skipped files, --force, an APM failure --------------------------------------


def test_install_skip_fails_naming_paths_and_force(repo: Path, bare: FakeTools) -> None:
    bare.on(
        "uvx",
        "apm install",
        stdout="[!] 1 file skipped -- local files exist, not managed by APM\n"
        "Use 'apm install --force' to overwrite\n",
        write={"apm.lock.yaml": _lock(skip=("audit",))},
    )

    result = _kmctl("plugin", "install", "--harness", "claude")

    assert result.exit_code == 1
    assert ".claude/skills/audit" in result.stderr
    assert ".claude/skills/handoff" not in result.stderr
    assert "kmctl plugin install --harness claude --force" in result.stderr
    assert not (repo / ".claude" / "settings.json").exists()


def test_install_force_passes_force_to_apm(repo: Path, fakes: FakeTools) -> None:
    _install("--force")

    [call] = _apm_calls(fakes, "install")
    assert call.args == [*APM, "install", "--target", "claude", "--force"]


def test_install_when_apm_fails_names_cause(repo: Path, bare: FakeTools) -> None:
    bare.on(
        "uvx",
        "apm install",
        stdout="[>] Resolving kmctl-apm...\n",
        stderr="[x] Failed to resolve kmctl: fatal: repository not found\n"
        "[*] Installed 0 APM dependencies.\n",
        exit=1,
    )

    result = _kmctl("plugin", "install", "--harness", "claude")

    assert result.exit_code == 1
    assert "[x] Failed to resolve kmctl: fatal: repository not found" in result.stderr
    assert "apm install --target claude failed" in result.stderr
    assert not (repo / ".claude" / "settings.json").exists()


def test_install_without_uvx_names_the_fix(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _fakes(tmp_path, monkeypatch, ("claude",))

    result = _kmctl("plugin", "install", "--harness", "claude")

    assert result.exit_code == 1
    assert "uvx is not on PATH" in result.stderr


# r6: old installs ---------------------------------------------------------------


def _plugin_list(*entries: dict) -> str:
    """``claude plugin list --json`` output holding ``entries``."""
    return json.dumps(list(entries))


def test_old_plugin_removed_at_its_scope_in_order(repo: Path, fakes: FakeTools) -> None:
    fakes.on(
        "claude",
        "plugin list --json",
        stdout=_plugin_list(
            {"id": "kmctl@kmctl", "scope": "project", "projectPath": str(repo)},
            {"id": "okf@scaccogatto", "scope": "project", "projectPath": str(repo)},
        ),
    )

    result = _install()

    calls = fakes.calls()
    claude = [c for c in calls if c.tool == "claude"]
    assert [c.args for c in claude] == [
        ["plugin", "list", "--json"],
        ["plugin", "uninstall", "kmctl@kmctl", "--scope", "project"],
        ["plugin", "prune", "--scope", "project", "--yes"],
        ["plugin", "marketplace", "remove", "kmctl", "--scope", "project"],
    ]
    [install] = _apm_calls(fakes, "install")
    assert all(calls.index(c) > calls.index(install) for c in claude)
    assert "removed the old claude plugin kmctl@kmctl (project scope)" in result.stdout


@pytest.mark.parametrize("broken", ["apm_fails", "no_uvx", "bad_settings"])
def test_old_plugin_kept_when_the_install_fails(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, broken: str
) -> None:
    """A failed install removes nothing: the old plugin keeps working."""
    tools = _fakes(
        tmp_path, monkeypatch, ("claude",) if broken == "no_uvx" else ("uvx", "claude")
    )
    tools.on(
        "claude",
        "plugin list --json",
        stdout=_plugin_list(
            {"id": "kmctl@kmctl", "scope": "project", "projectPath": str(repo)}
        ),
    )
    if broken == "apm_fails":
        tools.on("uvx", "apm install", stderr="[x] auth failed\n", exit=1)
    if broken == "bad_settings":
        (repo / ".claude").mkdir()
        (repo / ".claude" / "settings.json").write_text("[")

    result = _kmctl("plugin", "install", "--harness", "claude")

    assert result.exit_code == 1
    assert tools.calls("claude") == []
    if broken != "apm_fails":
        assert tools.calls() == []
        assert not (repo / "apm.yml").exists()


def test_old_plugin_of_another_repository_left_alone(
    repo: Path, fakes: FakeTools, tmp_path: Path
) -> None:
    fakes.on(
        "claude",
        "plugin list --json",
        stdout=_plugin_list(
            {"id": "kmctl@kmctl", "scope": "project", "projectPath": str(tmp_path)},
            {"id": "kmctl@kmctl", "scope": "user"},
        ),
    )

    _install()

    assert [c.args for c in fakes.calls("claude")] == [["plugin", "list", "--json"]]


def test_old_plugin_at_user_scope_removed_by_a_user_scope_install(
    repo: Path, fakes: FakeTools
) -> None:
    fakes.on(
        "claude",
        "plugin list --json",
        stdout=_plugin_list({"id": "kmctl@kmctl", "scope": "user"}),
    )
    fakes.on("uvx", "apm install", write={".apm/apm.lock.yaml": _lock()})

    _install("--scope", "user")

    claude = [c.args for c in fakes.calls("claude") if c.args[0] == "plugin"]
    assert claude[1:] == [
        ["plugin", "uninstall", "kmctl@kmctl", "--scope", "user"],
        ["plugin", "prune", "--scope", "user", "--yes"],
        ["plugin", "marketplace", "remove", "kmctl", "--scope", "user"],
    ]


def test_old_plugin_marketplace_already_gone_is_not_a_failure(
    repo: Path, fakes: FakeTools
) -> None:
    """claude 2.1.301 exits 1 with "not found" when the marketplace is gone: done already."""
    fakes.on(
        "claude",
        "plugin list --json",
        stdout=_plugin_list(
            {"id": "kmctl@kmctl", "scope": "project", "projectPath": str(repo)}
        ),
    )
    fakes.on(
        "claude",
        "plugin marketplace remove",
        stderr="✘ Failed to remove marketplace: Marketplace 'kmctl' not found\n",
        exit=1,
    )

    result = _install()

    assert "removed the old claude plugin kmctl@kmctl (project scope)" in result.stdout


def test_old_plugin_uninstall_failure_stops_the_install(
    repo: Path, fakes: FakeTools
) -> None:
    fakes.on(
        "claude",
        "plugin list --json",
        stdout=_plugin_list(
            {"id": "kmctl@kmctl", "scope": "project", "projectPath": str(repo)}
        ),
    )
    fakes.on("claude", "plugin uninstall", stderr="error: busy\n", exit=1)

    result = _kmctl("plugin", "install", "--harness", "claude")

    assert result.exit_code == 1
    assert (
        "claude plugin uninstall kmctl@kmctl --scope project failed: error: busy"
        in result.stderr
    )
    assert not (repo / ".claude" / "settings.json").exists()


def test_old_plugin_skipped_without_claude(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tools = _fakes(tmp_path, monkeypatch, ("uvx",))
    tools.on("uvx", "apm install", write={"apm.lock.yaml": _lock()})

    result = _install()

    assert "claude CLI is not on PATH" in result.stdout
    assert "kmctl@kmctl" in result.stdout
    assert len(_apm_calls(tools, "install")) == 1


@pytest.mark.parametrize(
    "old",
    [
        "    - JasperHG90/Knowledge-management/apm#v0.3.0\n",
        (
            "    - git: https://github.com/JasperHG90/Knowledge-management\n"
            "      path: apm\n      ref: v0.3.0\n"
        ),
    ],
)
def test_old_apm_entry_uninstalled_before_rewrite(
    repo: Path, fakes: FakeTools, old: str
) -> None:
    kept = "name: mine\nversion: 1.0.0\ndependencies:\n  apm:\n    - acme/rules#abc\n"
    (repo / "apm.yml").write_text(kept + old)
    (repo / "apm.lock.yaml").write_text(_old_layout_lock())
    fakes.on("uvx", "apm uninstall", write={"apm.yml": kept})

    result = _install()

    [uninstall] = _apm_calls(fakes, "uninstall")
    assert uninstall.args == [*APM, "uninstall", "JasperHG90/Knowledge-management/apm"]
    assert Path(uninstall.cwd) == repo
    assert old in (uninstall.apm_yml or "")
    [install] = _apm_calls(fakes, "install")
    assert fakes.calls().index(uninstall) < fakes.calls().index(install)
    assert "removed the old APM entry" in result.stdout
    deps = yaml.safe_load((repo / "apm.yml").read_text())["dependencies"]["apm"]
    assert deps == ["acme/rules#abc", {"git": GITHUB, "path": "apm", "ref": REF}]


def test_old_apm_entry_left_by_uninstall_is_refused(
    repo: Path, fakes: FakeTools
) -> None:
    """When apm uninstall leaves the old entry, kmctl refuses instead of adding a second."""
    (repo / "apm.yml").write_text(
        "name: mine\nversion: 1.0.0\ndependencies:\n  apm:\n"
        "    - git: https://github.com/JasperHG90/Knowledge-management\n"
        "      path: apm\n"
    )
    (repo / "apm.lock.yaml").write_text(_old_layout_lock())

    result = _kmctl("plugin", "install", "--harness", "claude")

    assert result.exit_code == 1
    assert "left the entry" in result.stderr
    assert "apm uninstall" in result.stderr
    assert _apm_calls(fakes, "install") == []


def test_old_apm_kmctl_entry_is_not_uninstalled(repo: Path, fakes: FakeTools) -> None:
    (repo / "apm.yml").write_text(
        "name: mine\nversion: 1.0.0\ndependencies:\n  apm:\n"
        f"    - git: {GITHUB}\n      path: apm\n      ref: v0.0.1\n"
    )

    _install()

    assert _apm_calls(fakes, "uninstall") == []


# f2: a kmctl entry from another --source ------------------------------------------

LOCAL = "http://127.0.0.1:46239/o/kmctl.git"


def _old_layout_lock() -> str:
    """An apm.lock.yaml as APM 0.33.0 writes it for kmctl v0.3.0, whose hook came from plugin/."""
    return yaml.safe_dump(
        {
            "lockfile_version": "1",
            "dependencies": [
                {
                    "repo_url": "JasperHG90/Knowledge-management",
                    "name": "kmctl",
                    "virtual_path": "apm",
                    "resolved_ref": "v0.3.0",
                },
                {
                    "repo_url": "JasperHG90/Knowledge-management",
                    "name": "kmctl",
                    "virtual_path": "plugin",
                    "resolved_ref": "v0.3.0",
                },
            ],
        }
    )


def _lock_at(git: str, name: str = "kmctl") -> str:
    """An apm.lock.yaml in APM 0.33.0's shape for a package at ``git`` with ``path: apm``.

    APM splits a git source over host, port and repo_url (spikes
    apm-only-install/4 to /6): http://127.0.0.1:N/o/kmctl.git becomes
    repo_url o/kmctl, host 127.0.0.1, port N.
    """
    if git == GITHUB:
        place = {"repo_url": "JasperHG90/Knowledge-management"}
    else:
        place = {"repo_url": "o/kmctl", "host": "127.0.0.1", "port": 46239}
    return yaml.safe_dump(
        {
            "lockfile_version": "1",
            "dependencies": [
                {**place, "name": name, "virtual_path": "apm", "resolved_ref": REF}
            ],
        }
    )


@pytest.mark.parametrize(("first", "then"), [(LOCAL, GITHUB), (GITHUB, LOCAL)])
def test_other_source_entry_replaced_in_place(
    repo: Path, fakes: FakeTools, first: str, then: str
) -> None:
    """A kmctl entry from another --source is replaced in its place, with a note."""
    (repo / "apm.yml").write_text(
        "name: mine\nversion: 1.0.0\ndependencies:\n  apm:\n"
        f"    - git: {first}\n      path: apm\n      ref: v0.0.1\n"
        "    - acme/rules#abc\n"
    )
    (repo / "apm.lock.yaml").write_text(_lock_at(first))
    args = () if then == GITHUB else ("--source", then)

    result = _install(*args)

    deps = yaml.safe_load((repo / "apm.yml").read_text())["dependencies"]["apm"]
    assert deps[1:] == ["acme/rules#abc"]
    assert deps[0]["git"] == then and deps[0]["path"] == "apm"
    assert f"replaced the kmctl entry from {first}" in result.stdout
    assert _apm_calls(fakes, "uninstall") == []


def test_unrelated_apm_path_package_kept(repo: Path, fakes: FakeTools) -> None:
    """A path: apm package the lock names something else is not kmctl's."""
    other = "https://example.com/acme/tools.git"
    (repo / "apm.yml").write_text(
        "name: mine\nversion: 1.0.0\ndependencies:\n  apm:\n"
        f"    - git: {other}\n      path: apm\n"
    )
    (repo / "apm.lock.yaml").write_text(
        yaml.safe_dump(
            {
                "lockfile_version": "1",
                "dependencies": [
                    {
                        "repo_url": "acme/tools",
                        "host": "example.com",
                        "name": "tools",
                        "virtual_path": "apm",
                    }
                ],
            }
        )
    )

    _install()

    deps = yaml.safe_load((repo / "apm.yml").read_text())["dependencies"]["apm"]
    assert deps[0] == {"git": other, "path": "apm"}
    assert deps[1]["git"] == GITHUB


def test_old_apm_uninstall_failure_names_cause(repo: Path, fakes: FakeTools) -> None:
    (repo / "apm.yml").write_text(
        "name: mine\nversion: 1.0.0\ndependencies:\n  apm:\n"
        "    - JasperHG90/Knowledge-management/apm#v0.3.0\n"
    )
    fakes.on("uvx", "apm uninstall", stderr="[x] Ambiguous dependency\n", exit=1)

    result = _kmctl("plugin", "install", "--harness", "claude")

    assert result.exit_code == 1
    assert "[x] Ambiguous dependency" in result.stderr
    assert _apm_calls(fakes, "install") == []


# r6b: okf's MCP server ----------------------------------------------------------


def _mcp(root: Path) -> dict:
    """The mcpServers of ``root``/.mcp.json."""
    return json.loads((root / ".mcp.json").read_text())["mcpServers"]


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


# r7: user scope -----------------------------------------------------------------


def test_user_scope_runs_apm_global_and_writes_user_settings(
    repo: Path, fakes: FakeTools, home: Path
) -> None:
    fakes.on("uvx", "apm install", write={".apm/apm.lock.yaml": _lock()})

    _install("--scope", "user")

    [call] = _apm_calls(fakes, "install")
    assert call.args == [*APM, "install", "--target", "claude", "-g"]
    assert Path(call.cwd) == home
    manifest = yaml.safe_load((home / ".apm" / "apm.yml").read_text())
    assert manifest["dependencies"]["apm"] == [
        {"git": GITHUB, "path": "apm", "ref": REF}
    ]
    assert not (repo / ".claude").exists()
    assert not (repo / "apm.yml").exists()


def test_user_scope_is_not_the_default(
    repo: Path, fakes: FakeTools, home: Path
) -> None:
    _install()

    assert "-g" not in _apm_calls(fakes, "install")[0].args
    assert not (home / ".claude" / "settings.json").exists()
    assert not (home / ".apm").exists()


# apm-hands-back r4: what an older kmctl wrote is taken out before APM runs -------


OLD_GROUP = {"hooks": [plugin.hook_entry()]}
APM_GROUP = {"matcher": "*", "hooks": [plugin.hook_entry()]}


def _record(settings: Path, *groups: dict) -> None:
    """Write APM's apm-hooks.json beside ``settings``, recording ``groups``."""
    (settings.parent / "apm-hooks.json").write_text(
        json.dumps(
            {"SessionStart": [{**g, "_apm_source": "kmctl/claude"} for g in groups]}
        )
    )


@pytest.mark.parametrize("scope", ["project", "user"])
def test_migrate_drops_the_unrecorded_kmctl_group(
    repo: Path, fakes: FakeTools, home: Path, scope: str
) -> None:
    root = home if scope == "user" else repo
    settings = root / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True, exist_ok=True)
    other = {"hooks": [{"type": "command", "command": "echo mine"}]}
    settings.write_text(
        json.dumps(
            {"theme": "dark", "hooks": {"SessionStart": [OLD_GROUP, APM_GROUP, other]}}
        )
    )
    _record(settings, APM_GROUP)
    if scope == "user":
        fakes.on("uvx", "apm install", write={".apm/apm.lock.yaml": _lock()})

    _install(*(["--scope", "user"] if scope == "user" else []))

    data = json.loads(settings.read_text())
    assert data["theme"] == "dark"
    assert data["hooks"]["SessionStart"] == [APM_GROUP, other]


def test_migrate_keeps_other_hooks_in_a_shared_group(
    repo: Path, fakes: FakeTools
) -> None:
    mine = {"type": "command", "command": "echo mine"}
    settings = repo / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)
    shared = {"matcher": "x", "hooks": [mine, plugin.hook_entry()]}
    settings.write_text(json.dumps({"hooks": {"SessionStart": [shared]}}))

    _install()

    assert json.loads(settings.read_text()) == {
        "hooks": {"SessionStart": [{"matcher": "x", "hooks": [mine]}]}
    }


def test_migrate_with_nothing_recorded_drops_every_kmctl_group(
    repo: Path, fakes: FakeTools
) -> None:
    settings = repo / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({"hooks": {"SessionStart": [OLD_GROUP]}, "x": 1}))

    _install()

    assert json.loads(settings.read_text()) == {"x": 1}


def test_migrate_drops_a_stale_okf_bundle_keeping_the_rest(
    repo: Path, fakes: FakeTools
) -> None:
    stale = {
        "command": "sh",
        "args": ["-c", "exec uv run https://example.invalid/old.py"],
    }
    current = plugin.okf_mcp_server()
    mine = {"command": "my-server"}
    (repo / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"okf-bundle": stale, "mine": mine}})
    )

    _install()

    assert json.loads((repo / ".mcp.json").read_text()) == {
        "mcpServers": {"mine": mine}
    }
    (repo / ".mcp.json").write_text(json.dumps({"mcpServers": {"okf-bundle": current}}))
    _install()
    assert json.loads((repo / ".mcp.json").read_text()) == {
        "mcpServers": {"okf-bundle": current}
    }


def test_migrate_user_scope_removes_a_stale_okf_bundle_with_claude(
    repo: Path, fakes: FakeTools, home: Path
) -> None:
    fakes.on("uvx", "apm install", write={".apm/apm.lock.yaml": _lock()})
    stale = {"command": "sh", "args": ["-c", "old"]}
    (home / ".claude" / ".claude.json").write_text(
        json.dumps({"mcpServers": {"okf-bundle": stale}})
    )

    _install("--scope", "user")

    removes = [c.args for c in fakes.calls("claude") if c.args[:2] == ["mcp", "remove"]]
    assert removes == [["mcp", "remove", "okf-bundle", "--scope", "user"]]


def test_migrate_user_scope_keeps_a_current_okf_bundle(
    repo: Path, fakes: FakeTools, home: Path
) -> None:
    fakes.on("uvx", "apm install", write={".apm/apm.lock.yaml": _lock()})
    current = {**plugin.okf_mcp_server(), "type": "stdio"}
    (home / ".claude" / ".claude.json").write_text(
        json.dumps({"mcpServers": {"okf-bundle": current}})
    )

    _install("--scope", "user")

    assert not [c for c in fakes.calls("claude") if c.args[:2] == ["mcp", "remove"]]


# harness-prompt: the question when --harness is missing ---------------------------


QUESTION = "Which harnesses should kmctl install for?"


@pytest.fixture
def terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make kmctl see a terminal on stdin, as a person running it by hand would."""
    monkeypatch.setattr(kmctl, "_at_terminal", lambda: True)


@pytest.fixture
def installs(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Record the harnesses each install is asked for, instead of installing."""
    seen: list[list[str]] = []

    def fake_install(cwd: Path, harnesses: list[str], scope: str, **_: object):
        seen.append(harnesses)
        return plugin.InstallResult(scope, harnesses, None, [])

    monkeypatch.setattr(kmctl, "install_plugin", fake_install)
    return seen


def _ask(verb: str, answer: str, *args: str) -> Result:
    """Run ``kmctl plugin VERB`` without --harness, typing ``answer``."""
    return CliRunner().invoke(app, ["plugin", verb, *args], input=answer)


@pytest.mark.usefixtures("terminal")
def test_prompt_installs_the_named_harnesses(repo: Path, fakes: FakeTools) -> None:
    result = _ask("install", "1\n")

    assert result.exit_code == 0, result.output
    assert QUESTION in result.stderr
    assert "1. claude" in result.stderr and "2. antigravity" in result.stderr
    assert QUESTION not in result.stdout and "1. claude" not in result.stdout
    [call] = _apm_calls(fakes, "install")
    assert call.args == [*APM, "install", "--target", "claude"]


@pytest.mark.usefixtures("repo", "terminal")
@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        ("1,2", ["claude", "antigravity"]),
        ("antigravity", ["antigravity"]),
        ("2, claude", ["antigravity", "claude"]),
        ("", ["claude"]),
    ],
)
def test_prompt_reads_numbers_and_names(
    installs: list[list[str]], answer: str, expected: list[str]
) -> None:
    result = _ask("install", answer + "\n")

    assert result.exit_code == 0, result.output
    assert installs == [expected]


@pytest.mark.usefixtures("repo", "terminal")
def test_prompt_asks_again_after_a_bad_answer(installs: list[list[str]]) -> None:
    result = _ask("install", "3\nopencode\n2\n")

    assert result.exit_code == 0, result.output
    assert installs == [["antigravity"]]
    assert result.stderr.count(QUESTION) == 1
    assert result.stderr.count("one of: 1 claude, 2 antigravity") == 2


@pytest.mark.usefixtures("terminal")
@pytest.mark.parametrize(
    ("targets", "expected"),
    [
        ([], ["claude"]),
        (["antigravity"], ["antigravity"]),
        (["claude", "antigravity"], ["claude", "antigravity"]),
    ],
)
def test_prompt_update_default_is_what_is_installed(
    repo: Path, installs: list[list[str]], targets: list[str], expected: list[str]
) -> None:
    if targets:
        entry = {"git": plugin.DEFAULT_SOURCE, "path": "apm", "ref": REF}
        manifest = {"dependencies": {"apm": [entry]}, "targets": targets}
        (repo / "apm.yml").write_text(yaml.safe_dump(manifest))

    result = _ask("update", "\n")

    assert result.exit_code == 0, result.output
    assert QUESTION in result.stderr
    assert f"[{','.join(expected)}]" in result.stderr
    assert installs == [expected]


@pytest.mark.parametrize("verb", ["install", "update"])
def test_no_terminal_without_harness_refuses(
    repo: Path, fakes: FakeTools, verb: str
) -> None:
    result = _ask(verb, "1\n")

    assert result.exit_code == 1
    assert QUESTION not in result.output
    assert "--harness" in result.stderr
    assert "claude, antigravity" in result.stderr
    assert fakes.calls() == []


@pytest.mark.usefixtures("terminal")
@pytest.mark.parametrize("verb", ["install", "update"])
def test_json_no_harness_refuses_at_a_terminal(
    repo: Path, fakes: FakeTools, verb: str
) -> None:
    result = _ask(verb, "1\n", "--json")

    assert result.exit_code == 1
    assert QUESTION not in result.output
    assert "--harness" in result.stderr
    assert fakes.calls() == []


@pytest.mark.usefixtures("repo", "terminal")
@pytest.mark.parametrize("verb", ["install", "update"])
def test_harness_given_never_prompts(installs: list[list[str]], verb: str) -> None:
    result = _ask(verb, "2\n", "--harness", "claude")

    assert result.exit_code == 0, result.output
    assert QUESTION not in result.output
    assert installs == [["claude"]]


@pytest.mark.parametrize("verb", ["install", "update"])
def test_harness_docs_help_says_it_asks(verb: str) -> None:
    result = CliRunner().invoke(
        app, ["plugin", verb, "--help"], env={"COLUMNS": "80"}, terminal_width=80
    )
    text = " ".join(plain(result.stdout).replace("│", " ").split())

    assert "Default: claude" not in text
    assert "asks which harnesses" in text
    assert "refuses" in text
    if verb == "update":
        assert "already installed" in text


def test_harness_docs_pages_say_it_asks() -> None:
    root = Path(__file__).parents[1]
    pages = [
        "docs/reference/commands.md",
        "docs/how-to/install-the-plugin-and-the-ci-action.md",
        "docs/how-to/install-kmctl-with-apm.md",
    ]
    for page in pages:
        text = " ".join((root / page).read_text().split())
        assert "asks which harnesses" in text, page
    reference = " ".join((root / pages[0]).read_text().split())
    assert "already installed" in reference
    assert "Default: claude" not in reference


@pytest.mark.usefixtures("repo", "terminal")
@pytest.mark.parametrize("answer", ["²", "①"])
def test_prompt_non_decimal_digit_is_asked_again(
    installs: list[list[str]], answer: str
) -> None:
    result = _ask("install", f"{answer}\n1\n")

    assert result.exit_code == 0, result.output
    assert result.exception is None
    assert installs == [["claude"]]
    assert "one of: 1 claude, 2 antigravity" in result.stderr
