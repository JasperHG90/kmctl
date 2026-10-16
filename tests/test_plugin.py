"""kmctl plugin install, update and status, with fake uvx, claude and uv on PATH (ADR 0014).

No test here runs the real APM or claude: ``FakeTools`` stands in for them,
records each run, and answers as a test tells it. HOME, CLAUDE_CONFIG_DIR and
XDG_DATA_HOME point at scratch folders, so nothing reaches the real ones. The
hook tests are invariant I1's: kmctl writes one SessionStart hook, and it exits
0 when kmctl is missing or fails (ADR 0004).
"""

from __future__ import annotations

import json
import re
import subprocess
from importlib.metadata import version
from pathlib import Path

import pytest
import yaml
from conftest import plain
from fixtures.fake_tools import Call, FakeTools
from typer.testing import CliRunner, Result

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


def test_install_writes_one_sessionstart_hook(repo: Path, fakes: FakeTools) -> None:
    """kmctl's only hook is one SessionStart entry relaying kmctl briefing (I1)."""
    _install()

    settings = _settings(repo)
    assert list(settings["hooks"]) == ["SessionStart"]
    [hook] = _session_hooks(settings)
    assert hook == {
        "type": "command",
        "description": plugin.HOOK_DESCRIPTION,
        "command": plugin.HOOK_COMMAND,
        "timeout": 10,
    }


def _installed_hook_command(repo: Path) -> str:
    """The command of the hook ``kmctl plugin install`` writes."""
    _install()
    [hook] = _kmctl_hooks(_settings(repo))
    return hook["command"]


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


def test_hook_merge_keeps_other_keys_and_hooks(repo: Path, fakes: FakeTools) -> None:
    other_start = {"hooks": [{"type": "command", "command": "echo hi"}]}
    stop = [{"hooks": [{"type": "command", "command": "okf-stop-check.sh"}]}]
    before = {
        "permissions": {"allow": ["Bash(ls)"]},
        "enabledPlugins": {"x@y": True},
        "hooks": {"SessionStart": [other_start], "Stop": stop},
    }
    (repo / ".claude").mkdir()
    (repo / ".claude" / "settings.json").write_text(json.dumps(before))

    _install()

    after = _settings(repo)
    assert after["permissions"] == before["permissions"]
    assert after["enabledPlugins"] == before["enabledPlugins"]
    assert after["hooks"]["Stop"] == stop
    assert after["hooks"]["SessionStart"][0] == other_start
    assert _kmctl_hooks(after) == [plugin.hook_entry()]


def test_hook_second_install_leaves_one_entry(repo: Path, fakes: FakeTools) -> None:
    _install()
    first = _settings(repo)

    _install()

    assert _settings(repo) == first
    assert len(_kmctl_hooks(first)) == 1


def test_hook_old_entry_replaced_in_place(repo: Path, fakes: FakeTools) -> None:
    old = {"type": "command", "command": "kmctl briefing", "timeout": 5}
    groups = [
        {"hooks": [{"type": "command", "command": "echo first"}]},
        {"matcher": "startup", "hooks": [old]},
        {"hooks": [{"type": "command", "command": "echo last"}]},
        {"hooks": [dict(old, command="old kmctl briefing again")]},
    ]
    (repo / ".claude").mkdir()
    (repo / ".claude" / "settings.json").write_text(
        json.dumps({"hooks": {"SessionStart": groups}})
    )

    _install()

    after = _settings(repo)["hooks"]["SessionStart"]
    assert after == [
        groups[0],
        {"matcher": "startup", "hooks": [plugin.hook_entry()]},
        groups[2],
    ]


def test_hook_missing_settings_file_created(repo: Path, fakes: FakeTools) -> None:
    assert not (repo / ".claude").exists()

    _install()

    assert _kmctl_hooks(_settings(repo)) == [plugin.hook_entry()]


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
    assert "kmctl plugin status" in last


def test_install_json_prints_status_and_notes(repo: Path, fakes: FakeTools) -> None:
    data = json.loads(_install("--json").stdout)

    assert data["package_ref"] == REF
    assert data["hook"] is True
    assert data["problems"] == []
    assert isinstance(data["notes"], list)


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
    result = _kmctl("plugin", "update")

    assert result.exit_code == 0, result.output
    [call] = _apm_calls(fakes, "install")
    assert call.args == [*APM, "install", "--target", "claude"]
    assert len(_kmctl_hooks(_settings(repo))) == 1


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
    assert len(_kmctl_hooks(_settings(repo))) == 1


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


def test_mcp_merged_keeping_other_servers(repo: Path, fakes: FakeTools) -> None:
    other = {"command": "npx", "args": ["some-server"]}
    (repo / ".mcp.json").write_text(json.dumps({"mcpServers": {"mine": other}}))

    result = _install()

    servers = _mcp(repo)
    assert servers["mine"] == other
    assert servers["okf-bundle"] == {
        "type": "stdio",
        "command": "sh",
        "args": ["-c", plugin.okf_mcp_launcher()],
    }
    assert "approve" in result.stdout


def test_mcp_one_entry_after_two_installs(repo: Path, fakes: FakeTools) -> None:
    _install()
    _install()

    assert list(_mcp(repo)) == ["okf-bundle"]


def test_mcp_sha_equals_apm_pin() -> None:
    [okf] = yaml.safe_load((ROOT / "apm" / "apm.yml").read_text())["dependencies"][
        "apm"
    ]
    pin = okf.partition("#")[2]

    assert plugin.OKF_COMMIT == pin
    assert plugin.okf_mcp_url() == (
        f"https://raw.githubusercontent.com/scaccogatto/okf-skills/{pin}"
        "/servers/okf_mcp.py"
    )
    assert plugin.okf_mcp_url() in plugin.okf_mcp_launcher()


def test_mcp_changed_pin_replaces_entry(
    repo: Path, fakes: FakeTools, monkeypatch: pytest.MonkeyPatch
) -> None:
    old = plugin.OKF_COMMIT
    _install()
    monkeypatch.setattr(plugin, "OKF_COMMIT", "f" * 40)

    _install()

    [launcher] = _mcp(repo)["okf-bundle"]["args"][1:]
    assert f"/okf-skills/{'f' * 40}/servers/okf_mcp.py" in launcher
    assert old not in launcher


@pytest.mark.parametrize("args", [["okf_mcp.py"], ["run", "x/servers/okf_mcp.py"]])
def test_mcp_existing_okf_server_kept(
    repo: Path, fakes: FakeTools, args: list[str]
) -> None:
    bundle = {"command": "uv", "args": args}
    (repo / ".mcp.json").write_text(
        json.dumps(
            {"mcpServers": {"bundle": bundle, "okf-bundle": plugin.okf_mcp_server()}}
        )
    )

    result = _install()

    assert _mcp(repo) == {"bundle": bundle}
    assert "kept the okf MCP server 'bundle'" in result.stdout


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


def test_mcp_user_scope_uses_claude_mcp_add_json(repo: Path, fakes: FakeTools) -> None:
    fakes.on("uvx", "apm install", write={".apm/apm.lock.yaml": _lock()})

    _install("--scope", "user")

    adds = [c.args for c in fakes.calls("claude") if c.args[:2] == ["mcp", "add-json"]]
    assert adds == [
        [
            "mcp",
            "add-json",
            "okf-bundle",
            json.dumps(plugin.okf_mcp_server()),
            "--scope",
            "user",
        ]
    ]
    assert not (repo / ".mcp.json").exists()


def test_mcp_user_scope_replaces_its_own_entry(
    repo: Path, fakes: FakeTools, home: Path
) -> None:
    """A user-scope reinstall removes kmctl's okf-bundle, then adds it again."""
    fakes.on("uvx", "apm install", write={".apm/apm.lock.yaml": _lock()})
    (home / ".claude" / ".claude.json").write_text(
        json.dumps({"mcpServers": {"okf-bundle": {"command": "sh", "args": []}}})
    )

    _install("--scope", "user")

    mcp = [c.args[:3] for c in fakes.calls("claude") if c.args[0] == "mcp"]
    assert mcp == [["mcp", "remove", "okf-bundle"], ["mcp", "add-json", "okf-bundle"]]


def test_mcp_user_scope_drops_its_own_beside_another_okf_server(
    repo: Path, fakes: FakeTools, home: Path
) -> None:
    """With another okf server at user scope, kmctl removes its own and adds none."""
    fakes.on("uvx", "apm install", write={".apm/apm.lock.yaml": _lock()})
    (home / ".claude" / ".claude.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "bundle": {"command": "uv", "args": ["okf_mcp.py"]},
                    "okf-bundle": {"command": "sh", "args": []},
                }
            }
        )
    )

    _install("--scope", "user")

    mcp = [c.args for c in fakes.calls("claude") if c.args[0] == "mcp"]
    assert mcp == [["mcp", "remove", "okf-bundle", "--scope", "user"]]


def test_mcp_user_scope_keeps_an_existing_okf_server(
    repo: Path, fakes: FakeTools, home: Path
) -> None:
    fakes.on("uvx", "apm install", write={".apm/apm.lock.yaml": _lock()})
    (home / ".claude" / ".claude.json").write_text(
        json.dumps(
            {"mcpServers": {"bundle": {"command": "uv", "args": ["okf_mcp.py"]}}}
        )
    )

    result = _install("--scope", "user")

    assert [c for c in fakes.calls("claude") if c.args[0] == "mcp"] == []
    assert "kept the okf MCP server 'bundle'" in result.stdout


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
    assert len(_kmctl_hooks(_settings(home))) == 1
    assert not (repo / ".claude").exists()
    assert not (repo / "apm.yml").exists()


def test_user_scope_follows_claude_config_dir(
    repo: Path, fakes: FakeTools, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = tmp_path / "elsewhere"
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(config))
    fakes.on("uvx", "apm install", write={".apm/apm.lock.yaml": _lock()})

    _install("--scope", "user")

    assert len(_kmctl_hooks(json.loads((config / "settings.json").read_text()))) == 1
    assert not (tmp_path / "home" / ".claude" / "settings.json").exists()


def test_user_scope_defaults_to_home_claude(
    repo: Path, fakes: FakeTools, home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CLAUDE_CONFIG_DIR")
    fakes.on("uvx", "apm install", write={".apm/apm.lock.yaml": _lock()})

    _install("--scope", "user")

    assert len(_kmctl_hooks(_settings(home))) == 1


def test_user_scope_is_not_the_default(
    repo: Path, fakes: FakeTools, home: Path
) -> None:
    _install()

    assert "-g" not in _apm_calls(fakes, "install")[0].args
    assert not (home / ".claude" / "settings.json").exists()
    assert not (home / ".apm").exists()


# r8: status ---------------------------------------------------------------------


def _status(*args: str) -> Result:
    """Run ``kmctl plugin status`` with ``args``."""
    return _kmctl("plugin", "status", *args)


def test_status_reports_no_problems_after_install(repo: Path, fakes: FakeTools) -> None:
    _install()

    data = json.loads(_status("--json").stdout)

    assert data == {
        "cli_version": version("kmctl"),
        "scope": "project",
        "package_ref": REF,
        "hook": True,
        "problems": [],
    }


def test_status_mismatched_ref_names_update(repo: Path, fakes: FakeTools) -> None:
    _install()
    (repo / "apm.lock.yaml").write_text(_lock(ref="v0.0.1"))

    result = _status()

    assert result.exit_code == 0
    assert re.search(
        r"problem: version mismatch.*v0\.0\.1.*; run kmctl plugin update --harness claude$",
        result.stdout,
        re.MULTILINE,
    )


def test_status_missing_hook_names_install(repo: Path, fakes: FakeTools) -> None:
    _install()
    (repo / ".claude" / "settings.json").write_text("{}")

    [problem] = json.loads(_status("--json").stdout)["problems"]

    assert "SessionStart hook is missing" in problem
    assert problem.endswith("run kmctl plugin install --harness claude")


def test_status_changed_hook_names_update(repo: Path, fakes: FakeTools) -> None:
    _install()
    path = repo / ".claude" / "settings.json"
    path.write_text(path.read_text().replace('"timeout": 10', '"timeout": 99'))

    [problem] = json.loads(_status("--json").stdout)["problems"]

    assert problem.endswith("run kmctl plugin update")


def test_status_without_install_names_install(repo: Path, fakes: FakeTools) -> None:
    data = json.loads(_status("--json").stdout)

    assert data["package_ref"] is None and data["hook"] is False
    assert len(data["problems"]) == 2
    assert all(
        p.endswith("run kmctl plugin install --harness claude")
        for p in data["problems"]
    )
    assert fakes.calls() == []


def test_status_user_scope_fix_names_the_scope(repo: Path, fakes: FakeTools) -> None:
    data = json.loads(_status("--scope", "user", "--json").stdout)

    assert data["scope"] == "user"
    assert len(data["problems"]) == 2
    assert all(p.endswith("--scope user") for p in data["problems"])
