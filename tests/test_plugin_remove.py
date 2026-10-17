"""kmctl plugin remove, with fake uvx and claude on PATH (ADR 0019).

The fake ``apm install`` writes what APM 0.33.0 deploys (the helpers come
from test_doctor); the fake ``apm uninstall`` writes back the apm.yml and
lock APM leaves, as spike:plugin-remove/3 saw them.
"""

from __future__ import annotations

import json
from importlib.metadata import version
from pathlib import Path

import pytest
import yaml
from conftest import plain
from fixtures.fake_tools import FakeTools
from test_doctor import Setup, _apm_writes
from typer.testing import CliRunner, Result

import kmctl
from kmctl import antigravity, app, plugin

ROOT = Path(__file__).resolve().parents[1]
REF = f"v{version('kmctl')}"
APM = ["--from", plugin.APM_CLI, "apm"]
GITHUB = plugin.DEFAULT_SOURCE
GITHUB_NAME = "github.com/JasperHG90/Knowledge-management/apm"
EMPTY_LOCK = yaml.safe_dump({"lockfile_version": "1", "dependencies": []})
QUESTION = "Which harnesses should kmctl be removed from?"


@pytest.fixture
def setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Setup:
    """A scratch repository with .okf/, HOME and fake uvx and claude alone on PATH."""
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home / ".claude"))
    monkeypatch.setenv("XDG_DATA_HOME", str(home / ".local" / "share"))
    repo = tmp_path / "repo"
    (repo / ".okf").mkdir(parents=True)
    monkeypatch.chdir(repo)
    fakes = FakeTools(tmp_path, tools=("uvx", "claude"))
    monkeypatch.setenv("PATH", fakes.path)
    return Setup(repo, home, fakes)


def _kmctl(*args: str, stdin: str | None = None) -> Result:
    """Run kmctl in-process with ``args``."""
    return CliRunner().invoke(app, list(args), input=stdin)


def _manifest(entries: list[object], targets: list[str]) -> str:
    """An apm.yml with these dependency entries and targets."""
    return yaml.safe_dump(
        {
            "name": "repo",
            "version": "0.1.0",
            "dependencies": {"apm": entries},
            "targets": targets,
        }
    )


def _install(
    s: Setup,
    harnesses: tuple[str, ...] = ("claude", "antigravity"),
    *flags: str,
    uninstall_leaves: list[object] | None = None,
) -> None:
    """Install for ``harnesses`` with fake APM; its uninstall leaves ``uninstall_leaves`` in apm.yml."""
    scope = "user" if "user" in flags else "project"
    s.fakes.on(
        "uvx",
        f"apm install --target {','.join(harnesses)}",
        write=_apm_writes(harnesses, scope),
    )
    for kept in harnesses:
        s.fakes.on(
            "uvx", f"apm install --target {kept}", write=_apm_writes((kept,), scope)
        )
    top = ".apm/" if scope == "user" else ""
    s.fakes.on(
        "uvx",
        "apm uninstall",
        write={
            f"{top}apm.yml": _manifest(uninstall_leaves or [], list(harnesses)),
            f"{top}apm.lock.yaml": EMPTY_LOCK,
        },
    )
    result = _kmctl("plugin", "install", "--harness", ",".join(harnesses), *flags)
    assert result.exit_code == 0, result.output


def _remove(*args: str) -> Result:
    """Run ``kmctl plugin remove`` with ``args``; fail the test unless it exits 0."""
    result = _kmctl("plugin", "remove", *args)
    assert result.exit_code == 0, result.output
    return result


def _apm_calls(fakes: FakeTools, verb: str) -> list[list[str]]:
    """The fake uvx runs whose APM verb is ``verb``, as argument lists."""
    return [c.args for c in fakes.calls("uvx") if c.args[3:4] == [verb]]


def _settings(root: Path) -> dict:
    return json.loads((root / ".claude" / "settings.json").read_text())


def _hook_commands(settings: dict) -> list[str]:
    groups = settings.get("hooks", {}).get("SessionStart", [])
    return [h["command"] for g in groups for h in g["hooks"]]


# r1: the harness question, and nothing installed --------------------------------


@pytest.fixture
def terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make kmctl see a terminal on stdin."""
    monkeypatch.setattr(kmctl, "_at_terminal", lambda: True)


@pytest.mark.usefixtures("terminal")
def test_prompt_suggests_the_installed_harnesses(setup: Setup) -> None:
    _install(setup)

    result = _kmctl("plugin", "remove", stdin="\n")

    assert result.exit_code == 0, result.output
    assert QUESTION in result.stderr
    assert "[claude,antigravity]" in result.stderr
    assert QUESTION not in result.stdout
    assert "removed kmctl from claude, antigravity" in result.stdout


@pytest.mark.usefixtures("terminal")
def test_prompt_answer_names_what_is_removed(setup: Setup) -> None:
    _install(setup)

    result = _kmctl("plugin", "remove", stdin="2\n")

    assert result.exit_code == 0, result.output
    assert "removed kmctl from antigravity" in result.stdout
    assert "still installed for claude" in result.stdout


@pytest.mark.parametrize("flags", [(), ("--json",)])
def test_no_terminal_without_harness_refuses(
    setup: Setup, flags: tuple[str, ...]
) -> None:
    _install(setup)
    before = len(setup.fakes.calls("uvx"))

    result = _kmctl("plugin", "remove", *flags)

    assert result.exit_code == 1
    assert QUESTION not in result.output
    assert "--harness" in result.stderr and "claude, antigravity" in result.stderr
    assert len(setup.fakes.calls("uvx")) == before


@pytest.mark.parametrize("flags", [(), ("--harness", "claude")])
def test_nothing_installed_says_so_and_runs_nothing(
    setup: Setup, flags: tuple[str, ...]
) -> None:
    result = _remove(*flags)

    assert "removed nothing" in result.stdout
    assert setup.fakes.calls() == []


def test_harness_unknown_is_refused(setup: Setup) -> None:
    result = _kmctl("plugin", "remove", "--harness", "opencode")

    assert result.exit_code == 1
    assert "one of: claude, antigravity" in result.stderr


@pytest.mark.parametrize("option", ["--harness", "--scope", "--json"])
def test_remove_help_names_each_option(option: str) -> None:
    result = CliRunner().invoke(
        app, ["plugin", "remove", "--help"], env={"COLUMNS": "80"}, terminal_width=80
    )

    assert option in plain(result.stdout)


# r2: the uninstall name ---------------------------------------------------------


@pytest.mark.parametrize(
    ("entry", "name"),
    [
        ({"git": GITHUB, "path": "apm", "ref": REF}, GITHUB_NAME),
        (
            {"git": "http://127.0.0.1:18765/o/kmctl.git", "path": "apm"},
            "127.0.0.1:18765/o/kmctl/apm",
        ),
        (
            {
                "git": "git@github.com:JasperHG90/Knowledge-management.git",
                "path": "apm",
            },
            GITHUB_NAME,
        ),
        (
            "JasperHG90/Knowledge-management/apm#v0.3.0",
            "JasperHG90/Knowledge-management/apm#v0.3.0",
        ),
    ],
)
def test_uninstall_name_follows_the_entry(entry: object, name: str) -> None:
    assert plugin.uninstall_name(entry) == name


def test_uninstall_name_used_and_nothing_installed_after(setup: Setup) -> None:
    _install(setup)
    installs = len(_apm_calls(setup.fakes, "install"))

    _remove("--harness", "claude,antigravity")

    assert _apm_calls(setup.fakes, "uninstall") == [[*APM, "uninstall", GITHUB_NAME]]
    assert len(_apm_calls(setup.fakes, "install")) == installs


def test_uninstall_name_user_scope_passes_g(setup: Setup) -> None:
    _install(setup, ("claude",), "--scope", "user")

    _remove("--harness", "claude", "--scope", "user")

    assert _apm_calls(setup.fakes, "uninstall") == [
        [*APM, "uninstall", GITHUB_NAME, "-g"]
    ]


# r3: the harnesses kept ---------------------------------------------------------


def test_kept_harness_reinstalled_from_the_entry_source_and_ref(setup: Setup) -> None:
    mirror = "https://mirror.example/JasperHG90/Knowledge-management.git"
    _install(setup)
    path = setup.repo / "apm.yml"
    data = yaml.safe_load(path.read_text())
    data["dependencies"]["apm"][0].update(git=mirror, ref="v0.0.9")
    path.write_text(yaml.safe_dump(data))

    _remove("--harness", "antigravity")

    assert _apm_calls(setup.fakes, "uninstall") == [
        [*APM, "uninstall", "mirror.example/JasperHG90/Knowledge-management/apm"]
    ]
    [*_, last] = _apm_calls(setup.fakes, "install")
    assert last == [*APM, "install", "--target", "claude"]
    [entry] = yaml.safe_load(path.read_text())["dependencies"]["apm"]
    assert (entry["git"], entry["ref"]) == (mirror, "v0.0.9")


def test_kept_reinstall_failure_names_the_way_back(
    setup: Setup, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install(setup)
    broken = FakeTools(tmp_path / "broken", tools=("uvx", "claude"))
    broken.on("uvx", "apm uninstall", write={"apm.lock.yaml": EMPTY_LOCK})
    broken.on("uvx", "apm install", exit=1, stderr="error: network is unreachable\n")
    monkeypatch.setenv("PATH", broken.path)

    result = _kmctl("plugin", "remove", "--harness", "antigravity")

    assert result.exit_code == 1
    assert "network is unreachable" in result.stderr
    assert "uninstalled it from claude too" in result.stderr
    assert f"kmctl plugin install --harness claude --source {GITHUB}" in result.stderr
    assert "at this kmctl's version" in result.stderr


# r4: the pieces kmctl wrote, and targets -----------------------------------------


def test_claude_pieces_removed_keeping_other_hooks_and_servers(setup: Setup) -> None:
    _install(setup, ("claude",))
    settings = _settings(setup.repo)
    other = {"type": "command", "command": "echo mine"}
    settings["hooks"]["SessionStart"][0]["hooks"].append(other)
    settings["theme"] = "dark"
    (setup.repo / ".claude" / "settings.json").write_text(json.dumps(settings))
    mcp = json.loads((setup.repo / ".mcp.json").read_text())
    mcp["mcpServers"]["mine"] = {"command": "my-server"}
    (setup.repo / ".mcp.json").write_text(json.dumps(mcp))

    _remove("--harness", "claude")

    after = _settings(setup.repo)
    assert _hook_commands(after) == ["echo mine"]
    assert after["theme"] == "dark"
    assert json.loads((setup.repo / ".mcp.json").read_text()) == {
        "mcpServers": {"mine": {"command": "my-server"}}
    }


def test_claude_pieces_only_kmctl_leaves_no_hook_and_no_mcp_file(setup: Setup) -> None:
    _install(setup, ("claude",))

    _remove("--harness", "claude")

    assert "hooks" not in _settings(setup.repo)
    assert not (setup.repo / ".mcp.json").exists()


def test_claude_pieces_keep_an_okf_server_kmctl_did_not_write(setup: Setup) -> None:
    _install(setup, ("claude",))
    path = setup.repo / ".mcp.json"
    theirs = {"command": "uv", "args": ["run", "x/servers/okf_mcp.py", ".okf"]}
    path.write_text(json.dumps({"mcpServers": {"their-okf": theirs}}))

    _remove("--harness", "claude")

    assert json.loads(path.read_text()) == {"mcpServers": {"their-okf": theirs}}


def test_claude_pieces_user_scope_runs_claude_mcp_remove(setup: Setup) -> None:
    _install(setup, ("claude",), "--scope", "user")
    config = setup.home / ".claude" / ".claude.json"
    config.write_text(
        json.dumps({"mcpServers": {"okf-bundle": plugin.okf_mcp_server()}})
    )

    _remove("--harness", "claude", "--scope", "user")

    removes = [
        c.args for c in setup.fakes.calls("claude") if c.args[:2] == ["mcp", "remove"]
    ]
    assert removes[-1] == ["mcp", "remove", "okf-bundle", "--scope", "user"]
    assert "hooks" not in json.loads(
        (setup.home / ".claude" / "settings.json").read_text()
    )


def test_antigravity_pieces_removed(setup: Setup) -> None:
    _install(setup, ("antigravity",))
    hooks = setup.repo / ".agents" / "hooks.json"
    hooks.write_text("{}\n")
    mine = setup.repo / ".agents" / "keep.md"
    mine.write_text("mine\n")

    _remove("--harness", "antigravity")

    assert not antigravity.plugin_dir(setup.repo).exists()
    assert not hooks.exists()
    assert mine.read_text() == "mine\n"


def test_antigravity_pieces_keep_a_hooks_file_with_hooks(setup: Setup) -> None:
    _install(setup, ("antigravity",))
    hooks = setup.repo / ".agents" / "hooks.json"
    hooks.write_text(json.dumps({"theirs": {"Stop": [{"command": "echo"}]}}))

    _remove("--harness", "antigravity")

    assert json.loads(hooks.read_text()) == {"theirs": {"Stop": [{"command": "echo"}]}}


def test_targets_dropped_when_no_other_dependency_is_left(setup: Setup) -> None:
    _install(setup)

    _remove("--harness", "antigravity")

    assert yaml.safe_load((setup.repo / "apm.yml").read_text())["targets"] == ["claude"]


def test_targets_kept_with_a_note_when_another_dependency_is_left(
    setup: Setup,
) -> None:
    other = "someone/rules#abc"
    _install(setup, uninstall_leaves=[other])

    result = _remove("--harness", "antigravity")

    data = yaml.safe_load((setup.repo / "apm.yml").read_text())
    assert data["targets"] == ["claude", "antigravity"]
    assert other in data["dependencies"]["apm"]
    assert "kept antigravity in apm.yml's targets" in result.stdout
    assert "bare apm install" in result.stdout


# r5: doctor after a remove, a second remove, the Next line -----------------------


def test_after_remove_doctor_reports_only_the_kept_harness(setup: Setup) -> None:
    _install(setup, uninstall_leaves=["someone/rules#abc"])

    _remove("--harness", "antigravity")

    assert kmctl.harnesses_found(setup.repo) == ["claude"]


def test_remove_again_changes_nothing(setup: Setup) -> None:
    _install(setup, ("claude",))
    _remove("--harness", "claude")
    calls = len(setup.fakes.calls())
    files = sorted(p for p in setup.repo.rglob("*") if p.is_file())

    result = _remove("--harness", "claude")

    assert "not installed for claude" in result.stdout
    assert len(setup.fakes.calls()) == calls
    assert sorted(p for p in setup.repo.rglob("*") if p.is_file()) == files


@pytest.mark.parametrize("flags", [(), ("--scope", "user")])
def test_next_line_names_doctor(setup: Setup, flags: tuple[str, ...]) -> None:
    harnesses = ("claude",)
    _install(setup, harnesses, *flags)

    result = _remove("--harness", "claude", *flags)

    want = "kmctl doctor --scope user" if flags else "kmctl doctor"
    assert plain(result.stdout).strip().splitlines()[-1] == f"Next: {want}"


def test_remove_json_is_one_object(setup: Setup) -> None:
    _install(setup)

    result = _remove("--harness", "antigravity", "--json")

    assert json.loads(result.stdout) == {
        "scope": "project",
        "removed": ["antigravity"],
        "kept": ["claude"],
        "notes": json.loads(result.stdout)["notes"],
    }


# r7: the help, the reference, the how-to and the decision ------------------------


def test_remove_help_says_what_it_removes() -> None:
    result = CliRunner().invoke(
        app, ["plugin", "remove", "--help"], env={"COLUMNS": "80"}, terminal_width=80
    )
    text = " ".join(plain(result.stdout).replace("│", " ").split())

    for term in (
        "apm uninstall",
        "SessionStart",
        "okf-bundle",
        ".agents/plugins/kmctl/",
        "targets",
    ):
        assert term in text, term


def test_remove_docs_reference_how_to_and_decision() -> None:
    commands = (ROOT / "docs" / "reference" / "commands.md").read_text()
    assert "### `kmctl plugin remove`" in commands
    how_to = (
        ROOT / "docs" / "how-to" / "install-the-plugin-and-the-ci-action.md"
    ).read_text()
    assert "kmctl plugin remove" in how_to
    [decision] = (ROOT / ".okf" / "decisions").glob("0019-*.md")
    text = decision.read_text()
    for term in ("apm uninstall", "targets", "ref", "spike:plugin-remove/2"):
        assert term in text, term


# r6: a real install and remove in a scratch consumer ------------------------------


def _files_under(root: Path, *tops: str) -> list[str]:
    """Every file under the ``tops`` folders of ``root``, relative to it."""
    return sorted(
        p.relative_to(root).as_posix()
        for top in tops
        for p in (root / top).rglob("*")
        if p.is_file()
    )


@pytest.mark.integration
def test_remove_in_a_consumer_takes_out_one_harness_then_the_other(
    consumer: Path, served: str
) -> None:
    (consumer / "README.md").write_text("keep me\n")
    install = _kmctl(
        "plugin", "install", "--harness", "claude,antigravity", "--source", served
    )
    assert install.exit_code == 0, install.output
    assert _kmctl("init").exit_code == 0

    first = _kmctl("plugin", "remove", "--harness", "antigravity")

    assert first.exit_code == 0, first.output
    assert _files_under(consumer, ".agents") == []
    checks = {
        c["id"]: c for c in json.loads(_kmctl("doctor", "--json").stdout)["checks"]
    }
    for cid in (
        "claude.lock",
        "claude.files",
        "claude.okf-skills",
        "claude.hook",
        "claude.okf-mcp",
    ):
        assert checks[cid]["ok"], checks[cid]
    assert not any(c.startswith("antigravity.") for c in checks)

    second = _kmctl("plugin", "remove", "--harness", "claude")

    assert second.exit_code == 0, second.output
    assert (
        _files_under(
            consumer,
            ".agents",
            ".claude/skills",
            ".claude/agents",
            ".claude/rules",
            ".claude/hooks",
        )
        == []
    )
    settings = consumer / ".claude" / "settings.json"
    assert not settings.exists() or "kmctl briefing" not in settings.read_text()
    assert not (consumer / ".mcp.json").exists()
    assert not (consumer / "apm.lock.yaml").exists()
    assert (consumer / "README.md").read_text() == "keep me\n"
    assert kmctl.harnesses_found(consumer) == []


def test_remove_summary_names_the_harness_still_installed(setup: Setup) -> None:
    _install(setup, ("claude",))

    result = _remove("--harness", "antigravity")

    assert "not installed for antigravity" in result.stdout
    assert "removed nothing; kmctl is installed for claude" in result.stdout


def test_remove_failure_names_remove_not_install(
    setup: Setup, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install(setup, ("claude",))
    broken = FakeTools(tmp_path / "broken", tools=("uvx", "claude"))
    broken.on("uvx", "apm uninstall", exit=1, stderr="error: lock is busy\n")
    monkeypatch.setenv("PATH", broken.path)

    result = _kmctl("plugin", "remove", "--harness", "claude")

    assert result.exit_code == 1
    assert "lock is busy" in result.stderr
    assert result.stderr.rstrip().endswith("then kmctl plugin remove again")
