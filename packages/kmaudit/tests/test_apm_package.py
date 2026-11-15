"""kmaudit's APM package carries its skills, its Claude Code agents and its MCP server (ADR 0043).

The package is ``packages/kmaudit/apm``: the extract-claims and write-checks
skills for every harness, the kmaudit MCP server from the package's own
release tag, and a Claude-only sub-package, ``claude/``, with the two agents,
which call the MCP tools and have no shell. The ``integration`` test installs
the package with the real APM from a local copy of this tree.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml
from packaging.version import Version

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "packages" / "kmaudit" / "apm"
SKILLS = PACKAGE / ".apm" / "skills"
CLAUDE = PACKAGE / "claude"
AGENTS = CLAUDE / ".apm" / "agents"
GIT_URL = "https://github.com/JasperHG90/kmctl.git"
SERVER_SOURCE = "git+https://github.com/JasperHG90/kmctl"
APM_CLI = "apm-cli==0.33.0"
#: Each agent and the kmaudit MCP tools it calls, past Read, Grep and Glob.
AGENT_TOOLS = {
    "kmaudit-claims-extractor": ["claims_todo", "claims_submit"],
    "kmaudit-check-writer": ["checks_todo", "checks_try", "checks_submit"],
}


def _load(path: Path) -> dict:
    """A YAML file, parsed."""
    return yaml.safe_load(path.read_text())


def _front_matter(path: Path) -> dict:
    """The front matter of a markdown file."""
    return yaml.safe_load(path.read_text().split("---")[1])


def _version() -> str:
    """kmaudit's one version, from its package's apm.yml."""
    return str(_load(PACKAGE / "apm.yml")["version"])


def _tag() -> str:
    """The release tag the package's server installs from: the version's, or the coming release's for a .dev version."""
    return f"kmaudit-v{Version(_version()).base_version}"


def _server() -> dict:
    """The kmaudit server the package's apm.yml declares."""
    servers = _load(PACKAGE / "apm.yml")["dependencies"]["mcp"]
    [server] = [s for s in servers if s["name"] == "kmaudit"]
    return server


# r1: the package --------------------------------------------------------------


def test_package_holds_both_skills_and_only_them() -> None:
    assert sorted(p.name for p in SKILLS.iterdir()) == [
        "extract-claims",
        "write-checks",
    ]
    for name in ("extract-claims", "write-checks"):
        assert _front_matter(SKILLS / name / "SKILL.md")["name"] == name
        assert (SKILLS / name / "evals" / "evals.json").is_file(), name


def test_package_pulls_in_the_claude_sub_package_at_its_version() -> None:
    manifest = _load(PACKAGE / "apm.yml")
    sub = _load(CLAUDE / "apm.yml")

    assert manifest["name"] == "kmaudit"
    assert manifest["dependencies"]["apm"] == ["./claude"]
    assert sub["name"] == "kmaudit-claude"
    assert sub["targets"] == ["claude"]
    assert str(sub["version"]) == _version()


def test_package_declares_the_server_at_its_own_tag() -> None:
    """uvx installs kmaudit from the package's own release tag and runs kmaudit mcp over stdio."""
    server = _server()

    assert server["transport"] == "stdio"
    assert server["registry"] is False
    assert server["command"] == "uvx"
    assert server["args"] == [
        "--from",
        f"{SERVER_SOURCE}@{_tag()}#subdirectory=packages/kmaudit",
        "kmaudit",
        "mcp",
    ]


def test_sub_package_holds_the_two_agents() -> None:
    assert sorted(p.stem for p in AGENTS.iterdir()) == sorted(AGENT_TOOLS)
    assert sorted(p.name for p in (CLAUDE / ".apm").iterdir()) == ["agents"]


@pytest.mark.parametrize("agent", sorted(AGENT_TOOLS))
def test_agent_calls_mcp_tools_with_no_shell_and_no_hook(agent: str) -> None:
    """Its tools are Read, Grep, Glob and its kmaudit MCP tools, as Claude Code names them; no Bash, no hooks."""
    meta = _front_matter(AGENTS / f"{agent}.md")
    tools = [t.strip() for t in meta["tools"].split(",")]

    assert meta["name"] == agent
    assert meta["model"] == "haiku"
    assert tools == [
        "Read",
        "Grep",
        "Glob",
        *(f"mcp__kmaudit__{t}" for t in AGENT_TOOLS[agent]),
    ]
    assert "hooks" not in meta
    assert "Bash" not in tools


def test_agents_name_tools_the_server_has() -> None:
    """The five tools the agents call are the server's own."""
    import asyncio

    from kmaudit.mcp_server import server

    names = {t.name for t in asyncio.run(server.list_tools())}
    called = {t for tools in AGENT_TOOLS.values() for t in tools}

    assert len(called) == 5
    assert called <= names


# r4: installed with APM -------------------------------------------------------


def _git(*args: str, cwd: Path) -> None:
    """Run git in ``cwd``, failing the test with its output when it fails."""
    proc = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )
    assert proc.returncode == 0, proc.stderr


@pytest.mark.integration
def test_apm_installs_the_server_for_both_and_the_agents_for_claude_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """apm install for claude and opencode writes the server into .mcp.json and opencode.json, and the agents into .claude/agents/ only."""
    # The package in a git repository of its own, tagged as its server names it.
    work = tmp_path / "kmctl"
    shutil.copytree(PACKAGE, work / "packages" / "kmaudit" / "apm")
    _git("init", "-q", "-b", "main", cwd=work)
    _git("add", "-A", cwd=work)
    _git(
        *("-c", "user.email=t@e.invalid", "-c", "user.name=t", "commit", "-qm", "p"),
        cwd=work,
    )
    _git("tag", _tag(), cwd=work)
    bare = tmp_path / "srv" / "kmctl.git"
    _git("clone", "-q", "--bare", str(work), str(bare), cwd=tmp_path)
    # APM refuses a rewrite to http:// or another host, but follows one to
    # file:// (spike:starter-in-repo/5), so GitHub is never reached.
    gitconfig = tmp_path / "gitconfig"
    gitconfig.write_text(f'[url "file://{bare}"]\n\tinsteadOf = {GIT_URL}\n')
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home / ".claude"))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(gitconfig))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "0")
    for token in ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_APM_PAT", "GITHUB_COPILOT_PAT"):
        monkeypatch.delenv(token, raising=False)
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    uvx = shutil.which("uvx")
    assert uvx, "uvx must be on PATH"
    consumer = tmp_path / "consumer"
    consumer.mkdir()
    _git("init", "-q", cwd=consumer)
    entry = {"git": GIT_URL, "path": "packages/kmaudit/apm", "ref": _tag()}
    (consumer / "apm.yml").write_text(
        yaml.safe_dump(
            {
                "name": "consumer",
                "version": "0.1.0",
                "dependencies": {"apm": [entry]},
                "targets": ["claude", "opencode"],
            }
        )
    )

    proc = subprocess.run(
        [uvx, "--from", APM_CLI, "apm", "install"],
        cwd=consumer,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ},
    )

    assert proc.returncode == 0, proc.stderr + proc.stdout
    server = _server()
    claude = json.loads((consumer / ".mcp.json").read_text())["mcpServers"]["kmaudit"]
    assert claude["command"] == "uvx"
    assert claude["args"] == server["args"]
    opencode = json.loads((consumer / "opencode.json").read_text())["mcp"]["kmaudit"]
    assert opencode["command"] == ["uvx", *server["args"]]
    agents = consumer / ".claude" / "agents"
    for name in AGENT_TOOLS:
        assert (agents / f"{name}.md").read_text() == (
            AGENTS / f"{name}.md"
        ).read_text(), name
    assert list((consumer / ".opencode" / "agents").glob("*")) == []
    for skill in ("extract-claims", "write-checks"):
        assert (consumer / ".claude" / "skills" / skill / "SKILL.md").is_file(), skill
        assert (consumer / ".agents" / "skills" / skill / "SKILL.md").is_file(), skill
