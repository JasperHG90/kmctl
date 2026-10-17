"""kmctl doctor: one ok or fail line per check, a fix on every failure, read only and offline.

No test without a marker runs the real APM, claude or agy. ``FakeTools``
stands in for uvx (whose ``apm install`` writes the files, the lock and okf's
agents as APM would), uv (whose offline ``apm --version`` doctor runs),
claude, git and agy. PATH holds only those fakes, so a test removes one to
make a tool missing. HOME, CLAUDE_CONFIG_DIR and XDG_DATA_HOME point at
scratch folders. The ``integration`` test runs the real APM 0.33.0 against
this tree served from a local git server.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shutil
import socket
from collections.abc import Callable
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path

import httpx
import pytest
import respx
import yaml
from conftest import plain
from fixtures.fake_tools import FakeTools
from typer.main import get_command
from typer.testing import CliRunner, Result

from kmctl import antigravity, app, doctor, plugin

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "apm" / ".apm" / "skills"
SKILL_NAMES = sorted(p.name for p in SKILLS.iterdir() if p.is_dir())
COMMANDS = ROOT / "docs" / "reference" / "commands.md"
INSTALL_HOW_TO = ROOT / "docs" / "how-to" / "install-the-plugin-and-the-ci-action.md"
REF = f"v{version('kmctl')}"
OKF_AGENTS = "apm_modules/scaccogatto/okf-skills/agents"
FOLDERS = {"claude": ".claude", "antigravity": ".agents"}
AGENT = "---\nname: {name}\ndescription: d\ntools: Read, Bash\n---\n\nYou {name}.\n"
AG_FIX = "run kmctl plugin install --harness antigravity"
CLAUDE_FIX = "run kmctl plugin install --harness claude"
#: Every id a complete install for both harnesses reports, in order.
ALL_IDS = [
    "kmctl.version",
    "dep.uv",
    "dep.git",
    "dep.apm",
    "dep.claude",
    "dep.agy",
    "init.okf",
    "init.docs",
    "kmctl.harness",
    "claude.lock",
    "claude.files",
    "claude.okf-skills",
    "claude.hook",
    "claude.okf-mcp",
    "claude.old-plugin",
    "antigravity.lock",
    "antigravity.files",
    "antigravity.okf-skills",
    "antigravity.plugin",
    "antigravity.hook",
    "antigravity.apm-hooks",
    "antigravity.okf-mcp",
    "antigravity.trust",
]
#: Ids that appear only in some states: no install here, or with --online.
OTHER_IDS = ["claude.scope", "antigravity.okf-mcp-url"]


# Building an installed repository ----------------------------------------------


def _sha(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()


def _package(harnesses: tuple[str, ...]) -> tuple[dict[str, str], list[str]]:
    """kmctl's files as APM deploys them for ``harnesses``, and the folders the lock also lists."""
    files, folders = {}, []
    for harness in harnesses:
        top = FOLDERS[harness]
        for skill in SKILL_NAMES:
            folders.append(f"{top}/skills/{skill}")
            files[f"{top}/skills/{skill}/SKILL.md"] = (
                SKILLS / skill / "SKILL.md"
            ).read_text()
        files[f"{top}/rules/okf-bundle.md"] = "a rule\n"
        if harness == "claude":
            files[f"{top}/agents/kmctl-auditor.md"] = "an agent\n"
    return files, folders


def _okf(harnesses: tuple[str, ...]) -> tuple[dict[str, str], list[str]]:
    """okf's skills as APM deploys them for ``harnesses``."""
    files = {f"{FOLDERS[h]}/skills/okf/SKILL.md": "okf\n" for h in harnesses}
    return files, [f"{FOLDERS[h]}/skills/okf" for h in harnesses]


def _lock(harnesses: tuple[str, ...], ref: str = REF) -> str:
    """An apm.lock.yaml as APM 0.33.0 writes it for kmctl's package and okf-skills."""
    kmctl = {
        "repo_url": "JasperHG90/Knowledge-management",
        "name": "kmctl",
        "resolved_ref": ref,
        "virtual_path": "apm",
    }
    okf = {"repo_url": "scaccogatto/okf-skills", "name": "okf", "resolved_ref": "a8b9"}
    deps = []
    for entry, (files, folders) in (
        (kmctl, _package(harnesses)),
        (okf, _okf(harnesses)),
    ):
        deps.append(
            {
                **entry,
                "deployed_files": sorted([*files, *folders]),
                "deployed_file_hashes": {p: _sha(t) for p, t in files.items()},
            }
        )
    return yaml.safe_dump({"lockfile_version": "1", "dependencies": deps})


def _apm_writes(harnesses: tuple[str, ...], scope: str) -> dict[str, str]:
    """What the fake ``apm install`` writes, relative to where APM runs."""
    lock = ".apm/apm.lock.yaml" if scope == "user" else "apm.lock.yaml"
    return {
        **_package(harnesses)[0],
        **_okf(harnesses)[0],
        lock: _lock(harnesses),
        f"{OKF_AGENTS}/bundle-weaver.md": AGENT.format(name="bundle-weaver"),
        f"{OKF_AGENTS}/event-analyzer.md": AGENT.format(name="event-analyzer"),
    }


@dataclass(frozen=True)
class Setup:
    """A scratch repository, HOME and fake tools.

    Attributes
    ----------
    repo : Path
        The repository, also the working folder.
    home : Path
        HOME; CLAUDE_CONFIG_DIR is its .claude folder.
    fakes : FakeTools
        uvx, uv, claude, git and agy, alone on PATH.
    """

    repo: Path
    home: Path
    fakes: FakeTools

    def remove(self, tool: str) -> None:
        """Take ``tool`` off PATH."""
        (self.fakes.bin / tool).unlink()


@pytest.fixture
def setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Setup:
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home / ".claude"))
    monkeypatch.setenv("XDG_DATA_HOME", str(home / ".local" / "share"))
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.chdir(repo)
    fakes = FakeTools(tmp_path, tools=("uvx", "uv", "claude", "git", "agy"))
    monkeypatch.setenv("PATH", str(fakes.bin))
    return Setup(repo, home, fakes)


def _kmctl(*args: str) -> Result:
    return CliRunner().invoke(app, list(args))


def _install(
    s: Setup, harnesses: tuple[str, ...] = ("claude", "antigravity"), *flags: str
) -> Result:
    """Run ``kmctl plugin install`` for ``harnesses``; fail the test unless it exits 0."""
    scope = "user" if "user" in flags else "project"
    s.fakes.on("uvx", "apm install", write=_apm_writes(harnesses, scope))
    result = _kmctl("plugin", "install", "--harness", ",".join(harnesses), *flags)
    assert result.exit_code == 0, result.output
    return result


def _trust(s: Setup, *folders: Path) -> None:
    """Write agy's settings, trusting ``folders`` (by default the repository)."""
    path = s.home / ".gemini" / "antigravity-cli" / "settings.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    trusted = [str(f) for f in (folders or (s.repo.resolve(),))]
    path.write_text(json.dumps({"trustedWorkspaces": trusted}))


def _complete(s: Setup, harnesses: tuple[str, ...] = ("claude", "antigravity")) -> None:
    """Install ``harnesses``, run kmctl init and trust the folder."""
    _install(s, harnesses)
    assert _kmctl("init").exit_code == 0
    _trust(s)


@pytest.fixture
def complete(setup: Setup) -> Setup:
    """A repository with a complete install for both harnesses."""
    _complete(setup)
    return setup


def _doctor(*args: str) -> tuple[Result, dict]:
    """Run ``kmctl doctor --json`` and return the result and the parsed object."""
    result = _kmctl("doctor", "--json", *args)
    assert result.exit_code in (0, 1), result.output
    return result, json.loads(result.stdout)


def _by_id(data: dict) -> dict[str, dict]:
    return {c["id"]: c for c in data["checks"]}


def _fail_line(text: str, cid: str) -> str:
    """The fail line of check ``cid`` in doctor's text output."""
    lines = [line for line in text.splitlines() if line.startswith(f"fail {cid}: ")]
    assert lines, text
    return lines[0]


# r1: a complete install is all ok ------------------------------------------------


def test_all_ok_for_claude_and_antigravity(complete: Setup) -> None:
    result = _kmctl("doctor")

    assert result.exit_code == 0, result.output
    lines = result.stdout.splitlines()
    assert [line.split(":")[0].split()[-1] for line in lines] == ALL_IDS
    assert all(line.startswith("ok   ") for line in lines), result.stdout
    assert result.stderr == ""


def test_all_ok_for_claude_alone(setup: Setup) -> None:
    _complete(setup, ("claude",))

    result = _kmctl("doctor")

    assert result.exit_code == 0, result.output
    assert not re.search(
        r"^\S+\s+(antigravity\.|dep\.agy)", result.stdout, re.MULTILINE
    )


def test_all_ok_function_returns_results_without_the_cli(complete: Setup) -> None:
    result = doctor.run_doctor(complete.repo)

    assert result.ok
    assert [c.id for c in result.checks] == ALL_IDS
    assert all(c.fix is None for c in result.checks)


def test_all_ok_with_another_okf_mcp_server(complete: Setup) -> None:
    """An okf server under another name is kept by install, so doctor accepts it too."""
    path = complete.repo / ".mcp.json"
    path.write_text(
        json.dumps({"mcpServers": {"okf": {"command": "uv", "args": ["okf_mcp.py"]}}})
    )

    result, data = _doctor()

    assert result.exit_code == 0, result.output
    assert "'okf'" in _by_id(data)["claude.okf-mcp"]["detail"]


# r2: a broken piece fails with its name and its fix --------------------------------


def _edit(path: Path, old: str, new: str) -> None:
    path.write_text(path.read_text().replace(old, new))


SKILL = f".claude/skills/{SKILL_NAMES[0]}/SKILL.md"
PLUGIN = ".agents/plugins/kmctl"
BREAKS: dict[str, tuple[Callable[[Path], None], str, str, str]] = {
    # case: (how to break it, the check, what the line names, the fix)
    "skill": (
        lambda r: (r / SKILL).unlink(),
        "claude.files",
        f"{SKILL} is missing",
        CLAUDE_FIX,
    ),
    "skill-folder": (
        lambda r: shutil.rmtree(r / ".agents" / "skills" / SKILL_NAMES[-1]),
        "antigravity.files",
        f".agents/skills/{SKILL_NAMES[-1]} is missing",
        AG_FIX,
    ),
    "hash": (
        lambda r: (r / f".agents/skills/{SKILL_NAMES[0]}/SKILL.md").write_text("e\n"),
        "antigravity.files",
        f".agents/skills/{SKILL_NAMES[0]}/SKILL.md differs from apm.lock.yaml",
        AG_FIX,
    ),
    "okf-skill": (
        lambda r: (r / ".claude/skills/okf/SKILL.md").unlink(),
        "claude.okf-skills",
        ".claude/skills/okf/SKILL.md is missing",
        CLAUDE_FIX,
    ),
    "hook": (
        lambda r: (r / ".claude/settings.json").write_text("{}"),
        "claude.hook",
        "SessionStart hook is missing from .claude/settings.json",
        CLAUDE_FIX,
    ),
    "hook-changed": (
        lambda r: _edit(r / ".claude/settings.json", '"timeout": 10', '"timeout": 99'),
        "claude.hook",
        "is not the one this kmctl writes",
        "run kmctl plugin update --harness claude",
    ),
    "plugin-file-missing": (
        lambda r: (r / PLUGIN / "plugin.json").unlink(),
        "antigravity.plugin",
        f"{PLUGIN}/plugin.json is missing",
        AG_FIX,
    ),
    "plugin-file-extra": (
        lambda r: (r / PLUGIN / "agents" / "extra.md").write_text("x\n"),
        "antigravity.plugin",
        f"{PLUGIN}/agents/extra.md is not one kmctl writes",
        AG_FIX,
    ),
    "plugin-file-edited": (
        lambda r: (r / PLUGIN / "agents" / "kmctl-auditor.md").write_text("x\n"),
        "antigravity.plugin",
        f"{PLUGIN}/agents/kmctl-auditor.md differs from what this kmctl writes",
        AG_FIX,
    ),
    "plugin-folder": (
        lambda r: shutil.rmtree(r / PLUGIN),
        "antigravity.plugin",
        f"{PLUGIN}/ is missing",
        AG_FIX,
    ),
    "antigravity-hook": (
        lambda r: (r / PLUGIN / "hooks.json").write_text("{}\n"),
        "antigravity.hook",
        f"{PLUGIN}/hooks.json",
        AG_FIX,
    ),
    "antigravity-mcp": (
        lambda r: (r / PLUGIN / "mcp_config.json").unlink(),
        "antigravity.okf-mcp",
        f"{PLUGIN}/mcp_config.json is missing",
        AG_FIX,
    ),
    "apm-modules": (
        lambda r: shutil.rmtree(r / "apm_modules"),
        "antigravity.plugin",
        "apm_modules/ is missing",
        AG_FIX,
    ),
    "mcp": (
        lambda r: (r / ".mcp.json").write_text("{}"),
        "claude.okf-mcp",
        "okf's MCP server okf-bundle is missing from .mcp.json",
        CLAUDE_FIX,
    ),
    "mcp-changed": (
        lambda r: _edit(r / ".mcp.json", '"sh"', '"bash"'),
        "claude.okf-mcp",
        "okf-bundle in .mcp.json is not the one this kmctl writes",
        "run kmctl plugin update --harness claude",
    ),
    "lock": (
        lambda r: (r / "apm.lock.yaml").unlink(),
        "claude.lock",
        "apm.lock.yaml is missing",
        CLAUDE_FIX,
    ),
    "lock-antigravity": (
        lambda r: (r / "apm.lock.yaml").unlink(),
        "antigravity.lock",
        "apm.lock.yaml is missing",
        AG_FIX,
    ),
    "ref": (
        lambda r: _edit(r / "apm.lock.yaml", REF, "v0.0.1"),
        "claude.lock",
        f"apm.lock.yaml has kmctl's package at v0.0.1, this kmctl is {REF[1:]}",
        "run kmctl plugin update --harness claude",
    ),
    "ref-antigravity": (
        lambda r: _edit(r / "apm.lock.yaml", REF, "v0.0.1"),
        "antigravity.lock",
        "at v0.0.1",
        "run kmctl plugin update --harness antigravity",
    ),
    "okf": (
        lambda r: shutil.rmtree(r / ".okf"),
        "init.okf",
        ".okf/index.md is missing",
        "run kmctl init",
    ),
    "docs": (
        lambda r: shutil.rmtree(r / "docs"),
        "init.docs",
        "docs/README.md is missing",
        "run kmctl init",
    ),
}


@pytest.mark.parametrize("case", BREAKS)
def test_broken_piece_fails_naming_it_and_its_fix(complete: Setup, case: str) -> None:
    breaks, cid, piece, fix = BREAKS[case]
    breaks(complete.repo)

    result = _kmctl("doctor")

    assert result.exit_code == 1, result.output
    line = _fail_line(result.stdout, cid)
    assert piece in line, line
    assert line.endswith(f"; {fix}"), line


def test_broken_lock_and_hook_still_name_the_harness(complete: Setup) -> None:
    """apm.yml's targets keep the harness found when the lock and the hook are both gone."""
    (complete.repo / "apm.lock.yaml").unlink()
    (complete.repo / ".claude" / "settings.json").write_text("{}")

    result = _kmctl("doctor")

    assert result.exit_code == 1
    _fail_line(result.stdout, "claude.lock")
    _fail_line(result.stdout, "claude.hook")
    assert "fail kmctl.harness" not in result.stdout


def test_broken_each_problem_is_listed_once_capped(complete: Setup) -> None:
    for skill in SKILL_NAMES:
        (complete.repo / ".claude" / "skills" / skill / "SKILL.md").unlink()

    line = _fail_line(_kmctl("doctor").stdout, "claude.files")

    assert line.count(" is missing") == doctor.SHOWN_PROBLEMS
    assert f"and {len(SKILL_NAMES) - doctor.SHOWN_PROBLEMS} more" in line


def test_broken_settings_json_is_named(complete: Setup) -> None:
    (complete.repo / ".claude" / "settings.json").write_text("not json")

    line = _fail_line(_kmctl("doctor").stdout, "claude.hook")

    assert ".claude/settings.json is not a JSON object" in line


# r3: dependencies ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("tool", "cid", "hint"),
    [
        ("uv", "dep.uv", "install uv"),
        ("git", "dep.git", "install git"),
        ("claude", "dep.claude", "install Claude Code"),
        ("agy", "dep.agy", "install the Antigravity CLI"),
    ],
)
def test_dependency_missing_fails_with_install_hint(
    complete: Setup, tool: str, cid: str, hint: str
) -> None:
    complete.remove(tool)

    result = _kmctl("doctor")

    assert result.exit_code == 1
    line = _fail_line(result.stdout, cid)
    assert f"{tool} is not on PATH; {hint}" in line


def test_dependency_missing_uv_fails_apm_too(complete: Setup) -> None:
    complete.remove("uv")

    line = _fail_line(_kmctl("doctor").stdout, "dep.apm")

    assert line.endswith("; install uv (https://docs.astral.sh/uv/)")


def test_dependency_apm_not_in_uv_cache_names_the_fetch(complete: Setup) -> None:
    complete.fakes.on("uv", "apm --version", exit=2, stderr="offline\n")

    line = _fail_line(_kmctl("doctor").stdout, "dep.apm")

    assert "APM 0.33.0 is not in uv's cache" in line
    assert line.endswith(
        "; run uvx --from apm-cli==0.33.0 apm --version, which downloads it once"
    )


def test_dependency_apm_reports_its_version(complete: Setup) -> None:
    complete.fakes.on("uv", "apm --version", stdout="Agent Package Manager 0.33.0\n")

    _, data = _doctor()

    assert _by_id(data)["dep.apm"]["detail"].endswith("Agent Package Manager 0.33.0")


def test_dependency_of_a_harness_not_installed_is_not_checked(setup: Setup) -> None:
    _complete(setup, ("claude",))
    setup.remove("agy")

    result = _kmctl("doctor")

    assert result.exit_code == 0, result.output
    assert "dep.agy" not in result.stdout and "antigravity" not in result.stdout


def test_dependency_claude_not_checked_for_antigravity_alone(setup: Setup) -> None:
    _complete(setup, ("antigravity",))
    setup.remove("claude")

    result = _kmctl("doctor")

    assert result.exit_code == 0, result.output
    assert "dep.claude" not in result.stdout and "claude." not in result.stdout


def test_dependency_no_harness_fails_once_with_install(setup: Setup) -> None:
    assert _kmctl("init").exit_code == 0

    result = _kmctl("doctor")

    assert result.exit_code == 1
    fails = [line for line in result.stdout.splitlines() if line.startswith("fail")]
    assert fails == [
        (
            "fail kmctl.harness: no kmctl harness in this repository; run kmctl "
            "plugin install --harness claude"
        )
    ]


# r3b: user scope -------------------------------------------------------------------


def _user_install(s: Setup) -> None:
    """Install claude at user scope; the fake claude cannot add the MCP server, so write it."""
    _install(s, ("claude",), "--scope", "user")
    plugin.user_mcp_file().write_text(
        json.dumps({"mcpServers": {"okf-bundle": plugin.okf_mcp_server()}})
    )


def test_user_scope_install_passes(setup: Setup) -> None:
    _user_install(setup)

    result = _kmctl("doctor", "--scope", "user")

    assert result.exit_code == 0, result.output
    assert "init." not in result.stdout
    assert "ok   kmctl.harness: installed for claude at user scope" in result.stdout


@pytest.mark.parametrize(
    ("breaks", "cid"),
    [
        (lambda h: (h / ".claude" / "settings.json").write_text("{}"), "claude.hook"),
        (
            lambda h: shutil.rmtree(h / ".claude" / "skills" / SKILL_NAMES[0]),
            "claude.files",
        ),
        (lambda h: _edit(h / ".apm" / "apm.lock.yaml", REF, "v0.0.1"), "claude.lock"),
        (lambda h: plugin.user_mcp_file().write_text("{}"), "claude.okf-mcp"),
    ],
    ids=["hook", "skill", "ref", "mcp"],
)
def test_user_scope_broken_fails_with_scope_fix(
    setup: Setup, breaks: Callable[[Path], object], cid: str
) -> None:
    _user_install(setup)
    breaks(setup.home)

    result = _kmctl("doctor", "--scope", "user")

    assert result.exit_code == 1
    assert _fail_line(result.stdout, cid).endswith("--harness claude --scope user")


def test_user_scope_seen_from_a_project_is_ok(setup: Setup) -> None:
    _user_install(setup)
    assert _kmctl("init").exit_code == 0

    result = _kmctl("doctor")

    assert result.exit_code == 0, result.output
    assert (
        "ok   claude.scope: installed at user scope; run kmctl doctor --scope user"
        in result.stdout
    )
    assert "plugin install" not in result.stdout


def test_user_scope_none_fails_with_user_install(setup: Setup) -> None:
    result = _kmctl("doctor", "--scope", "user")

    assert result.exit_code == 1
    assert _fail_line(result.stdout, "kmctl.harness").endswith(
        "; run kmctl plugin install --harness claude --scope user"
    )


# r4: --json ------------------------------------------------------------------------


def test_json_shape_and_ids(complete: Setup) -> None:
    result, data = _doctor()

    assert result.exit_code == 0
    assert set(data) == {"ok", "checks"} and data["ok"] is True
    assert [c["id"] for c in data["checks"]] == ALL_IDS
    for check in data["checks"]:
        assert set(check) == {"id", "harness", "ok", "detail", "fix"}
        assert check["fix"] is None and check["detail"]
    harness = {c["id"]: c["harness"] for c in data["checks"]}
    assert harness["dep.uv"] is None and harness["dep.claude"] == "claude"
    assert harness["dep.agy"] == "antigravity"
    assert harness["claude.hook"] == "claude"
    assert harness["antigravity.plugin"] == "antigravity"


def test_json_exit_code_and_fix_match_the_text(complete: Setup) -> None:
    (complete.repo / ".claude" / "settings.json").write_text("{}")

    result, data = _doctor()
    text = _kmctl("doctor")

    assert result.exit_code == text.exit_code == 1
    assert data["ok"] is False
    hook = _by_id(data)["claude.hook"]
    assert hook["ok"] is False and hook["fix"] == CLAUDE_FIX
    assert f"fail claude.hook: {hook['detail']}; {hook['fix']}" in text.stdout


def test_json_ids_are_the_documented_ones(complete: Setup) -> None:
    """Every id doctor can print is in the help and in the commands reference."""
    help_text = " ".join(plain(_kmctl("doctor", "--help").stdout).split())
    reference = COMMANDS.read_text()

    for cid in ALL_IDS + OTHER_IDS:
        short = (
            cid.split(".", 1)[1] if cid.startswith(("claude.", "antigravity.")) else cid
        )
        assert short in help_text, cid
        assert f"`{cid}`" in reference, cid


# r5: read only and offline -----------------------------------------------------------


def _snapshot(*roots: Path) -> dict[str, tuple[bytes | None, int]]:
    """Every file's bytes and every path's mtime under ``roots``."""
    found: dict[str, tuple[bytes | None, int]] = {}
    for root in roots:
        for path in [root, *root.rglob("*")]:
            stat = path.lstat()
            data = (
                path.read_bytes() if path.is_file() and not path.is_symlink() else None
            )
            found[str(path)] = (data, stat.st_mtime_ns)
    return found


def test_readonly_writes_nothing_connects_nowhere_runs_one_command(
    complete: Setup, monkeypatch: pytest.MonkeyPatch
) -> None:
    before = _snapshot(complete.repo, complete.home)
    calls_before = len(complete.fakes.calls())
    connects: list[object] = []

    def refuse(self: socket.socket, address: object) -> None:
        connects.append(address)
        raise OSError("doctor must not connect")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket.socket, "connect_ex", refuse)

    result = _kmctl("doctor")

    assert result.exit_code == 0, result.output
    assert _snapshot(complete.repo, complete.home) == before
    assert connects == []
    runs = complete.fakes.calls()[calls_before:]
    assert [(c.tool, c.args) for c in runs] == [("uv", list(doctor.APM_VERSION_ARGS))]
    assert doctor.APM_VERSION_ARGS == (
        "tool",
        "run",
        "--offline",
        "--from",
        "apm-cli==0.33.0",
        "apm",
        "--version",
    )


def test_readonly_broken_install_writes_nothing(complete: Setup) -> None:
    shutil.rmtree(complete.repo / PLUGIN)
    (complete.repo / "apm.lock.yaml").unlink()
    before = _snapshot(complete.repo, complete.home)

    assert _kmctl("doctor").exit_code == 1

    assert _snapshot(complete.repo, complete.home) == before


@respx.mock
def test_readonly_online_alone_fetches_the_mcp_script(complete: Setup) -> None:
    route = respx.head(plugin.okf_mcp_url()).mock(return_value=httpx.Response(200))

    _, data = _doctor()
    assert route.call_count == 0
    assert "antigravity.okf-mcp-url" not in _by_id(data)

    online, data = _doctor("--online")

    assert online.exit_code == 0, online.output
    assert route.call_count == 1
    assert _by_id(data)["antigravity.okf-mcp-url"]["ok"] is True


@respx.mock
def test_readonly_online_fetch_failure_fails(complete: Setup) -> None:
    respx.head(plugin.okf_mcp_url()).mock(return_value=httpx.Response(404))

    result = _kmctl("doctor", "--online")

    assert result.exit_code == 1
    assert "HTTP 404" in _fail_line(result.stdout, "antigravity.okf-mcp-url")


def test_readonly_doctor_module_prints_and_exits_nothing() -> None:
    """doctor.py neither prints, exits nor calls a writer; the CLI renders its results."""
    tree = ast.parse(Path(doctor.__file__).read_text())
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    imported = {
        a.name.split(".")[0]
        for n in ast.walk(tree)
        if isinstance(n, ast.Import)
        for a in n.names
    } | {
        (n.module or "").split(".")[0]
        for n in ast.walk(tree)
        if isinstance(n, ast.ImportFrom)
    }

    assert not names & {"print", "exit", "quit", "SystemExit", "open"}
    assert not attrs & {
        "exit",
        "echo",
        "write",
        "write_text",
        "write_bytes",
        "mkdir",
        "unlink",
        "rmtree",
        "touch",
    }
    assert not imported & {"typer", "sys", "click", "os"}


# r6: help, docs, and plugin status folded into doctor ---------------------------------


def test_doctor_help_names_checks_exit_codes_and_flags() -> None:
    result = _kmctl("doctor", "--help")
    text = " ".join(plain(result.stdout).split())

    assert result.exit_code == 0
    for words in (
        "--json",
        "--online",
        "--scope",
        "--path",
        "Exit 0 when every check is ok, 1 when any fails, 2 for a usage error",
        "writes nothing and uses no network unless --online",
        "uv tool run --offline --from apm-cli==0.33.0 apm --version",
    ):
        assert words in text, words


def test_doctor_install_and_update_end_with_next_doctor(setup: Setup) -> None:
    install = _install(setup)
    update = _kmctl("plugin", "update", "--harness", "claude,antigravity")

    assert update.exit_code == 0, update.output
    for result in (install, update):
        last = result.stdout.strip().splitlines()[-1]
        assert last.startswith("Next: ") and last.endswith(", then kmctl doctor")


def test_doctor_user_install_next_names_the_scope(setup: Setup) -> None:
    result = _install(setup, ("claude",), "--scope", "user")

    assert result.stdout.strip().splitlines()[-1].endswith("kmctl doctor --scope user")


def test_doctor_replaces_plugin_status() -> None:
    result = _kmctl("plugin", "status")

    assert result.exit_code == 2
    assert "No such command" in plain(result.output)
    assert sorted(get_command(app).commands["plugin"].commands) == ["install", "update"]


def test_docs_name_doctor_and_not_plugin_status() -> None:
    pages = [ROOT / "README.md", *(ROOT / "docs").rglob("*.md")]

    for page in pages:
        assert "plugin status" not in page.read_text(), page
    reference = " ".join(COMMANDS.read_text().split())
    assert "### `kmctl doctor`" in COMMANDS.read_text()
    for words in ("--online", "--json", "--scope", "Exit code: 0", "1 when"):
        assert words in reference, words


def test_docs_install_how_to_ends_with_doctor() -> None:
    text = INSTALL_HOW_TO.read_text()

    assert "kmctl doctor" in text
    assert "Next: start a new Claude Code session, then kmctl doctor" in text


# r6b: the old claude plugin and Antigravity trust ---------------------------------------


@pytest.mark.parametrize(
    ("enabled", "file", "fix"),
    [
        ([plugin.OLD_PLUGIN], "settings.json", CLAUDE_FIX),
        ([plugin.OLD_PLUGIN], "settings.local.json", CLAUDE_FIX),
        (
            [plugin.OLD_PLUGIN, "okf@scaccogatto"],
            "settings.json",
            CLAUDE_FIX,
        ),
        (
            ["okf@scaccogatto"],
            "settings.json",
            "run claude plugin uninstall okf@scaccogatto --scope project",
        ),
        (
            ["okf@scaccogatto"],
            "settings.local.json",
            "run claude plugin uninstall okf@scaccogatto --scope local",
        ),
    ],
)
def test_old_plugin_enabled_fails_with_its_fix(
    complete: Setup, enabled: list[str], file: str, fix: str
) -> None:
    """The install removes kmctl@kmctl; an okf plugin on its own needs its own uninstall."""
    path = complete.repo / ".claude" / file
    data = json.loads(path.read_text()) if path.is_file() else {}
    path.write_text(
        json.dumps({**data, "enabledPlugins": dict.fromkeys(enabled, True)})
    )
    calls = len(complete.fakes.calls())

    result = _kmctl("doctor")

    assert result.exit_code == 1
    line = _fail_line(result.stdout, "claude.old-plugin")
    assert all(f"{name} in .claude/{file}" in line for name in enabled)
    assert line.endswith(f"; {fix}")
    assert [c.tool for c in complete.fakes.calls()[calls:]] == ["uv"]


def test_old_okf_plugin_alone_does_not_mark_the_claude_harness(setup: Setup) -> None:
    """An okf plugin the user chose is not a kmctl install."""
    assert _kmctl("init").exit_code == 0
    (setup.repo / ".claude").mkdir()
    (setup.repo / ".claude" / "settings.json").write_text(
        json.dumps({"enabledPlugins": {"okf@scaccogatto": True}})
    )

    assert "fail claude.old-plugin" not in _kmctl("doctor").stdout


def test_old_plugin_disabled_passes(complete: Setup) -> None:
    path = complete.repo / ".claude" / "settings.json"
    data = json.loads(path.read_text())
    path.write_text(json.dumps({**data, "enabledPlugins": {plugin.OLD_PLUGIN: False}}))

    assert _kmctl("doctor").exit_code == 0


def test_old_plugin_at_user_scope_names_the_scope(setup: Setup) -> None:
    _user_install(setup)
    path = setup.home / ".claude" / "settings.json"
    data = json.loads(path.read_text())
    path.write_text(json.dumps({**data, "enabledPlugins": {"okf@scaccogatto": True}}))

    result = _kmctl("doctor", "--scope", "user")

    assert _fail_line(result.stdout, "claude.old-plugin").endswith(
        "; run claude plugin uninstall okf@scaccogatto --scope user"
    )


def test_old_plugin_alone_marks_the_claude_harness(setup: Setup) -> None:
    """A repository with only the old plugin is told to reinstall, not that kmctl is absent."""
    assert _kmctl("init").exit_code == 0
    (setup.repo / ".claude").mkdir()
    (setup.repo / ".claude" / "settings.json").write_text(
        json.dumps({"enabledPlugins": {plugin.OLD_PLUGIN: True}})
    )

    result = _kmctl("doctor")

    _fail_line(result.stdout, "claude.old-plugin")
    assert "fail kmctl.harness" not in result.stdout


@pytest.mark.parametrize(
    "trusted", [None, "other"], ids=["no-settings", "other-folder"]
)
def test_trust_missing_fails_with_trust_fix(
    complete: Setup, trusted: str | None, tmp_path: Path
) -> None:
    settings = complete.home / ".gemini" / "antigravity-cli" / "settings.json"
    if trusted is None:
        settings.unlink()
    else:
        _trust(complete, tmp_path / trusted)

    result = _kmctl("doctor")

    assert result.exit_code == 1
    line = _fail_line(result.stdout, "antigravity.trust")
    assert "trustedWorkspaces" in line
    assert line.endswith("; open this folder in Antigravity and trust it")


def test_trust_not_checked_without_agy(complete: Setup) -> None:
    complete.remove("agy")
    (complete.home / ".gemini" / "antigravity-cli" / "settings.json").unlink()

    result = _kmctl("doctor")

    assert "antigravity.trust" not in result.stdout
    _fail_line(result.stdout, "dep.agy")


# r7: a real install --------------------------------------------------------------------


@pytest.mark.integration
def test_doctor_after_a_real_install_exits_zero(
    consumer: Path, served: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The real APM 0.33.0 installs both harnesses; doctor then passes, offline.

    claude and agy are fakes on PATH: doctor only looks them up, and the
    install's claude plugin list must not reach the real claude.
    """
    fakes = FakeTools(tmp_path / "fakes", tools=("claude", "agy"))
    monkeypatch.setenv("PATH", f"{fakes.bin}:{os.environ['PATH']}")
    home = Path(os.environ["HOME"])
    trust = home / ".gemini" / "antigravity-cli" / "settings.json"
    trust.parent.mkdir(parents=True)
    trust.write_text(json.dumps({"trustedWorkspaces": [str(consumer.resolve())]}))

    install = _kmctl(
        "plugin", "install", "--harness", "claude,antigravity", "--source", served
    )
    init = _kmctl("init")
    result = _kmctl("doctor")

    assert install.exit_code == 0, install.output
    assert init.exit_code == 0, init.output
    assert result.exit_code == 0, result.output
    assert re.findall(r"^\S+\s+([\w.-]+):", result.stdout, re.MULTILINE) == ALL_IDS
    assert [c.tool for c in fakes.calls()] == ["claude"]
    assert antigravity.plugin_problems(consumer) == []


# antigravity-rules r3: kmctl's rules live in the plugin folder -------------------


def test_antigravity_rules_absent_from_agents_rules_pass(complete: Setup) -> None:
    assert not (complete.repo / ".agents/rules/okf-bundle.md").exists()

    _, data = _doctor()

    assert _by_id(data)["antigravity.files"]["ok"], data


@pytest.mark.parametrize(
    ("change", "said"),
    [
        (lambda f: (f / "rules/okf-bundle.md").unlink(), "is missing"),
        (lambda f: (f / "rules/okf-bundle.md").write_text("e\n"), "differs"),
        (lambda f: (f / "rules/extra.md").write_text("e\n"), "is not one kmctl"),
    ],
)
def test_antigravity_rule_changes_fail_the_plugin_check(
    complete: Setup, change: Callable[[Path], object], said: str
) -> None:
    change(complete.repo / ".agents" / "plugins" / "kmctl")

    result, data = _doctor()

    check = _by_id(data)["antigravity.plugin"]
    assert not check["ok"]
    assert "rules/" in check["detail"] and said in check["detail"]
    assert check["fix"] == AG_FIX
    assert result.exit_code == 1


# antigravity-okf-stop-hook r3: APM's okf Stop handler and kmctl's hooks -----------


def test_okf_stop_apm_handler_fails_its_check(complete: Setup) -> None:
    path = complete.repo / ".agents" / "hooks.json"
    path.write_text(
        json.dumps(
            {
                "apm": {
                    "Stop": [
                        {
                            "command": "bash .agents/hooks/okf-skills/hooks/okf-stop-check.sh"
                        }
                    ]
                }
            }
        )
    )

    result, data = _doctor()

    check = _by_id(data)["antigravity.apm-hooks"]
    assert not check["ok"]
    assert ".agents/hooks.json" in check["detail"]
    assert check["fix"] == AG_FIX
    assert result.exit_code == 1


def test_okf_stop_apm_hooks_without_okf_pass(complete: Setup) -> None:
    path = complete.repo / ".agents" / "hooks.json"
    path.write_text(json.dumps({"theirs": {"Stop": [{"command": "echo hi"}]}}))

    _, data = _doctor()

    assert _by_id(data)["antigravity.apm-hooks"]["ok"]


def test_okf_stop_missing_from_plugin_hooks_fails_antigravity_hook(
    complete: Setup,
) -> None:
    path = complete.repo / ".agents" / "plugins" / "kmctl" / "hooks.json"
    data = json.loads(path.read_text())
    del data["kmctl-okf-stop"]
    path.write_text(json.dumps(data, indent=2) + "\n")

    _, checks = _doctor()

    assert not _by_id(checks)["antigravity.hook"]["ok"]


# antigravity-okf-stop-hook-reviewer-f4: doctor reads .agents/hooks.json as install does


@pytest.mark.parametrize(
    "content", [b"not json okf-stop-check.sh", b"[]", b"\xff\xfe okf-stop-check.sh"]
)
def test_apm_hooks_unparsable_names_the_file_and_the_repair(
    complete: Setup, content: bytes
) -> None:
    (complete.repo / ".agents" / "hooks.json").write_bytes(content)

    result, data = _doctor()

    check = _by_id(data)["antigravity.apm-hooks"]
    assert not check["ok"]
    assert ".agents/hooks.json is not a JSON object" in check["detail"]
    assert check["fix"] == f"repair .agents/hooks.json by hand, then {AG_FIX}"
    assert result.exit_code == 1


def test_apm_hooks_mention_outside_a_handler_passes(complete: Setup) -> None:
    path = complete.repo / ".agents" / "hooks.json"
    path.write_text(
        json.dumps(
            {"theirs": {"Stop": [{"command": "echo hi"}]}, "note": "okf-stop-check.sh"}
        )
    )

    _, data = _doctor()

    assert _by_id(data)["antigravity.apm-hooks"]["ok"]


def test_apm_hooks_docs_show_the_check_and_the_note() -> None:
    how_to = (
        ROOT / "docs" / "how-to" / "install-the-plugin-and-the-ci-action.md"
    ).read_text()
    assert (
        "ok   antigravity.apm-hooks: .agents/hooks.json runs no okf Stop check"
        in how_to
    )
    note = next(
        line
        for line in how_to.splitlines()
        if line.startswith("note: wrote .agents/plugins/kmctl/")
    )
    assert "okf's Stop check" in note
    assert "not a JSON object" in COMMANDS.read_text()
