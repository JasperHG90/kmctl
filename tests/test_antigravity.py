"""kmctl's Antigravity pieces and kmctl briefing --format antigravity (ADR 0015, ADR 0020).

APM installs kmctl's and okf's skills, the rules, the hooks and okf's MCP
server into .agents/; kmctl plugin patch writes the translated agents into
a folder it alone owns, .agents/plugins/kmctl/, and takes APM's broken okf
Stop handler out of .agents/hooks.json. No test here
without a marker runs the real APM: ``FakeTools`` stands in for uvx and
writes okf's agents where APM puts them. HOME, CLAUDE_CONFIG_DIR and
XDG_DATA_HOME point at scratch folders. The ``integration`` tests run the real
``agy plugin validate`` (skipped without agy) and the real APM 0.33.0 against
this tree served from a local git server.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from importlib.metadata import version
from pathlib import Path

import pytest
import yaml
from conftest import apm_install, plain
from fixtures.fake_tools import FakeTools
from jsonschema import Draft202012Validator
from typer.testing import CliRunner, Result

from kmctl import antigravity, app, plugin
from kmctl.briefing import hook_workspace
from kmctl.kinds import schema, skeleton
from kmctl.okf import front_matter

ROOT = Path(__file__).resolve().parents[1]
DOT_APM = ROOT / "apm" / ".apm"
SKILLS = DOT_APM / "skills"
AUDITOR = DOT_APM / "agents" / "kmctl-auditor.md"
INSTRUCTIONS = ROOT / "apm" / "claude" / ".apm" / "instructions"
DECISIONS = ROOT / ".okf" / "decisions"
MANIFESTO = ROOT / ".okf" / "manifesto.md"
ADR_0003 = DECISIONS / "0003-claude-code-plugin-first-depends-on-okf.md"
COMMANDS = ROOT / "docs" / "reference" / "commands.md"
INSTALL_HOW_TO = ROOT / "docs" / "how-to" / "install-the-plugin-and-the-ci-action.md"
REF = f"v{version('kmctl')}"
OKF_AGENTS = "apm_modules/scaccogatto/okf-skills/agents"
AGY = shutil.which("agy") or (
    str(Path.home() / ".local" / "bin" / "agy")
    if (Path.home() / ".local" / "bin" / "agy").is_file()
    else None
)
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
# A comment the translation drops.
model: haiku
effort: medium
tools: Bash, Read, Write
color: blue
---

You analyze one event.
"""
RULE_NAMES = sorted(
    p.name.removesuffix(".instructions.md")
    for p in INSTRUCTIONS.glob("*.instructions.md")
)
PLUGIN_FILES = [
    "agents/bundle-weaver.md",
    "agents/event-analyzer.md",
    "agents/kmctl-auditor.md",
    "plugin.json",
]


def _split(text: str) -> tuple[dict, str]:
    """The front matter and the body of a markdown file."""
    assert text.startswith("---\n"), text[:40]
    end = text.index("\n---\n", 4)
    return yaml.safe_load(text[4:end]), text[end + 5 :]


def _lock(harnesses: tuple[str, ...] = ("antigravity",)) -> str:
    """An apm.lock.yaml holding the kmctl package at this CLI's ref, deployed for ``harnesses``."""
    tops = {"claude": ".claude", "antigravity": ".agents"}
    return yaml.safe_dump(
        {
            "lockfile_version": "1",
            "dependencies": [
                {
                    "repo_url": "JasperHG90/kmctl",
                    "name": "kmctl",
                    "resolved_ref": REF,
                    "virtual_path": "apm",
                    "deployed_files": [f"{tops[h]}/skills/audit" for h in harnesses],
                }
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
    """A scratch repository with a .okf/ folder, as the working folder."""
    repo = tmp_path / "repo"
    (repo / ".okf").mkdir(parents=True)
    monkeypatch.chdir(repo)
    return repo


@pytest.fixture
def fakes(tmp_path: Path, home: Path, monkeypatch: pytest.MonkeyPatch) -> FakeTools:
    """Fake uvx and claude alone on PATH; kmctl plugin patch runs neither APM nor uvx."""
    tools = FakeTools(tmp_path, tools=("uvx", "claude"))
    monkeypatch.setenv("PATH", tools.path)
    return tools


def _apm_install(harnesses: tuple[str, ...] = ("antigravity",)) -> None:
    """Write what ``apm install`` of kmctl's entry leaves: the lock and okf's two agents."""
    cwd = Path.cwd()
    (cwd / OKF_AGENTS).mkdir(parents=True, exist_ok=True)
    (cwd / OKF_AGENTS / "bundle-weaver.md").write_text(BUNDLE_WEAVER)
    (cwd / OKF_AGENTS / "event-analyzer.md").write_text(EVENT_ANALYZER)
    (cwd / "apm.lock.yaml").write_text(_lock(harnesses))


def _kmctl(*args: str, stdin: str | None = None) -> Result:
    """Run kmctl in-process with ``args``."""
    return CliRunner().invoke(app, list(args), input=stdin)


def _install(*args: str, harnesses: tuple[str, ...] = ("antigravity",)) -> Result:
    """Install kmctl's package with the fake APM, then run ``kmctl plugin patch``; fail unless it exits 0."""
    _apm_install(harnesses)
    result = _kmctl("plugin", "patch", *args)
    assert result.exit_code == 0, result.output
    return result


def _folder(repo: Path) -> Path:
    return repo / ".agents" / "plugins" / "kmctl"


def _files(folder: Path) -> dict[str, bytes]:
    """Every file under ``folder``, by its path relative to it."""
    return {
        p.relative_to(folder).as_posix(): p.read_bytes()
        for p in sorted(folder.rglob("*"))
        if p.is_file()
    }


# r1: the agent translator -----------------------------------------------------


def test_translate_maps_each_known_tool() -> None:
    claude = "---\nname: a\ndescription: d\ntools: Read, Grep, Glob, Write, Edit, Bash\n---\nbody\n"

    meta, _ = _split(antigravity.translate_agent(claude, "a.md"))

    assert meta["tools"] == [
        "view_file",
        "grep_search",
        "find_by_name",
        "list_dir",
        "write_to_file",
        "replace_file_content",
        "run_command",
    ]


def test_translate_reads_a_yaml_tool_list() -> None:
    claude = "---\nname: a\ndescription: d\ntools:\n  - Read\n  - Glob\n---\nbody\n"

    meta, _ = _split(antigravity.translate_agent(claude, "a.md"))

    assert meta["tools"] == ["view_file", "find_by_name", "list_dir"]


def test_translate_auditor_is_read_only_subagent() -> None:
    meta, _ = _split(antigravity.translate_agent(AUDITOR.read_text(), AUDITOR.name))

    assert meta == {
        "name": "kmctl-auditor",
        "description": _split(AUDITOR.read_text())[0]["description"],
        "tools": ["view_file", "grep_search", "find_by_name", "list_dir"],
        "mainAgent": False,
        "subagent": True,
        "model": "inherit",
        "commandExecutionPolicy": "off",
    }


def test_translate_agent_with_bash_gets_no_execution_policy() -> None:
    meta, _ = _split(antigravity.translate_agent(BUNDLE_WEAVER, "bundle-weaver.md"))

    assert "commandExecutionPolicy" not in meta
    assert "run_command" in meta["tools"]


def test_translate_drops_claude_only_keys() -> None:
    meta, _ = _split(antigravity.translate_agent(EVENT_ANALYZER, "event-analyzer.md"))

    assert list(meta) == [
        "name",
        "description",
        "tools",
        "mainAgent",
        "subagent",
        "model",
    ]
    assert meta["model"] == "inherit"
    assert meta["tools"] == ["run_command", "view_file", "write_to_file"]


@pytest.mark.parametrize("source", [BUNDLE_WEAVER, EVENT_ANALYZER, None])
def test_translate_copies_the_body_unchanged(source: str | None) -> None:
    text = source if source is not None else AUDITOR.read_text()

    translated = antigravity.translate_agent(text, "x.md")

    assert translated.partition("\n---\n")[2] == text[4:].partition("\n---\n")[2]


def test_translate_refuses_an_unknown_tool_naming_it() -> None:
    claude = "---\nname: a\ndescription: d\ntools: Read, WebFetch\n---\nbody\n"

    with pytest.raises(plugin.PluginError, match=r"a\.md.*'WebFetch'"):
        antigravity.translate_agent(claude, "a.md")


def test_translate_refuses_an_agent_without_tools() -> None:
    with pytest.raises(plugin.PluginError, match="a.md"):
        antigravity.translate_agent("---\nname: a\ndescription: d\n---\nb\n", "a.md")


# r2: the plugin folder --------------------------------------------------------


def test_plugin_folder_holds_exactly_the_agents_and_the_manifest(
    repo: Path, fakes: FakeTools
) -> None:
    _install()

    assert sorted(_files(_folder(repo))) == PLUGIN_FILES


def test_plugin_folder_manifest_names_kmctl(repo: Path, fakes: FakeTools) -> None:
    _install()

    assert json.loads((_folder(repo) / "plugin.json").read_text()) == {"name": "kmctl"}


def test_plugin_folder_agents_are_the_translations(
    repo: Path, fakes: FakeTools
) -> None:
    _install()
    agents = _folder(repo) / "agents"

    assert (agents / "kmctl-auditor.md").read_text() == antigravity.translate_agent(
        AUDITOR.read_text(), AUDITOR.name
    )
    auditor, _ = _split((agents / "kmctl-auditor.md").read_text())
    assert auditor["commandExecutionPolicy"] == "off"
    assert not {"write_to_file", "replace_file_content", "run_command"} & set(
        auditor["tools"]
    )
    for name, text in (
        ("bundle-weaver.md", BUNDLE_WEAVER),
        ("event-analyzer.md", EVENT_ANALYZER),
    ):
        assert (agents / name).read_text() == antigravity.translate_agent(text, name)


def test_plugin_folder_second_install_changes_nothing(
    repo: Path, fakes: FakeTools
) -> None:
    _install()
    first = _files(_folder(repo))

    _install()

    assert _files(_folder(repo)) == first


def test_plugin_folder_install_replaces_the_whole_folder(
    repo: Path, fakes: FakeTools
) -> None:
    _install()
    (_folder(repo) / "agents" / "old.md").write_text("stale")
    (_folder(repo) / "hooks.json").write_text("{}")
    (_folder(repo) / "plugin.json").write_text("{}")

    _install()

    assert sorted(_files(_folder(repo))) == PLUGIN_FILES
    assert json.loads((_folder(repo) / "plugin.json").read_text()) == {"name": "kmctl"}


def test_plugin_folder_needs_okf_agents_from_apm(repo: Path, fakes: FakeTools) -> None:
    """Without apm_modules/ the okf agents cannot be translated, so the install refuses."""
    with pytest.raises(plugin.PluginError, match="apm_modules/"):
        antigravity.plugin_files(repo)


def test_plugin_folder_patch_for_antigravity_alone_skips_claude(
    repo: Path, fakes: FakeTools
) -> None:
    _install()

    assert not (repo / ".claude").exists()
    assert not (repo / ".mcp.json").exists()
    assert fakes.calls() == []


def test_plugin_folder_patch_for_both_harnesses(repo: Path, fakes: FakeTools) -> None:
    result = _install("--json", harnesses=("claude", "antigravity"))

    assert sorted(_files(_folder(repo))) == PLUGIN_FILES
    assert json.loads(result.stdout)["harnesses"] == ["claude", "antigravity"]


def test_plugin_folder_not_written_at_user_scope(
    repo: Path, fakes: FakeTools, home: Path
) -> None:
    (home / ".apm").mkdir()
    (home / ".apm" / "apm.lock.yaml").write_text(_lock(("claude", "antigravity")))

    result = _kmctl("plugin", "patch", "--scope", "user")

    assert result.exit_code == 0, result.output
    assert not _folder(repo).exists()


def test_plugin_folder_install_ends_with_trust_step(
    repo: Path, fakes: FakeTools
) -> None:
    result = _install()

    assert re.search(
        r"^Next: .*trust.*, then kmctl doctor$",
        result.stdout,
        re.MULTILINE,
    )


# r3: kmctl briefing --format antigravity --------------------------------------


def _text_briefing(root: Path) -> str:
    result = _kmctl("briefing", "--path", str(root))
    assert result.exit_code == 0, result.output
    return result.stdout.rstrip("\n")


def _steps(result: Result) -> str:
    """The systemMessage of a ``--format antigravity`` briefing; fail unless it has that shape."""
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)
    assert list(data) == ["injectSteps"]
    [step] = data["injectSteps"]
    assert list(step) == ["systemMessage"] and list(step["systemMessage"]) == [
        "systemMessage"
    ]
    return step["systemMessage"]["systemMessage"]


def test_briefing_format_antigravity_wraps_the_text_briefing(repo: Path) -> None:
    result = _kmctl("briefing", "--format", "antigravity", "--path", str(repo))

    assert _steps(result) == _text_briefing(repo)


def test_briefing_format_antigravity_reads_workspace_from_stdin(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    hook_input = json.dumps({"workspacePaths": [str(repo)], "hookEventName": "x"})

    result = _kmctl("briefing", "--format", "antigravity", stdin=hook_input)

    assert _steps(result) == _text_briefing(repo)
    assert _steps(result) != _text_briefing(elsewhere)


def test_briefing_format_antigravity_reads_a_file_uri(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    hook_input = json.dumps({"workspacePaths": [repo.resolve().as_uri()]})

    result = _kmctl("briefing", "--format", "antigravity", stdin=hook_input)

    assert _steps(result) == _text_briefing(repo)


@pytest.mark.parametrize(
    "stdin",
    [
        "",
        "not json",
        "[]",
        '{"workspacePaths": []}',
        '{"workspacePaths": ["/no/such"]}',
    ],
)
def test_briefing_format_antigravity_falls_back_to_path(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stdin: str
) -> None:
    monkeypatch.chdir(tmp_path)

    result = _kmctl(
        "briefing", "--format", "antigravity", "--path", str(repo), stdin=stdin
    )

    assert _steps(result) == _text_briefing(repo)


def test_briefing_format_antigravity_from_a_terminal_uses_path(repo: Path) -> None:
    """A terminal on stdin is never read, so the command does not wait for input."""

    class Terminal:
        def isatty(self) -> bool:
            return True

        def read(self) -> str:
            raise AssertionError("read a terminal")

    assert hook_workspace(Terminal()) is None


def test_briefing_format_antigravity_stdin_path_runs_from_any_folder(
    repo: Path, tmp_path: Path
) -> None:
    """The real CLI, run from another folder with the hook's JSON piped in."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    kmctl = shutil.which("kmctl", path=os.environ.get("PATH", ""))
    assert kmctl, "kmctl must be on PATH (uv run)"

    proc = subprocess.run(
        [kmctl, "briefing", "--format", "antigravity"],
        input=json.dumps({"workspacePaths": [str(repo)]}),
        cwd=elsewhere,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["injectSteps"][0]["systemMessage"]["systemMessage"] == (
        _text_briefing(repo)
    )


def test_briefing_format_text_is_the_default(repo: Path) -> None:
    default = _kmctl("briefing", "--path", str(repo))
    text = _kmctl("briefing", "--format", "text", "--path", str(repo))

    assert default.stdout == text.stdout
    assert not default.stdout.startswith("{")


def test_briefing_format_json_keeps_its_meaning(repo: Path) -> None:
    data = json.loads(_kmctl("briefing", "--path", str(repo), "--json").stdout)

    assert set(data) == {"routing", "state", "rules", "skills"}


def test_briefing_format_antigravity_with_json_is_refused(repo: Path) -> None:
    result = _kmctl(
        "briefing", "--format", "antigravity", "--json", "--path", str(repo)
    )

    assert result.exit_code == 2
    output = plain(result.output)
    assert "--json" in output and "--format" in output


# r4 and I1: the hook never blocks ---------------------------------------------


def _run_hook(cwd: Path, path: str) -> subprocess.CompletedProcess[str]:
    """Run the Antigravity hook command in ``cwd`` with only ``path`` on PATH."""
    return subprocess.run(
        ["/bin/sh", "-c", antigravity.HOOK_COMMAND],
        input=json.dumps({"workspacePaths": [str(cwd)]}),
        env={"PATH": path, "HOME": str(cwd)},
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _fake_kmctl(tmp_path: Path, script: str) -> str:
    """A bin folder holding a fake kmctl running ``script``; returns a PATH with it."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "kmctl"
    fake.write_text(f"#!/bin/sh\n{script}\n")
    fake.chmod(0o755)
    return f"{bin_dir}:/usr/bin:/bin"


def test_hook_never_blocks_without_kmctl(tmp_path: Path) -> None:
    result = _run_hook(tmp_path, "/usr/bin:/bin")

    assert result.returncode == 0
    assert json.loads(result.stdout) == {}


def test_hook_never_blocks_when_kmctl_fails(tmp_path: Path) -> None:
    path = _fake_kmctl(tmp_path, "echo 'half a briefing'; echo boom >&2; exit 3")

    result = _run_hook(tmp_path, path)

    assert result.returncode == 0
    assert json.loads(result.stdout) == {}


def test_hook_never_blocks_and_relays_the_briefing(tmp_path: Path) -> None:
    """When kmctl works, the hook passes its JSON and the hook's stdin through."""
    path = _fake_kmctl(
        tmp_path,
        'read -r line; printf \'{"injectSteps": [], "got": %s}\\n\' "$line"',
    )

    result = _run_hook(tmp_path, path)

    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["got"] == {"workspacePaths": [str(tmp_path)]}


# r5: the folder comparison doctor uses ---------------------------------------


def test_plugin_problems_name_each_file_without_the_cli(
    repo: Path, fakes: FakeTools
) -> None:
    _install()
    (_folder(repo) / "plugin.json").write_text("{}")
    (_folder(repo) / "agents" / "kmctl-auditor.md").unlink()
    (_folder(repo) / "agents" / "extra.md").write_text("x\n")

    problems = antigravity.plugin_problems(repo)

    assert problems == [
        ".agents/plugins/kmctl/agents/extra.md is not one kmctl writes",
        ".agents/plugins/kmctl/agents/kmctl-auditor.md is missing",
        ".agents/plugins/kmctl/plugin.json differs from what this kmctl writes",
    ]


def test_plugin_problems_without_apm_modules_raise_the_fix(
    repo: Path, fakes: FakeTools
) -> None:
    _install()
    shutil.rmtree(repo / "apm_modules")

    with pytest.raises(
        plugin.PluginError,
        match=r"^apm_modules/ is missing; run apm install --target antigravity \(kmctl's package must be in apm.yml\), then kmctl plugin patch$",
    ):
        antigravity.plugin_problems(repo)


# r6: agy validates the folder -------------------------------------------------


@pytest.mark.integration
def test_agy_validate_counts_three_agents(
    repo: Path, fakes: FakeTools, home: Path
) -> None:
    if AGY is None:
        pytest.skip("agy is not installed")
    _install()

    proc = subprocess.run(
        [AGY, "plugin", "validate", "--strict", "--json", str(_folder(repo))],
        env={
            "PATH": "/usr/bin:/bin",
            "HOME": str(home),
            "CLAUDE_CONFIG_DIR": str(home / ".claude"),
            "XDG_DATA_HOME": str(home / ".local" / "share"),
        },
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr + proc.stdout
    report = json.loads(proc.stdout)
    assert report["components"]["agents"] == 3
    assert report["components"]["hooks"] == 0
    assert report["components"]["mcpServers"] == 0
    assert report["components"]["rules"] == 0
    assert report["findings"] == []


# r7: a real install in a scratch consumer --------------------------------------


@pytest.mark.integration
def test_consumer_gets_skills_rules_and_the_plugin_folder(
    consumer: Path, served: str
) -> None:
    apm_install(consumer, served, "antigravity")

    agents = consumer / ".agents"
    for skill in sorted(p.name for p in SKILLS.iterdir() if p.is_dir()):
        assert (agents / "skills" / skill / "SKILL.md").read_bytes() == (
            SKILLS / skill / "SKILL.md"
        ).read_bytes(), skill
    for skill in ("okf", "validate", "backfill", "visualize"):
        assert (agents / "skills" / skill / "SKILL.md").is_file(), skill
    assert len(RULE_NAMES) == 4
    for rule in RULE_NAMES:
        meta, _ = _split((agents / "rules" / f"{rule}.md").read_text())
        assert meta["trigger"] == "glob", rule
        assert isinstance(meta["globs"], str), rule
        assert all(g.startswith("**/") for g in meta["globs"].split(", ")), rule
    assert antigravity.mcp_present(consumer)
    folder = agents / "plugins" / "kmctl"
    assert sorted(_files(folder)) == PLUGIN_FILES
    assert {k: v.decode() for k, v in _files(folder).items()} == (
        antigravity.plugin_files(consumer)
    )
    assert antigravity.plugin_problems(consumer) == []
    assert antigravity.hook_present(consumer)
    (consumer / ".okf").mkdir(exist_ok=True)
    assert _kmctl("init").exit_code == 0
    doctor = _kmctl("doctor", "--json")
    checks = {c["id"]: c for c in json.loads(doctor.stdout)["checks"]}
    for cid in (
        "antigravity.files",
        "antigravity.plugin",
        "antigravity.okf-skills",
        "antigravity.hook",
        "antigravity.apm-hooks",
        "antigravity.okf-mcp",
    ):
        assert checks[cid]["ok"], checks[cid]
    assert not antigravity.apm_okf_stop_present(consumer)


# r8: the decision and the docs ------------------------------------------------


def _decision() -> Path:
    [path] = [p for p in DECISIONS.glob("0015-*.md")]
    return path


def _flat(text: str) -> str:
    return " ".join(text.split())


def _sections(text: str) -> list[str]:
    return [line[3:].strip() for line in text.splitlines() if line.startswith("## ")]


def test_docs_decision_matches_the_decision_schema() -> None:
    meta = json.loads(json.dumps(front_matter(_decision()), default=str))

    errors = [
        e.message for e in Draft202012Validator(schema("decision")).iter_errors(meta)
    ]

    assert errors == []
    # Later corrections are appended, never written into the skeleton's sections.
    sections = [
        s
        for s in _sections(_decision().read_text())
        if not s.startswith("Correction, ")
    ]
    assert sections == skeleton("decision")


def test_docs_decision_records_the_route() -> None:
    text = _flat(_decision().read_text())

    for words in (
        "kmctl plugin install --harness antigravity",
        "apm install",
        ".agents/plugins/kmctl/",
        "agy plugin install",
        "trust",
        "Read",
        "view_file",
        "grep_search",
        "find_by_name",
        "list_dir",
        "write_to_file",
        "replace_file_content",
        "run_command",
        "kmctl briefing --format antigravity",
        "mcp_config.json",
    ):
        assert words in text, words


def test_docs_manifesto_names_antigravity() -> None:
    text = MANIFESTO.read_text()
    parts = text.split("## Parts", 1)[1].split("\n## ", 1)[0]
    out_of_scope = text.split("## Out of scope for now", 1)[1]

    assert "Antigravity" in parts
    assert "--target antigravity" in _flat(parts)
    assert "Antigravity" not in out_of_scope


def test_docs_adr_0003_points_to_the_new_decision() -> None:
    assert _decision().name in ADR_0003.read_text()


def test_docs_commands_reference_documents_harness_and_format() -> None:
    text = _flat(COMMANDS.read_text())

    assert "kmctl plugin patch" in text and "`--undo`" in text
    assert "--format" in text and "injectSteps" in text
    assert ".agents/plugins/kmctl/" in text


def test_docs_install_how_to_covers_antigravity() -> None:
    text = _flat(INSTALL_HOW_TO.read_text())

    assert "apm install --target antigravity" in text
    assert "kmctl plugin patch" in text
    assert "trust" in text.lower()
    assert re.search(r"okf's MCP server[^.]*needs `?uv`?", text), (
        "uv for the MCP server"
    )


# antigravity-okf-stop-hook: okf's Stop check, run by kmctl ----------------------

OKF_STOP = ROOT / "tests" / "fixtures" / "okf-stop-check.sh"
APM_OKF_HANDLER = {
    "type": "command",
    "statusMessage": "Checking OKF bundle...",
    "command": 'bash ".agents/hooks/okf-skills/hooks/okf-stop-check.sh"',
    "timeout": 15,
}


def _git(cwd: Path, *args: str) -> None:
    """Run git quietly in ``cwd``; fail the test when it fails."""
    subprocess.run(
        ["git", "-c", "user.email=t@e.invalid", "-c", "user.name=t", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


def _stop_repo(tmp_path: Path, *, enforced: bool = True, script: bool = True) -> Path:
    """A git repository with a bundle, okf's script where APM puts it and the plugin folder."""
    repo = tmp_path / "stop-repo"
    (repo / ".okf").mkdir(parents=True)
    upkeep = "upkeep: enforced\n" if enforced else ""
    (repo / ".okf" / "index.md").write_text(f"---\ntype: index\n{upkeep}---\n\n# B\n")
    (repo / "README.md").write_text("# r\n")
    if script:
        target = repo / antigravity.OKF_STOP_SCRIPT
        target.parent.mkdir(parents=True)
        shutil.copy(OKF_STOP, target)
    (repo / ".agents").mkdir(exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "init")
    return repo


def _run_stop(repo: Path, stdin: str) -> subprocess.CompletedProcess[str]:
    """Run the package's Stop handler as agy does: sh -c, in .agents/, which holds the hooks.json."""
    return subprocess.run(
        ["sh", "-c", antigravity.STOP_COMMAND],
        cwd=repo / ".agents",
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
        env={"PATH": "/usr/bin:/bin", "HOME": str(repo)},
    )


def _stop_input(execution: int) -> str:
    """The JSON agy sends a Stop hook, as spike:antigravity-okf-stop-hook/2 logged it."""
    return json.dumps(
        {"conversationId": "c", "executionNum": execution, "fullyIdle": True}
    )


def _okf_reason() -> str:
    """The reason okf's script gives when it blocks."""
    text = OKF_STOP.read_text()
    block = json.loads(text[text.index('{"decision"') : text.rindex("}") + 1])
    return block["reason"]


def test_okf_stop_continues_on_the_first_stop_with_okf_reason(tmp_path: Path) -> None:
    repo = _stop_repo(tmp_path)
    (repo / "README.md").write_text("# changed\n")

    proc = _run_stop(repo, _stop_input(0))

    assert proc.returncode == 0
    assert json.loads(proc.stdout) == {"decision": "continue", "reason": _okf_reason()}


@pytest.mark.parametrize(
    ("enforced", "change", "execution"),
    [
        (True, True, 1),
        (True, False, 0),
        (False, True, 0),
    ],
)
def test_okf_stop_prints_nothing_to_do_otherwise(
    tmp_path: Path, enforced: bool, change: bool, execution: int
) -> None:
    repo = _stop_repo(tmp_path, enforced=enforced)
    if change:
        (repo / "README.md").write_text("# changed\n")

    proc = _run_stop(repo, _stop_input(execution))

    assert proc.returncode == 0
    assert json.loads(proc.stdout) == {}


def test_okf_stop_with_bundle_change_lets_it_stop(tmp_path: Path) -> None:
    repo = _stop_repo(tmp_path)
    (repo / "README.md").write_text("# changed\n")
    (repo / ".okf" / "index.md").write_text(
        "---\ntype: index\nupkeep: enforced\n---\n\n# C\n"
    )

    proc = _run_stop(repo, _stop_input(0))

    assert (proc.returncode, json.loads(proc.stdout)) == (0, {})


@pytest.mark.parametrize("broken", ["missing", "fails"])
def test_okf_stop_never_blocks_without_a_working_script(
    tmp_path: Path, broken: str
) -> None:
    repo = _stop_repo(tmp_path, script=broken != "missing")
    if broken == "fails":
        (repo / antigravity.OKF_STOP_SCRIPT).write_text("echo not json; exit 3\n")
    (repo / "README.md").write_text("# changed\n")

    proc = _run_stop(repo, _stop_input(0))

    assert (proc.returncode, json.loads(proc.stdout)) == (0, {})


def _apm_hooks(repo: Path) -> Path:
    return repo / antigravity.APM_HOOKS


def test_apm_okf_hook_removed_keeping_every_other_hook(
    repo: Path, fakes: FakeTools
) -> None:
    other = {"type": "command", "command": "echo other", "timeout": 5}
    grouped = {"matcher": "*", "hooks": [other]}
    path = _apm_hooks(repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "apm": {"Stop": [APM_OKF_HANDLER]},
                "mixed": {"Stop": [APM_OKF_HANDLER, other], "PreToolUse": [grouped]},
                "theirs": {"SessionStart": [other]},
                "empty": {},
            }
        )
    )

    _install()

    assert json.loads(path.read_text()) == {
        "mixed": {"Stop": [other], "PreToolUse": [grouped]},
        "theirs": {"SessionStart": [other]},
        "empty": {},
    }
    before = path.read_bytes()
    _install()
    assert path.read_bytes() == before


def test_apm_okf_hook_missing_file_stays_missing(repo: Path, fakes: FakeTools) -> None:
    _install()

    assert not _apm_hooks(repo).exists()


def test_apm_okf_hook_unparsable_file_left_alone(repo: Path, fakes: FakeTools) -> None:
    path = _apm_hooks(repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not json okf-stop-check.sh")

    _install()

    assert path.read_text() == "not json okf-stop-check.sh"


def test_okf_stop_docs_name_the_hook_and_the_check() -> None:
    decision = DECISIONS / "0018-kmctl-runs-okf-s-stop-check-for-antigravity.md"
    text = _flat(decision.read_text())
    for term in ("executionNum", "continue", "block", "repository root", "hooks.json"):
        assert term in text, term
    assert "0018" in _decision().read_text()
    for path in (COMMANDS, INSTALL_HOW_TO):
        assert "Stop" in path.read_text(), path.name
    commands = COMMANDS.read_text()
    assert ".agents/hooks.json" in commands
    assert "antigravity.apm-hooks" in commands


# apm-hands-back r3: install writes only the agents and the okf Stop fix -------------


def test_hands_back_patch_writes_no_hook_mcp_or_rules(
    repo: Path, fakes: FakeTools
) -> None:
    _install(harnesses=("claude", "antigravity"))

    assert not (repo / ".claude" / "settings.json").exists()
    assert not (repo / ".mcp.json").exists()
    assert sorted(_files(repo / ".agents")) == [
        f"plugins/kmctl/{name}" for name in PLUGIN_FILES
    ]
    assert fakes.calls("uvx") == []


def test_hands_back_okf_handler_dropped_wrapper_kept(
    repo: Path, fakes: FakeTools
) -> None:
    wrapper = {"type": "command", "command": antigravity.STOP_COMMAND, "timeout": 10}
    start = {"type": "command", "command": antigravity.HOOK_COMMAND, "timeout": 10}
    path = _apm_hooks(repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"apm": {"SessionStart": [start], "Stop": [APM_OKF_HANDLER, wrapper]}}
        )
    )

    _install()

    assert json.loads(path.read_text()) == {
        "apm": {"SessionStart": [start], "Stop": [wrapper]}
    }
    assert antigravity.hook_present(repo)
    assert not antigravity.apm_okf_stop_present(repo)
