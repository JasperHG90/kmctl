"""The package's skills have the layout their tickets promise."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "packages" / "kmctl" / "apm" / ".apm" / "skills"


def test_write_docs_skill_layout() -> None:
    skill = SKILLS / "write-docs"
    text = (skill / "SKILL.md").read_text()

    assert text.startswith("---\nname: write-docs\n")
    for doc_type in ("tutorial", "how-to", "reference", "explanation"):
        assert (skill / "references" / f"{doc_type}.md").is_file(), doc_type
    assert "kmctl new doc" in text
    assert (skill / "evals" / "evals.json").is_file()


def test_handoff_and_continue_skills_exist() -> None:
    handoff = (SKILLS / "handoff" / "SKILL.md").read_text()
    resume = (SKILLS / "continue" / "SKILL.md").read_text()

    assert handoff.startswith("---\nname: handoff\n")
    assert resume.startswith("---\nname: continue\n")
    assert '${CLAUDE_CODE_SESSION_ID:+--key "$CLAUDE_CODE_SESSION_ID"}' in handoff
    assert "only when `CLAUDE_CODE_SESSION_ID` is set and not empty" in handoff
    assert "kmctl handoffs --json" in resume
    assert "multiSelect: true" in resume


def test_write_docs_grader_joins_metadata(tmp_path: Path) -> None:
    import json
    import subprocess
    import sys

    evals = json.loads((SKILLS / "write-docs" / "evals" / "evals.json").read_text())
    reference = next(e for e in evals["evals"] if e["doc_type"] == "reference")
    it = tmp_path / "iteration-1"
    good = it / "some-free-name" / "with_skill" / "repo" / "docs"
    (good / "reference").mkdir(parents=True)
    (good / "README.md").write_text("# Docs\n\n- [Reference](reference/README.md)\n")
    (good / "reference" / "README.md").write_text("# Reference\n\n- [Cmds](cmds.md)\n")
    (good / "reference" / "cmds.md").write_text("# Cmds\n")
    (it / "some-free-name" / "eval_metadata.json").write_text(
        json.dumps(
            {
                "eval_id": reference["id"],
                "eval_name": "x",
                "prompt": reference["prompt"],
            }
        )
    )
    (it / "no-metadata" / "with_skill" / "repo" / "docs").mkdir(parents=True)
    wrong = it / "wrong-prompt" / "with_skill" / "repo" / "docs"
    wrong.mkdir(parents=True)
    (it / "wrong-prompt" / "eval_metadata.json").write_text(
        json.dumps(
            {"eval_id": reference["id"], "eval_name": "y", "prompt": "something else"}
        )
    )
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    (fake_bin / "kmctl").write_text("#!/bin/sh\necho 'all checks passed'\nexit 0\n")
    (fake_bin / "kmctl").chmod(0o755)

    proc = subprocess.run(
        [sys.executable, str(SKILLS / "write-docs" / "evals" / "grade.py"), str(it)],
        env={"PATH": "/usr/bin:/bin", "KMCTL_BIN": str(fake_bin)},
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    grading = json.loads(
        (it / "some-free-name" / "with_skill" / "grading.json").read_text()
    )
    assert grading["summary"]["passed"] == grading["summary"]["total"]
    assert "no-metadata" in proc.stdout and "skipped" in proc.stdout
    assert "wrong-prompt" in proc.stdout
    assert not (it / "no-metadata" / "with_skill" / "grading.json").exists()
    assert not (it / "wrong-prompt" / "with_skill" / "grading.json").exists()


AGENTS = ROOT / "packages" / "kmctl" / "apm" / ".apm" / "agents"
#: kmaudit's APM package: its skills, and its agents in the Claude-only sub-package.
KMAUDIT_SKILLS = ROOT / "packages" / "kmaudit" / "apm" / ".apm" / "skills"
KMAUDIT_AGENTS = ROOT / "packages" / "kmaudit" / "apm" / "claude" / ".apm" / "agents"
KMAUDIT_FILES = [
    KMAUDIT_SKILLS / "extract-claims" / "SKILL.md",
    KMAUDIT_AGENTS / "kmaudit-claims-extractor.md",
    KMAUDIT_SKILLS / "write-checks" / "SKILL.md",
    KMAUDIT_AGENTS / "kmaudit-check-writer.md",
]
#: ``kmaudit`` followed by one of its CLI verb groups, the way a shell command starts.
COMMAND = re.compile(
    r"\bkmaudit +(?:claims|checks|guard|judge|coverage|namespaces|ui|briefing|mcp)\b"
)
#: Code: fenced blocks and inline code spans, where a file names a command to run.
CODE = re.compile(r"```.*?```|`[^`\n]+`", re.DOTALL)
#: A name in code that looks like a kmaudit MCP tool: a verb group, then a verb.
TOOL = re.compile(r"`(?:mcp__kmaudit__)?((?:claims|checks)_[a-z]+)`")


def _ids(path: Path) -> str:
    """A skill's folder name, or an agent's file stem."""
    return path.parent.name if path.name == "SKILL.md" else path.stem


def _server_tools() -> set[str]:
    """The tools kmaudit's MCP server lists."""
    import asyncio

    from kmaudit.mcp_server import server

    return {t.name for t in asyncio.run(server.list_tools())}


@pytest.mark.parametrize("path", KMAUDIT_FILES, ids=_ids)
def test_names_no_kmaudit_shell_command(path: Path) -> None:
    """The skill or agent drives kmaudit through its MCP tools, not a shell (ADR 0043)."""
    code = "\n".join(CODE.findall(path.read_text()))

    assert COMMAND.findall(code) == []


@pytest.mark.parametrize("path", KMAUDIT_FILES, ids=_ids)
def test_every_named_mcp_tool_exists(path: Path) -> None:
    """Each kmaudit tool the skill or agent names is one the server lists (skills-name-only-real-verbs)."""
    named = set(TOOL.findall(path.read_text()))

    assert named, "the file names no kmaudit tool"
    assert named <= _server_tools()


@pytest.mark.parametrize(
    "path",
    [
        KMAUDIT_SKILLS / "extract-claims" / "SKILL.md",
        KMAUDIT_SKILLS / "write-checks" / "SKILL.md",
    ],
    ids=_ids,
)
def test_skill_works_the_batch_itself_where_no_agent_exists(path: Path) -> None:
    """In Antigravity and OpenCode, which get no agents, the skill does each batch with the same tools."""
    text = path.read_text()
    group = "claims" if "extract-claims" in path.parts else "checks"

    assert "When the agent is not available (Antigravity, OpenCode)" in text
    assert f"`{group}_submit`" in text
    assert "namespace" in text


@pytest.mark.parametrize("path", KMAUDIT_FILES[1::2], ids=_ids)
def test_agent_submits_to_the_namespace_folder(path: Path) -> None:
    """An agent's submit names its namespace through folder, so a docs/ answer never lands in .okf (ADR 0043)."""
    text = path.read_text()

    assert "joined" in text and "`namespace`" in text
    assert (
        f"`by` set\n   to `{path.stem}`" in text or f"`by` set to `{path.stem}`" in text
    )


@pytest.mark.parametrize(
    "path", sorted(KMAUDIT_SKILLS.glob("*/evals/evals.json")), ids=lambda p: p.parts[-3]
)
def test_skill_evals_follow_the_mcp_flow(path: Path) -> None:
    """The evals expect the renamed agent and the MCP tools, and test the no-agent harness."""
    import json

    text = path.read_text()
    evals = json.loads(text)["evals"]

    assert "kmctl-" not in text
    assert COMMAND.findall(text) == []
    assert any(e["name"] == "no-agent-harness" for e in evals)


@pytest.mark.parametrize(
    "path",
    sorted(SKILLS.glob("*/SKILL.md"))
    + sorted(AGENTS.glob("*.md"))
    + sorted(KMAUDIT_SKILLS.glob("*/SKILL.md"))
    + sorted(KMAUDIT_AGENTS.glob("*.md")),
    ids=_ids,
)
def test_front_matter_parses_with_a_name_and_description(path: Path) -> None:
    """A description with an unquoted ': ' breaks the YAML, and every harness then skips the skill."""
    import yaml

    meta = yaml.safe_load(path.read_text().split("---")[1])

    assert isinstance(meta, dict) and meta.get("name") and meta.get("description")
