"""kmctl's OpenCode pieces (ADR 0024).

APM installs kmctl's and okf's skills into .agents/skills/, copies the agents
into .opencode/agents/ in Claude Code's format and writes okf's MCP server
into opencode.json; kmctl plugin patch rewrites the agents into OpenCode's
format and writes the rules, their instructions entry and the briefing
plugin. No test here without a marker runs the real APM: ``_apm_install``
writes what APM 0.33.0 leaves, and ``FakeTools`` stands in for uvx, uv,
claude and git. The briefing plugin runs under node with a stub ``ctx``
(skipped without node). The ``integration`` tests run the real APM 0.33.0
against this tree served from a local git server, and the real OpenCode when
it is on PATH.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import socket
import subprocess
import time
from importlib.metadata import version
from pathlib import Path

import pytest
import yaml
from conftest import apm_install, plain
from fixtures.fake_tools import FakeTools
from jsonschema import Draft202012Validator
from typer.testing import CliRunner, Result

from kmctl import app, doctor, opencode, plugin
from kmctl.kinds import schema
from kmctl.okf import front_matter

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "apm" / ".apm" / "skills"
SKILL_NAMES = sorted(p.name for p in SKILLS.iterdir() if p.is_dir())
AUDITOR = ROOT / "apm" / ".apm" / "agents" / "kmctl-auditor.md"
INSTRUCTIONS = ROOT / "apm" / "claude" / ".apm" / "instructions"
RULE_NAMES = sorted(
    p.name.removesuffix(".instructions.md") for p in INSTRUCTIONS.glob("*.md")
)
DECISIONS = ROOT / ".okf" / "decisions"
MANIFESTO = ROOT / ".okf" / "manifesto.md"
COMMANDS = ROOT / "docs" / "reference" / "commands.md"
INSTALL_HOW_TO = ROOT / "docs" / "how-to" / "install-kmctl-with-apm.md"
README = ROOT / "README.md"
REF = f"v{version('kmctl')}"
OKF_AGENTS = "apm_modules/scaccogatto/okf-skills/agents"
AGENT_NAMES = ["bundle-weaver", "event-analyzer", "kmctl-auditor"]
AGENT_PATHS = [f".opencode/agents/{n}.md" for n in AGENT_NAMES]
RULE_PATHS = [f".opencode/rules/{n}.md" for n in RULE_NAMES]
PLUGIN_PATH = ".opencode/plugins/kmctl.js"
NODE = shutil.which("node")
OPENCODE = shutil.which("opencode")
#: okf's two agents with the front matter they have at the pinned commit.
BUNDLE_WEAVER = """\
---
name: bundle-weaver
description: >-
  Fold event analyses into an OKF knowledge bundle in deterministic sequence.
model: sonnet
effort: high
tools: Read, Write, Edit, Bash, Grep, Glob
color: green
---

You fold event analyses into the bundle.
"""
EVENT_ANALYZER = """\
---
name: event-analyzer
description: >-
  Analyze a single repository history event.
model: haiku
effort: medium
tools: Bash, Read, Write
color: blue
---

You analyze one event.
"""
OKF_SOURCES = {"bundle-weaver": BUNDLE_WEAVER, "event-analyzer": EVENT_ANALYZER}
#: The opencode.* checks doctor runs, in order.
OPENCODE_IDS = [
    "opencode.lock",
    "opencode.files",
    "opencode.okf-skills",
    "opencode.agents",
    "opencode.rules",
    "opencode.okf-mcp",
    "opencode.hook",
]
PATCH_FIX = "run kmctl plugin patch"
APM_FIX = (
    "run apm install --target opencode (kmctl's package must be in apm.yml), "
    "then kmctl plugin patch"
)


def _split(text: str) -> tuple[dict, str]:
    """The front matter and the body of a markdown file."""
    assert text.startswith("---\n"), text[:40]
    end = text.index("\n---\n", 4)
    return yaml.safe_load(text[4:end]), text[end + 5 :]


def _sha(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()


def _mcp_entry() -> dict[str, object]:
    """okf's server as APM 0.33.0 writes it into opencode.json (spike:opencode-harness/6)."""
    return {
        "type": "local",
        "enabled": True,
        "command": ["sh", "-c", plugin.okf_mcp_launcher()],
    }


def _dep(entry: dict[str, object], files: dict[str, str], folders: list[str]) -> dict:
    return {
        **entry,
        "deployed_files": sorted([*files, *folders]),
        "deployed_file_hashes": {p: _sha(t) for p, t in files.items()},
    }


def _apm_writes(antigravity: bool = False) -> dict[str, str]:
    """What ``apm install --target opencode`` of kmctl's package leaves, by path from the repository.

    With ``antigravity`` the lock also holds Antigravity's sub-package rules,
    as an install for both targets would.
    """
    kmctl = {
        "repo_url": "JasperHG90/kmctl",
        "name": "kmctl",
        "resolved_ref": REF,
        "virtual_path": "apm",
    }
    okf = {"repo_url": "scaccogatto/okf-skills", "name": "okf", "resolved_ref": "a8b9"}
    files = {
        f".agents/skills/{s}/SKILL.md": (SKILLS / s / "SKILL.md").read_text()
        for s in SKILL_NAMES
    }
    files[".opencode/agents/kmctl-auditor.md"] = AUDITOR.read_text()
    okf_files = {".agents/skills/okf/SKILL.md": "okf\n"}
    for name, text in OKF_SOURCES.items():
        okf_files[f".opencode/agents/{name}.md"] = text
    deps = [
        _dep(kmctl, files, [f".agents/skills/{s}" for s in SKILL_NAMES]),
        _dep(okf, okf_files, [".agents/skills/okf"]),
    ]
    out = {**files, **okf_files}
    if antigravity:
        rules = {".agents/rules/okf-bundle.md": "a rule\n"}
        sub = {**kmctl, "name": "kmctl-antigravity", "virtual_path": "apm/antigravity"}
        deps.append(_dep(sub, rules, []))
        out.update(rules)
    out["apm.lock.yaml"] = yaml.safe_dump(
        {"lockfile_version": "1", "dependencies": deps}
    )
    for name, text in OKF_SOURCES.items():
        out[f"{OKF_AGENTS}/{name}.md"] = text
    out["opencode.json"] = json.dumps({"mcp": {plugin.MCP_NAME: _mcp_entry()}})
    out["apm.yml"] = yaml.safe_dump(
        {
            "name": "repo",
            "version": "0.1.0",
            "dependencies": {"apm": [plugin.new_entry()]},
            "targets": ["opencode", *(["antigravity"] if antigravity else [])],
        }
    )
    return out


def _apm_install(
    repo: Path, antigravity: bool = False, keep: tuple[str, ...] = ()
) -> None:
    """Write what ``apm install`` leaves in ``repo``; files in ``keep`` stay as they are."""
    for rel, text in _apm_writes(antigravity).items():
        path = repo / rel
        if rel in keep and path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A scratch repository as the working folder, with a scratch HOME and fake tools on PATH."""
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home / ".claude"))
    monkeypatch.setenv("XDG_DATA_HOME", str(home / ".local" / "share"))
    fakes = FakeTools(tmp_path, tools=("uvx", "uv", "claude", "git"))
    monkeypatch.setenv("PATH", fakes.path)
    repo = tmp_path / "repo"
    (repo / ".okf").mkdir(parents=True)
    monkeypatch.chdir(repo)
    return repo


def _kmctl(*args: str) -> Result:
    return CliRunner().invoke(app, list(args))


def _patch(*args: str) -> Result:
    result = _kmctl("plugin", "patch", *args)
    assert result.exit_code == 0, result.output
    return result


def _install(repo: Path) -> Result:
    """Install kmctl's package for OpenCode with the fake APM, then patch; fail unless it exits 0."""
    _apm_install(repo)
    return _patch()


def _tree(repo: Path) -> dict[str, bytes]:
    """Every file in ``repo`` but apm_modules/, by its path from the repository."""
    return {
        p.relative_to(repo).as_posix(): p.read_bytes()
        for p in sorted(repo.rglob("*"))
        if p.is_file() and "apm_modules" not in p.parts
    }


# r1: the agent translator -----------------------------------------------------


def test_translate_maps_each_known_tool() -> None:
    text = "---\nname: a\ndescription: d\ntools: Read, Grep, Glob, Write, Edit, Bash\n---\nb\n"

    meta, _ = _split(opencode.translate_agent(text, "a.md"))

    assert meta["permission"] == {
        "*": "deny",
        "read": "allow",
        "grep": "allow",
        "glob": "allow",
        "edit": "allow",
        "shell": "allow",
    }


def test_translate_puts_deny_first_so_the_allows_win() -> None:
    """OpenCode's last matching rule wins, so the wildcard deny must come first."""
    out = opencode.translate_agent(AUDITOR.read_text(), "kmctl-auditor.md")

    assert list(_split(out)[0]["permission"]) == ["*", "read", "grep", "glob"]


def test_translate_reads_a_yaml_tool_list() -> None:
    text = "---\nname: a\ndescription: d\ntools: [Read, Bash]\n---\nb\n"

    meta, _ = _split(opencode.translate_agent(text, "a.md"))

    assert meta["permission"] == {"*": "deny", "read": "allow", "shell": "allow"}


def test_translate_auditor_is_a_read_only_subagent() -> None:
    meta, _ = _split(opencode.translate_agent(AUDITOR.read_text(), "kmctl-auditor.md"))

    assert meta["mode"] == "subagent"
    assert meta["permission"] == {
        "*": "deny",
        "read": "allow",
        "grep": "allow",
        "glob": "allow",
    }


def test_translate_drops_claude_only_keys_and_tools() -> None:
    meta, _ = _split(opencode.translate_agent(BUNDLE_WEAVER, "bundle-weaver.md"))

    assert list(meta) == ["description", "mode", "permission"]
    assert meta["description"] == (
        "Fold event analyses into an OKF knowledge bundle in deterministic sequence."
    )


@pytest.mark.parametrize("source", [BUNDLE_WEAVER, EVENT_ANALYZER, None])
def test_translate_copies_the_body_unchanged(source: str | None) -> None:
    text = source if source is not None else AUDITOR.read_text()

    _, body = _split(opencode.translate_agent(text, "x.md"))

    assert body == _split(text)[1]


def test_translate_gives_the_same_bytes_twice() -> None:
    text = AUDITOR.read_text()

    assert opencode.translate_agent(text, "a") == opencode.translate_agent(text, "a")


def test_translate_refuses_an_unknown_tool_naming_it() -> None:
    text = "---\nname: a\ndescription: d\ntools: Read, WebFetch\n---\nb\n"

    with pytest.raises(plugin.PluginError, match="'WebFetch'"):
        opencode.translate_agent(text, "a.md")


def test_translate_refuses_an_agent_without_tools() -> None:
    with pytest.raises(plugin.PluginError, match="tools"):
        opencode.translate_agent("---\nname: a\ndescription: d\n---\nb\n", "a.md")


# r2: what patch writes ----------------------------------------------------------


def test_patch_rewrites_the_three_agents(repo: Path) -> None:
    _install(repo)

    for name in AGENT_NAMES:
        source = AUDITOR.read_text() if name == "kmctl-auditor" else OKF_SOURCES[name]
        have = (repo / ".opencode" / "agents" / f"{name}.md").read_text()
        assert have == opencode.translate_agent(source, name), name
    meta, _ = _split((repo / ".opencode/agents/kmctl-auditor.md").read_text())
    assert set(meta["permission"]) == {"*", "read", "grep", "glob"}


def test_patch_writes_the_four_rules_without_apply_to(repo: Path) -> None:
    _install(repo)

    assert len(RULE_NAMES) == 4
    assert sorted(p.name for p in (repo / ".opencode" / "rules").iterdir()) == sorted(
        f"{n}.md" for n in RULE_NAMES
    )
    for name in RULE_NAMES:
        text = (repo / ".opencode" / "rules" / f"{name}.md").read_text()
        source = (INSTRUCTIONS / f"{name}.instructions.md").read_text()
        assert "applyTo" not in text, name
        assert not text.startswith("---"), name
        assert text.endswith(_split(source)[1].lstrip("\n")), name


def test_patch_adds_the_instructions_entry_once_keeping_other_keys(repo: Path) -> None:
    _apm_install(repo)
    config = repo / "opencode.json"
    data = json.loads(config.read_text())
    data.update({"theme": "x", "instructions": ["CONTRIBUTING.md"]})
    config.write_text(json.dumps(data))

    _patch()
    _patch()

    after = json.loads(config.read_text())
    assert after["instructions"] == ["CONTRIBUTING.md", ".opencode/rules/*.md"]
    assert after["theme"] == "x"
    assert after["mcp"] == {plugin.MCP_NAME: _mcp_entry()}


def test_patch_creates_opencode_json_when_missing(repo: Path) -> None:
    _apm_install(repo)
    (repo / "opencode.json").unlink()

    _patch()

    assert json.loads((repo / "opencode.json").read_text()) == {
        "instructions": [".opencode/rules/*.md"]
    }


def test_patch_writes_the_briefing_plugin_and_nothing_under_agents_plugins(
    repo: Path,
) -> None:
    result = _install(repo)

    assert (repo / PLUGIN_PATH).read_text() == opencode.PLUGIN_SOURCE
    assert not (repo / ".agents" / "plugins").exists()
    assert "patched kmctl's package" in result.stdout
    assert "opencode" in result.stdout


def test_patch_twice_changes_no_file(repo: Path) -> None:
    _install(repo)
    before = _tree(repo)

    _patch()

    assert _tree(repo) == before


def test_patch_after_apm_install_again_gives_the_same_tree(repo: Path) -> None:
    """apm install puts APM's agents back; patch then rewrites them to the same bytes (spike:opencode-harness/7)."""
    _install(repo)
    before = _tree(repo)

    _apm_install(repo, keep=("opencode.json",))
    assert (
        repo / ".opencode/agents/kmctl-auditor.md"
    ).read_text() == AUDITOR.read_text()
    _patch()

    assert _tree(repo) == before


def test_patch_without_apm_modules_names_apm_install(repo: Path) -> None:
    _apm_install(repo)
    shutil.rmtree(repo / "apm_modules")

    result = _kmctl("plugin", "patch")

    assert result.exit_code == 1
    assert "apm install --target opencode" in plain(result.output)


# r3: an opencode.json that is not JSON ----------------------------------------------


def test_patch_refuses_invalid_json_naming_the_file(repo: Path) -> None:
    _apm_install(repo)
    config = repo / "opencode.json"
    config.write_text("{ not json")

    result = _kmctl("plugin", "patch")

    assert result.exit_code == 1
    assert "opencode.json" in plain(result.output)
    assert config.read_text() == "{ not json"
    assert not (repo / ".opencode" / "rules").exists()


def test_patch_refuses_instructions_that_are_not_a_list_writing_nothing(
    repo: Path,
) -> None:
    _apm_install(repo)
    config = repo / "opencode.json"
    config.write_text(json.dumps({"instructions": "A.md"}))
    before = _tree(repo)

    result = _kmctl("plugin", "patch")

    assert result.exit_code == 1
    assert "instructions key that is not a list" in plain(result.output)
    assert _tree(repo) == before


# r4: which harnesses are here -------------------------------------------------------


def _lock_of(paths: list[str], sub: list[str] | None = None) -> plugin.Lock:
    deps = [
        {
            "repo_url": "JasperHG90/kmctl",
            "name": "kmctl",
            "virtual_path": "apm",
            "deployed_files": paths,
        }
    ]
    if sub:
        deps.append(
            {
                "repo_url": "JasperHG90/kmctl",
                "name": "kmctl-antigravity",
                "virtual_path": "apm/antigravity",
                "deployed_files": sub,
            }
        )
    return plugin.Lock.model_validate({"dependencies": deps})


HARNESS_CASES = {
    "opencode only": (
        [".agents/skills/audit", ".opencode/agents/kmctl-auditor.md"],
        None,
        ["opencode"],
    ),
    "antigravity only": (
        [".agents/skills/audit"],
        [".agents/rules/okf-bundle.md"],
        ["antigravity"],
    ),
    "both": (
        [".agents/skills/audit", ".opencode/agents/kmctl-auditor.md"],
        [".agents/rules/okf-bundle.md"],
        ["antigravity", "opencode"],
    ),
}


@pytest.mark.parametrize("case", HARNESS_CASES)
def test_harnesses_patch_tells_opencode_from_antigravity(case: str) -> None:
    paths, sub, want = HARNESS_CASES[case]
    package = plugin.kmctl_files(_lock_of(paths, sub))
    assert package is not None

    assert plugin._harnesses_of(package) == want


@pytest.mark.parametrize("case", HARNESS_CASES)
def test_harnesses_doctor_tells_opencode_from_antigravity(
    case: str, tmp_path: Path
) -> None:
    paths, sub, want = HARNESS_CASES[case]
    (tmp_path / "apm.lock.yaml").write_text(
        yaml.safe_dump(_lock_of(paths, sub).model_dump())
    )

    assert doctor.harnesses_found(tmp_path) == want


def test_harnesses_shared_skills_alone_mark_neither() -> None:
    assert plugin.harnesses_marked([".agents/skills/audit/SKILL.md"]) == set()


def test_harnesses_opencode_only_patch_writes_no_antigravity_folder(repo: Path) -> None:
    result = _install(repo)

    assert json.loads(_kmctl("plugin", "patch", "--json").stdout)["harnesses"] == [
        "opencode"
    ]
    assert not (repo / ".agents" / "plugins").exists()
    assert "Antigravity" not in result.stdout


# r5: the briefing plugin never breaks a session ----------------------------------------

_HARNESS_JS = """\
// Load the plugin as OpenCode 2.x does, with a stub ctx, and report.
const [file, work] = process.argv.slice(2)
import(file).then(async ({ default: plugin }) => {
  const out = { id: plugin.id, bare: "ok", setup: "ok", hook: "ok", hooked: false, pushed: [] }
  // A ctx without session or location first: setup must not throw on it.
  try { await plugin.setup({}) } catch (e) { out.bare = String(e) }
  let hook = null
  const ctx = {
    location: { directory: work, project: { directory: work } },
    session: { hook: async (name, cb) => { if (name === "context") hook = cb } },
  }
  try { await plugin.setup(ctx) } catch (e) { out.setup = String(e) }
  if (hook) {
    out.hooked = true
    try { await hook({ system: out.pushed }) } catch (e) { out.hook = String(e) }
  }
  process.stdout.write(JSON.stringify(out))
})
"""


def _run_plugin(tmp_path: Path, kmctl: str | None) -> dict:
    """Load the plugin under node as OpenCode 2.x does; ``kmctl`` is the fake kmctl's script, or None for none on PATH."""
    if NODE is None:
        pytest.skip("node is not installed")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    if kmctl is not None:
        fake = bin_dir / "kmctl"
        fake.write_text(kmctl)
        fake.chmod(0o755)
    plugin_file = tmp_path / "kmctl.mjs"
    plugin_file.write_text(opencode.PLUGIN_SOURCE)
    harness = tmp_path / "harness.mjs"
    harness.write_text(_HARNESS_JS)
    work = tmp_path / "work"
    work.mkdir()
    proc = subprocess.run(
        [NODE, str(harness), plugin_file.as_uri(), str(work)],
        env={"PATH": f"{bin_dir}:/usr/bin:/bin", "HOME": str(tmp_path)},
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    return {**json.loads(proc.stdout), "work": str(work)}


def test_briefing_plugin_pushes_the_briefing_as_a_system_part(tmp_path: Path) -> None:
    out = _run_plugin(
        tmp_path,
        "#!/bin/sh\nprintf '%s\\n' \"$*\" >> \"$HOME/args\"\nprintf '# briefing\\nline two\\n'\n",
    )

    assert out["id"] == "kmctl"
    assert (out["bare"], out["setup"], out["hook"], out["hooked"]) == (
        "ok",
        "ok",
        "ok",
        True,
    )
    assert out["pushed"] == [{"type": "text", "text": "# briefing\nline two"}]
    # The bare setup ran kmctl too, from its own folder; the real one names the repository.
    lines = (tmp_path / "args").read_text().splitlines()
    assert f"briefing --path {out['work']}" in lines


@pytest.mark.parametrize(
    "kmctl",
    [None, "#!/bin/sh\necho oops >&2\nexit 1\n", "#!/bin/sh\nexit 0\n"],
    ids=["missing", "failing", "silent"],
)
def test_briefing_plugin_adds_nothing_and_throws_nothing(
    tmp_path: Path, kmctl: str | None
) -> None:
    out = _run_plugin(tmp_path, kmctl)

    assert (out["bare"], out["setup"], out["hook"], out["hooked"]) == (
        "ok",
        "ok",
        "ok",
        True,
    )
    assert out["pushed"] == []


# r6: --undo, and user scope ---------------------------------------------------------


def test_undo_leaves_no_kmctl_file(repo: Path) -> None:
    _apm_install(repo)
    apm_tree = _tree(repo)
    _patch()

    result = _patch("--undo")

    have = _tree(repo)
    for rel in [*AGENT_PATHS, *RULE_PATHS, PLUGIN_PATH]:
        assert rel not in have, rel
    assert json.loads((repo / "opencode.json").read_text()) == {
        "mcp": {plugin.MCP_NAME: _mcp_entry()}
    }
    # Everything else APM wrote is as it was (opencode.json is checked above).
    kept = [*AGENT_PATHS, "opencode.json"]
    assert {k: v for k, v in apm_tree.items() if k not in kept} == {
        k: v for k, v in have.items() if k not in kept
    }
    assert "OpenCode" in result.stdout


def test_undo_keeps_an_agent_that_is_not_kmctls_translation(repo: Path) -> None:
    _install(repo)
    edited = repo / ".opencode" / "agents" / "kmctl-auditor.md"
    edited.write_text("mine\n")

    _patch("--undo")

    assert edited.read_text() == "mine\n"


def test_undo_deletes_opencode_json_when_nothing_else_is_left(repo: Path) -> None:
    _apm_install(repo)
    (repo / "opencode.json").unlink()
    _patch()

    _patch("--undo")

    assert not (repo / "opencode.json").exists()


def test_undo_keeps_other_instructions(repo: Path) -> None:
    _apm_install(repo)
    (repo / "opencode.json").write_text(json.dumps({"instructions": ["A.md"]}))
    _patch()

    _patch("--undo")

    assert json.loads((repo / "opencode.json").read_text()) == {
        "instructions": ["A.md"]
    }


def test_undo_user_scope_leaves_opencode_files_and_names_them(repo: Path) -> None:
    _install(repo)
    before = _tree(repo)

    result = _patch("--undo", "--scope", "user")

    assert _tree(repo) == before
    said = " ".join(plain(result.stdout).split())
    for rel in [*AGENT_PATHS, *RULE_PATHS, PLUGIN_PATH, "opencode.json"]:
        assert rel in said, rel
    assert "kmctl plugin patch --undo" in said
    assert "without --scope user" in said


def test_undo_paths_name_what_undo_removes(repo: Path) -> None:
    _install(repo)
    planned = opencode.undo_paths(repo)

    assert sorted(opencode.undo(repo)) == sorted(planned)


def test_user_scope_leaves_opencode_alone_and_says_so(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = Path.home()
    for rel, text in _apm_writes().items():
        if rel in ("apm.lock.yaml", "apm.yml"):
            path = home / ".apm" / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)

    result = _patch("--scope", "user")

    assert not (repo / ".opencode").exists()
    assert not (home / ".opencode" / "rules").exists()
    assert "OpenCode is patched at project scope only" in plain(result.stdout)


# r7: kmctl doctor ---------------------------------------------------------------


def _checks(repo: Path) -> dict[str, dict]:
    assert _kmctl("init").exit_code == 0
    result = _kmctl("doctor", "--json")
    assert result.exit_code in (0, 1), result.output
    return {c["id"]: c for c in json.loads(result.stdout)["checks"]}


def test_doctor_opencode_runs_its_checks_and_passes_when_patched(repo: Path) -> None:
    _install(repo)

    checks = _checks(repo)

    ids = [i for i in checks if i.startswith("opencode.")]
    assert ids == OPENCODE_IDS
    for cid in OPENCODE_IDS:
        assert checks[cid]["ok"], checks[cid]
    assert checks["dep.opencode"]["status"] == "warn"
    assert checks["dep.opencode"]["detail"].startswith("opencode is not on PATH")
    assert "antigravity.lock" not in checks
    assert all(c["ok"] for c in checks.values()), checks


def _break_agents(repo: Path) -> None:
    _apm_install(repo, keep=("opencode.json",))


def _break_rule(repo: Path) -> None:
    (repo / RULE_PATHS[0]).write_text("edited\n")


def _break_entry(repo: Path) -> None:
    config = repo / "opencode.json"
    data = json.loads(config.read_text())
    data["instructions"] = []
    config.write_text(json.dumps(data))


def _break_mcp(repo: Path) -> None:
    config = repo / "opencode.json"
    data = json.loads(config.read_text())
    del data["mcp"]
    config.write_text(json.dumps(data))


def _break_plugin(repo: Path) -> None:
    (repo / PLUGIN_PATH).write_text("// edited\n")


@pytest.mark.parametrize(
    ("breaks", "cid", "said", "fix"),
    [
        (
            _break_agents,
            "opencode.agents",
            ".opencode/agents/kmctl-auditor.md differs",
            PATCH_FIX,
        ),
        (_break_rule, "opencode.rules", f"{RULE_PATHS[0]} differs", PATCH_FIX),
        (
            _break_entry,
            "opencode.rules",
            "instructions lacks .opencode/rules/*.md",
            PATCH_FIX,
        ),
        (
            _break_mcp,
            "opencode.okf-mcp",
            "missing okf's MCP server okf-bundle",
            APM_FIX,
        ),
        (_break_plugin, "opencode.hook", f"{PLUGIN_PATH} differs", PATCH_FIX),
    ],
    ids=["bare-apm-install", "edited-rule", "no-entry", "no-mcp", "edited-plugin"],
)
def test_doctor_opencode_reports_each_fault(
    repo: Path, breaks, cid: str, said: str, fix: str
) -> None:
    _install(repo)
    breaks(repo)

    check = _checks(repo)[cid]

    assert check["ok"] is False
    assert said in check["detail"]
    assert check["fix"] == fix


def test_doctor_opencode_files_ignore_the_rewritten_agents(repo: Path) -> None:
    """The lock hashes APM's agents; patch rewrote them, so .files and .okf-skills skip them."""
    _install(repo)
    (repo / ".agents" / "skills" / SKILL_NAMES[0] / "SKILL.md").write_text("e\n")

    checks = _checks(repo)

    assert checks["opencode.okf-skills"]["ok"], checks["opencode.okf-skills"]
    assert checks["opencode.files"]["detail"] == (
        f".agents/skills/{SKILL_NAMES[0]}/SKILL.md differs from apm.lock.yaml"
    )


def test_doctor_opencode_ids_are_in_the_help_and_the_reference() -> None:
    help_text = " ".join(plain(_kmctl("doctor", "--help").stdout).split())
    reference = COMMANDS.read_text()

    for cid in [*OPENCODE_IDS, "dep.opencode"]:
        assert f"`{cid}`" in reference, cid
    # The help names the checks shared by every harness once, as claude.,
    # antigravity. or opencode.: lock, files, okf-skills; and the rest in full.
    assert "claude., antigravity. or opencode.:" in help_text
    for cid in (
        "opencode.agents",
        "opencode.rules",
        "opencode.okf-mcp",
        "opencode.hook",
    ):
        assert cid in help_text, cid
    assert "dep.opencode" in help_text


# r8: a real install in a scratch consumer ------------------------------------------


def _git_tree(repo: Path) -> dict[str, bytes]:
    return {
        p.relative_to(repo).as_posix(): p.read_bytes()
        for p in sorted(repo.rglob("*"))
        if p.is_file() and ".git" not in p.parts and "apm_modules" not in p.parts
    }


def _apm(consumer: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uvx", "--from", plugin.APM_CLI, "apm", *args],
        cwd=consumer,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.integration
def test_consumer_gets_skills_rules_agents_plugin_and_mcp(
    consumer: Path, served: str
) -> None:
    apm_install(consumer, served, "opencode")

    skills = consumer / ".agents" / "skills"
    for skill in SKILL_NAMES:
        assert (skills / skill / "SKILL.md").read_bytes() == (
            SKILLS / skill / "SKILL.md"
        ).read_bytes(), skill
    for skill in ("okf", "validate", "backfill", "visualize"):
        assert (skills / skill / "SKILL.md").is_file(), skill
    want = opencode.files(consumer)
    assert sorted(want) == sorted([*AGENT_PATHS, *RULE_PATHS, PLUGIN_PATH])
    for rel, text in want.items():
        assert (consumer / rel).read_text() == text, rel
    config = json.loads((consumer / "opencode.json").read_text())
    assert config["instructions"] == [".opencode/rules/*.md"]
    assert config["mcp"][plugin.MCP_NAME] == _mcp_entry()
    assert not (consumer / ".agents" / "plugins").exists()

    # A second apm install puts APM's agents back; patch rewrites them.
    before = _git_tree(consumer)
    again = _apm(consumer, "install", "--allow-insecure")
    assert again.returncode == 0, again.stderr + again.stdout
    assert _kmctl("plugin", "patch").exit_code == 0
    assert _git_tree(consumer) == before

    # --undo, then apm uninstall, leaves no kmctl or okf file.
    assert _kmctl("plugin", "patch", "--undo").exit_code == 0
    entry = yaml.safe_load((consumer / "apm.yml").read_text())["dependencies"]["apm"][0]
    gone = _apm(consumer, "uninstall", plugin.uninstall_name(entry))
    assert gone.returncode == 0, gone.stderr + gone.stdout
    left = [
        rel for rel in _git_tree(consumer) if rel.startswith((".agents/", ".opencode/"))
    ]
    assert left == []


# r9: OpenCode loads the agents -----------------------------------------------------


def _subagents(opencode_bin: str, repo: Path, env: dict[str, str]) -> set[str]:
    """The subagents ``opencode debug agents`` lists in ``repo``.

    OpenCode 2.x answers through a background service it starts on first
    use, on a fixed port unless told otherwise, and lists no agents until
    that service has loaded them. So the service gets a free port of its own
    (a service the user runs is left alone), an empty list is asked again for
    up to 30 seconds, and the service is stopped afterwards.
    """
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = str(sock.getsockname()[1])
    subprocess.run(
        [opencode_bin, "service", "set", "port", port],
        env=env,
        capture_output=True,
        check=True,
    )
    try:
        for _ in range(30):
            proc = subprocess.run(
                [opencode_bin, "debug", "agents"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=False,
                timeout=180,
                env=env,
                stdin=subprocess.DEVNULL,
            )
            assert proc.returncode == 0, proc.stderr
            agents = json.loads(proc.stdout)
            if agents:
                return {a["id"] for a in agents if a.get("mode") == "subagent"}
            time.sleep(1)
        return set()
    finally:
        subprocess.run(
            [opencode_bin, "service", "stop"], env=env, capture_output=True, check=False
        )


@pytest.mark.integration
def test_opencode_loads_agents(repo: Path, tmp_path: Path) -> None:
    """With OpenCode 2.x on PATH, it lists the three translated agents as subagents."""
    if OPENCODE is None:
        pytest.skip("opencode is not installed")
    _install(repo)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    home = tmp_path / "opencode-home"
    home.mkdir()
    env = {"PATH": f"{Path(OPENCODE).parent}:/usr/bin:/bin", "HOME": str(home)}

    assert set(AGENT_NAMES) <= _subagents(OPENCODE, repo, env)


# r10: the decision and the docs ---------------------------------------------------


def _decision() -> Path:
    [path] = list(DECISIONS.glob("0024-*.md"))
    return path


def _flat(text: str) -> str:
    return " ".join(text.split())


def test_docs_decision_matches_the_decision_schema() -> None:
    meta = json.loads(json.dumps(front_matter(_decision()), default=str))

    errors = [
        e.message for e in Draft202012Validator(schema("decision")).iter_errors(meta)
    ]

    assert errors == []


def test_docs_decision_records_the_route() -> None:
    text = _flat(_decision().read_text())

    for words in (
        "apm install --target opencode",
        "kmctl plugin patch",
        ".opencode/rules/*.md",
        "instructions",
        "every session",
        ".opencode/plugins/kmctl.js",
        "mode: subagent",
        "Bash",
        "shell",
        "setup",
        "OpenCode 2.x",
        "2.0.32",
        "apm uninstall",
        "--undo",
        "apm audit",
        "Drop it when",
    ):
        assert words in text, words


def test_docs_manifesto_names_opencode() -> None:
    text = MANIFESTO.read_text()
    out_of_scope = text.split("Out of scope", 1)[1].split("\n## ", 1)[0]

    assert "OpenCode" in text.split("Out of scope", 1)[0]
    assert "opencode" not in out_of_scope.lower()


def test_docs_commands_reference_documents_opencode() -> None:
    text = _flat(COMMANDS.read_text())

    for words in (".opencode/rules/", "opencode.json", ".opencode/plugins/kmctl.js"):
        assert words in text, words
    assert "apm uninstall" in text


def test_docs_install_how_to_and_readme_cover_opencode() -> None:
    assert "OpenCode" in README.read_text()
    how_to = _flat(INSTALL_HOW_TO.read_text())
    for words in (
        "apm install --target opencode",
        "every session",
        "uv",
        "kmctl plugin patch --undo",
    ):
        assert words in how_to, words


# drop-summary-nudge r1: the plugin runs nothing after a tool call ----------------


def test_plugin_has_no_after_tool_hook() -> None:
    assert "execute.after" not in opencode.PLUGIN_SOURCE
    assert '["briefing", "--path", cwd]' in opencode.PLUGIN_SOURCE
