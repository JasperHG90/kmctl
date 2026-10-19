"""kmctl plugin patch: what kmctl adds after APM installs its package (ADR 0021).

The fake APM install writes what APM 0.33.0 deploys for kmctl's package
(``_apm_writes`` from test_doctor); patch never runs APM, which the fake uvx
on PATH records.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

import pytest
import yaml
from conftest import plain
from fixtures.fake_tools import FakeTools
from test_doctor import OKF_AGENTS, _apm_writes
from typer.main import get_command
from typer.testing import CliRunner, Result

from kmctl import antigravity, app, plugin

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
COMMANDS = ROOT / "docs" / "reference" / "commands.md"
DECISIONS = ROOT / ".okf" / "decisions"
OLD_GROUP = {"hooks": [plugin.hook_entry()]}
#: okf's own server entry, which okf-skills declares as bundle.
OKF_OWN = {"command": "uv", "args": ["run", "${CLAUDE_PLUGIN_ROOT}/servers/okf_mcp.py"]}


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


@pytest.fixture
def fakes(tmp_path: Path, home: Path, monkeypatch: pytest.MonkeyPatch) -> FakeTools:
    """Fake uvx and claude alone on PATH; patch must never run uvx."""
    tools = FakeTools(tmp_path / "fakes", tools=("uvx", "claude"))
    monkeypatch.setenv("PATH", tools.path)
    return tools


def _apm_install(
    root: Path,
    harnesses: tuple[str, ...] = ("claude", "antigravity"),
    scope: str = "project",
) -> None:
    """Write what ``apm install`` of kmctl's entry leaves in ``root`` (the repository, or HOME at user scope)."""
    for rel, text in _apm_writes(harnesses, scope).items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


def _kmctl(*args: str) -> Result:
    return CliRunner().invoke(app, list(args))


def _patch(*args: str) -> Result:
    """Run ``kmctl plugin patch``; fail the test unless it exits 0."""
    result = _kmctl("plugin", "patch", *args)
    assert result.exit_code == 0, result.output
    return result


def _files(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


# r1: what patch writes and removes --------------------------------------------------


def test_patch_writes_the_agents_and_drops_apms_okf_stop(
    repo: Path, fakes: FakeTools
) -> None:
    _apm_install(repo)
    hooks = repo / ".agents" / "hooks.json"
    data = json.loads(hooks.read_text())
    data["apm"]["Stop"].insert(
        0, {"type": "command", "command": antigravity.APM_OKF_STOP}
    )
    hooks.write_text(json.dumps(data))

    result = _patch()

    folder = antigravity.plugin_dir(repo)
    assert {
        k: v.decode() for k, v in _files(folder).items()
    } == antigravity.plugin_files(repo)
    assert sorted(_files(folder)) == [
        "agents/bundle-weaver.md",
        "agents/event-analyzer.md",
        "agents/kmctl-auditor.md",
        "plugin.json",
    ]
    assert not antigravity.apm_okf_stop_present(repo)
    assert antigravity.hook_present(repo)
    assert fakes.calls("uvx") == []
    assert "patched kmctl's package" in result.stdout


def test_patch_writes_nothing_for_a_harness_apm_did_not_install(
    repo: Path, fakes: FakeTools
) -> None:
    _apm_install(repo, ("claude",))

    result = _patch()

    assert not antigravity.plugin_dir(repo).exists()
    assert "for claude (project scope)" in result.stdout


def test_patch_claude_takes_out_an_older_kmctls_hook_and_keeps_every_server(
    repo: Path, fakes: FakeTools
) -> None:
    _apm_install(repo, ("claude",))
    settings = repo / ".claude" / "settings.json"
    data = json.loads(settings.read_text())
    data["hooks"]["SessionStart"].insert(0, OLD_GROUP)
    settings.write_text(json.dumps(data))
    # okf declares its own server under the name kmctl gives it.
    servers = {"mcpServers": {plugin.MCP_NAME: OKF_OWN, "mine": {"command": "x"}}}
    (repo / ".mcp.json").write_text(json.dumps(servers))

    result = _patch()

    assert len(plugin.kmctl_hooks(settings)) == 1
    assert json.loads((repo / ".mcp.json").read_text()) == servers
    assert "run apm install" not in result.stdout


def test_patch_claude_user_scope_uses_the_user_files(
    repo: Path, fakes: FakeTools, home: Path
) -> None:
    _apm_install(home, ("claude",), "user")
    settings = home / ".claude" / "settings.json"
    data = json.loads(settings.read_text())
    data["hooks"]["SessionStart"].append(OLD_GROUP)
    settings.write_text(json.dumps(data))
    (home / ".claude" / ".claude.json").write_text(
        json.dumps({"mcpServers": {plugin.MCP_NAME: OKF_OWN}})
    )

    result = _patch("--scope", "user")

    assert len(plugin.kmctl_hooks(settings)) == 1
    assert not [c for c in fakes.calls("claude") if c.args[:2] == ["mcp", "remove"]]
    assert "run apm install" not in result.stdout
    assert not (repo / ".agents").exists()


def test_patch_claude_removes_the_old_claude_plugin(
    repo: Path, fakes: FakeTools
) -> None:
    _apm_install(repo, ("claude",))
    fakes.on(
        "claude",
        "plugin list --json",
        stdout=json.dumps(
            [{"id": "kmctl@kmctl", "scope": "project", "projectPath": str(repo)}]
        ),
    )

    result = _patch()

    assert [c.args for c in fakes.calls("claude")][1:] == [
        ["plugin", "uninstall", "kmctl@kmctl", "--scope", "project"],
        ["plugin", "prune", "--scope", "project", "--yes"],
        ["plugin", "marketplace", "remove", "kmctl", "--scope", "project"],
    ]
    assert "removed the old claude plugin kmctl@kmctl" in result.stdout


def test_patch_again_changes_nothing(repo: Path, fakes: FakeTools) -> None:
    _apm_install(repo)
    _patch()
    before = _files(repo)

    _patch()

    assert _files(repo) == before
    assert fakes.calls("uvx") == []


def test_patch_json_is_one_object_and_text_ends_with_doctor(
    repo: Path, fakes: FakeTools
) -> None:
    _apm_install(repo)

    data = json.loads(_patch("--json").stdout)
    text = plain(_patch().stdout).strip().splitlines()

    assert data["scope"] == "project"
    assert data["harnesses"] == ["claude", "antigravity"]
    assert data["package_ref"].startswith("v")
    assert text[-1] == (
        "Next: start a new Claude Code session, then open this folder in "
        "Antigravity, trust it and start a new session, then kmctl doctor"
    )


# r2: refusals ------------------------------------------------------------------------


def test_patch_refuses_without_a_kmctl_package(repo: Path, fakes: FakeTools) -> None:
    result = _kmctl("plugin", "patch")

    assert result.exit_code == 1
    assert "apm.lock.yaml lists no kmctl package" in result.stderr
    assert '"path": "apm"' in result.stderr
    assert "apm install" in result.stderr
    assert fakes.calls() == []


@pytest.mark.parametrize("scope", ["project", "user"])
def test_patch_refuses_the_adr_0013_string_entry(
    repo: Path, fakes: FakeTools, home: Path, scope: str
) -> None:
    root = home / ".apm" if scope == "user" else repo
    root.mkdir(exist_ok=True)
    (root / "apm.yml").write_text(
        "name: x\nversion: 0.1.0\ndependencies:\n  apm:\n"
        "    - JasperHG90/Knowledge-management/apm#v0.3.0\n"
    )

    result = _kmctl(
        "plugin", "patch", *(["--scope", "user"] if scope == "user" else [])
    )

    assert result.exit_code == 1
    g = " -g" if scope == "user" else ""
    assert f"run apm uninstall{g} JasperHG90/Knowledge-management/apm," in result.stderr
    assert '"ref": "v' in result.stderr


def test_patch_refuses_the_v030_layout(repo: Path, fakes: FakeTools) -> None:
    (repo / "apm.yml").write_text(
        "name: x\nversion: 0.1.0\ndependencies:\n  apm:\n"
        "    - {git: https://github.com/JasperHG90/kmctl.git, path: apm, ref: v0.3.0}\n"
    )
    (repo / "apm.lock.yaml").write_text(
        yaml.safe_dump(
            {
                "dependencies": [
                    {
                        "repo_url": "jasperhg90/knowledge-management",
                        "name": "kmctl",
                        "virtual_path": "plugin",
                    }
                ]
            }
        )
    )

    result = _kmctl("plugin", "patch")

    assert result.exit_code == 1
    assert "run apm uninstall github.com/JasperHG90/kmctl/apm," in result.stderr


# r3: --undo --------------------------------------------------------------------------


def test_undo_deletes_only_the_plugin_folder(repo: Path, fakes: FakeTools) -> None:
    _apm_install(repo)
    _patch()
    before = {
        k: v
        for k, v in _files(repo).items()
        if not k.startswith(".agents/plugins/kmctl/")
    }

    result = _patch("--undo")

    assert not antigravity.plugin_dir(repo).exists()
    assert _files(repo) == before
    assert "deleted .agents/plugins/kmctl/" in result.stdout


def test_undo_with_nothing_to_undo_exits_zero(repo: Path, fakes: FakeTools) -> None:
    result = _patch("--undo")

    assert "nothing to undo" in result.stdout


def test_undo_user_scope_leaves_the_antigravity_folder_and_names_it(
    repo: Path, fakes: FakeTools
) -> None:
    _apm_install(repo)
    _patch()
    before = _files(repo)

    result = _patch("--undo", "--scope", "user")

    assert _files(repo) == before
    said = " ".join(plain(result.stdout).split())
    assert ".agents/plugins/kmctl/" in said
    assert "kmctl plugin patch --undo" in said
    assert "without --scope user" in said
    assert "deleted" not in said


def test_undo_user_scope_with_nothing_here_says_nothing_to_undo(
    repo: Path, fakes: FakeTools
) -> None:
    result = _patch("--undo", "--scope", "user")

    assert result.exit_code == 0
    assert "nothing to undo" in result.stdout
    assert "note:" not in result.stdout


def test_undo_docs_say_user_scope_leaves_project_files() -> None:
    help_text = " ".join(plain(_kmctl("plugin", "patch", "--help").stdout).split())
    reference = " ".join(COMMANDS.read_text().split())

    assert (
        "With --scope user, --undo leaves this repository's .agents/plugins/kmctl/ "
        "and OpenCode files, which are patched at project scope only, and names them"
    ) in help_text
    assert (
        "With `--scope user` it deletes nothing in this repository: it leaves "
        "`.agents/plugins/kmctl/` and the OpenCode files"
    ) in reference


# r4: the old verbs are gone -----------------------------------------------------------


@pytest.mark.parametrize("verb", ["install", "update", "remove"])
def test_old_verbs_no_longer_exist(verb: str) -> None:
    result = _kmctl("plugin", verb)

    assert result.exit_code == 2
    assert "No such command" in plain(result.output)
    assert sorted(get_command(app).commands["plugin"].commands) == ["patch"]


# r5: the README, the reference and the decision ----------------------------------------


def _section(text: str, heading: str) -> str:
    start = text.index(heading)
    end = text.find("\n## ", start + len(heading))
    return text[start : end if end != -1 else None]


def test_patch_docs_readme_installs_per_harness() -> None:
    install = _section(README.read_text(), "## Install")
    flat = " ".join(install.split())

    for harness in (
        "### Claude Code",
        "### Antigravity",
        "### OpenCode",
        "### More than one",
    ):
        assert harness in install, harness
    for step in (
        "path: apm",
        "uvx --from apm-cli==0.33.0 apm install --target claude",
        "uvx --from apm-cli==0.33.0 apm install --target antigravity",
        "uvx --from apm-cli==0.33.0 apm install --target opencode",
        "kmctl plugin patch",
        "trust",
        "kmctl plugin patch --undo",
        "apm uninstall",
        "claude mcp remove bundle --scope user",
    ):
        assert step in flat, step
    assert re.search(r"[Uu]pgrad", install)


def test_patch_docs_reference_and_decision() -> None:
    commands = COMMANDS.read_text()
    assert "### `kmctl plugin patch`" in commands
    for old in (
        "### `kmctl plugin install`",
        "### `kmctl plugin update`",
        "### `kmctl plugin remove`",
    ):
        assert old not in commands, old
    [decision] = DECISIONS.glob("0021-*.md")
    assert "ADR 0019" in decision.read_text() and "ADR 0014" in decision.read_text()
    old = next(DECISIONS.glob("0019-*.md")).read_text()
    assert decision.name in old


# r6: a real APM install, patch, undo and uninstall --------------------------------------


@pytest.mark.integration
def test_patch_after_a_real_apm_install_then_undo_and_uninstall(
    consumer: Path, served: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fakes = FakeTools(tmp_path / "fakes", tools=("claude", "agy"))
    monkeypatch.setenv("PATH", f"{fakes.bin}:{os.environ['PATH']}")
    home = Path(os.environ["HOME"])
    trust = home / ".gemini" / "antigravity-cli" / "settings.json"
    trust.parent.mkdir(parents=True)
    trust.write_text(json.dumps({"trustedWorkspaces": [str(consumer.resolve())]}))
    entry = {
        "git": served,
        "path": "apm",
        "ref": plugin.package_ref(),
        "allow_insecure": True,
    }
    (consumer / "apm.yml").write_text(
        yaml.safe_dump(
            {
                "name": "consumer",
                "version": "0.1.0",
                "dependencies": {"apm": [entry]},
                "targets": ["claude", "antigravity"],
            }
        )
    )
    apm = ["uvx", "--from", plugin.APM_CLI, "apm"]
    install = subprocess.run(
        [*apm, "install", "--allow-insecure"],
        cwd=consumer,
        capture_output=True,
        text=True,
        check=False,
    )
    assert install.returncode == 0, install.stderr + install.stdout

    patch = _kmctl("plugin", "patch")
    init = _kmctl("init")
    doctor = _kmctl("doctor")

    assert patch.exit_code == 0, patch.output
    assert init.exit_code == 0, init.output
    assert doctor.exit_code == 0, doctor.output

    assert _kmctl("plugin", "patch", "--undo").exit_code == 0
    uninstall = subprocess.run(
        [*apm, "uninstall", plugin.uninstall_name(entry)],
        cwd=consumer,
        capture_output=True,
        text=True,
        check=False,
    )
    assert uninstall.returncode == 0, uninstall.stderr + uninstall.stdout
    left = [
        p.relative_to(consumer).as_posix()
        for top in (".claude", ".agents")
        for p in (consumer / top).rglob("*")
        if p.is_file()
    ]
    assert not [
        p for p in left if "plugins/kmctl" in p or "/skills/" in p or "/rules/" in p
    ]
    assert plugin.kmctl_hooks(consumer / ".claude" / "settings.json") == []
    assert not antigravity.hook_present(consumer)
    assert not (consumer / OKF_AGENTS).exists()


# The helpers patch runs, case by case ----------------------------------------------


def _list_plugins(fakes: FakeTools, *entries: dict) -> None:
    fakes.on("claude", "plugin list --json", stdout=json.dumps(list(entries)))


def test_patch_refuses_settings_that_are_not_json(repo: Path, fakes: FakeTools) -> None:
    _apm_install(repo, ("claude",))
    (repo / ".claude" / "settings.json").write_text("{not json")

    result = _kmctl("plugin", "patch")

    assert result.exit_code == 1
    assert "settings.json is not valid JSON" in result.stderr
    assert "then run the command again" in result.stderr
    assert "plugin install" not in result.stderr
    assert (repo / ".claude" / "settings.json").read_text() == "{not json"


def test_patch_old_plugin_of_another_repository_left_alone(
    repo: Path, fakes: FakeTools, tmp_path: Path
) -> None:
    _apm_install(repo, ("claude",))
    _list_plugins(
        fakes,
        {"id": "kmctl@kmctl", "scope": "project", "projectPath": str(tmp_path)},
        {"id": "kmctl@kmctl", "scope": "user"},
    )

    _patch()

    assert [c.args for c in fakes.calls("claude")] == [["plugin", "list", "--json"]]


def test_patch_old_plugin_at_user_scope_removed_at_user_scope(
    repo: Path, fakes: FakeTools, home: Path
) -> None:
    _apm_install(home, ("claude",), "user")
    _list_plugins(fakes, {"id": "kmctl@kmctl", "scope": "user"})

    _patch("--scope", "user")

    claude = [c.args for c in fakes.calls("claude") if c.args[0] == "plugin"]
    assert claude[1:] == [
        ["plugin", "uninstall", "kmctl@kmctl", "--scope", "user"],
        ["plugin", "prune", "--scope", "user", "--yes"],
        ["plugin", "marketplace", "remove", "kmctl", "--scope", "user"],
    ]


def test_patch_old_plugin_marketplace_already_gone_is_not_a_failure(
    repo: Path, fakes: FakeTools
) -> None:
    _apm_install(repo, ("claude",))
    _list_plugins(
        fakes, {"id": "kmctl@kmctl", "scope": "project", "projectPath": str(repo)}
    )
    fakes.on(
        "claude",
        "plugin marketplace remove",
        stderr="✘ Failed to remove marketplace: Marketplace 'kmctl' not found\n",
        exit=1,
    )

    result = _patch()

    assert "removed the old claude plugin kmctl@kmctl (project scope)" in result.stdout


def test_patch_old_plugin_uninstall_failure_names_cause_and_patch(
    repo: Path, fakes: FakeTools
) -> None:
    _apm_install(repo, ("claude",))
    _list_plugins(
        fakes, {"id": "kmctl@kmctl", "scope": "project", "projectPath": str(repo)}
    )
    fakes.on("claude", "plugin uninstall", stderr="error: busy\n", exit=1)

    result = _kmctl("plugin", "patch")

    assert result.exit_code == 1
    assert (
        "claude plugin uninstall kmctl@kmctl --scope project failed: error: busy"
        in (result.stderr)
    )
    assert result.stderr.rstrip().endswith("then kmctl plugin patch again")


def test_patch_old_plugin_skipped_without_claude(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, home: Path
) -> None:
    tools = FakeTools(tmp_path / "noclaude", tools=("uvx",))
    monkeypatch.setenv("PATH", tools.path)
    _apm_install(repo, ("claude",))

    result = _patch()

    assert "claude CLI is not on PATH" in result.stdout
    assert "kmctl@kmctl" in result.stdout


def test_patch_claude_keeps_other_hooks_in_a_shared_group(
    repo: Path, fakes: FakeTools
) -> None:
    _apm_install(repo, ("claude",))
    settings = repo / ".claude" / "settings.json"
    mine = {"type": "command", "command": "echo mine"}
    data = json.loads(settings.read_text())
    data["hooks"]["SessionStart"].append(
        {"matcher": "x", "hooks": [mine, plugin.hook_entry()]}
    )
    settings.write_text(json.dumps(data))

    _patch()

    groups = json.loads(settings.read_text())["hooks"]["SessionStart"]
    assert {"matcher": "x", "hooks": [mine]} in groups
    assert len(plugin.kmctl_hooks(settings)) == 1


def test_patch_claude_with_nothing_recorded_drops_every_kmctl_hook(
    repo: Path, fakes: FakeTools
) -> None:
    _apm_install(repo, ("claude",))
    settings = repo / ".claude" / "settings.json"
    settings.write_text(json.dumps({"hooks": {"SessionStart": [OLD_GROUP]}, "x": 1}))
    (repo / ".claude" / "apm-hooks.json").unlink()

    _patch()

    assert json.loads(settings.read_text()) == {"x": 1}


@pytest.mark.parametrize(
    ("entry", "name"),
    [
        (
            {
                "git": "https://github.com/JasperHG90/kmctl.git",
                "path": "apm",
            },
            "github.com/JasperHG90/kmctl/apm",
        ),
        (
            {"git": "http://127.0.0.1:18765/o/kmctl.git", "path": "apm"},
            "127.0.0.1:18765/o/kmctl/apm",
        ),
        (
            {
                "git": "git@github.com:JasperHG90/kmctl.git",
                "path": "apm",
            },
            "github.com/JasperHG90/kmctl/apm",
        ),
        (
            "JasperHG90/Knowledge-management/apm#v0.3.0",
            "JasperHG90/Knowledge-management/apm#v0.3.0",
        ),
    ],
)
def test_patch_uninstall_name_follows_the_entry(entry: object, name: str) -> None:
    assert plugin.uninstall_name(entry) == name


def test_undo_reports_the_scope_given(repo: Path, fakes: FakeTools) -> None:
    data = json.loads(_patch("--undo", "--scope", "user", "--json").stdout)

    assert data["scope"] == "user"
