"""The package's skills have the layout their tickets promise."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "apm" / ".apm" / "skills"


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


AGENTS = ROOT / "apm" / ".apm" / "agents"
#: ``kmaudit`` followed by its words and flags, up to the first word that is neither.
COMMAND = re.compile(r"\bkmaudit((?: +(?:[a-z][a-z-]*|--[a-z][a-z-]*|-(?= )))+)")
#: Code: fenced blocks and inline code spans, where a file names a command to run.
CODE = re.compile(r"```.*?```|`[^`\n]+`", re.DOTALL)


def _named_commands(text: str) -> list[list[str]]:
    """Each ``kmaudit ...`` command a skill or agent names in its code, as its words."""
    code = "\n".join(CODE.findall(text))
    return [m.group(1).split() for m in COMMAND.finditer(code)]


@pytest.mark.parametrize(
    "path",
    [
        SKILLS / "extract-claims" / "SKILL.md",
        AGENTS / "kmctl-claims-extractor.md",
        SKILLS / "write-checks" / "SKILL.md",
        AGENTS / "kmctl-check-writer.md",
    ],
    ids=lambda p: p.parent.name if p.name == "SKILL.md" else p.stem,
)
def test_every_named_kmaudit_command_exists(path: Path) -> None:
    """Each kmaudit command and flag the skill or agent names is in kmaudit's CLI (skills-name-only-real-verbs)."""
    from kmaudit.cli import app
    from typer.main import get_command

    named = _named_commands(path.read_text())
    assert named, "the file names no kmaudit command"
    for words in named:
        command = get_command(app)
        for word in (w for w in words if not w.startswith("--")):
            if not hasattr(command, "commands"):
                break  # a verb's argument
            assert word in command.commands, f"kmaudit {' '.join(words)}: no {word!r}"
            command = command.commands[word]
        known = {o for p in command.params for o in p.opts}
        flags = {w for w in words if w.startswith("--")}
        assert flags <= known, f"kmaudit {' '.join(words)}: {flags - known}"


#: The kmaudit verbs that write, which must name their namespace.
WRITES = re.compile(r"\bkmaudit (?:claims submit|checks try|checks submit)\b[^\n`]*")


@pytest.mark.parametrize(
    "path",
    [
        SKILLS / "extract-claims" / "SKILL.md",
        AGENTS / "kmctl-claims-extractor.md",
        SKILLS / "write-checks" / "SKILL.md",
        AGENTS / "kmctl-check-writer.md",
    ],
    ids=lambda p: p.parent.name if p.name == "SKILL.md" else p.stem,
)
def test_writes_name_their_namespace_with_path(path: Path) -> None:
    """An agent's submit or try passes --path, or a docs/ answer lands in .okf (ADR 0043)."""
    code = "\n".join(CODE.findall(path.read_text()))
    commands = [m.group(0) for m in WRITES.finditer(code)]

    assert commands, "the file names no kmaudit write"
    assert [c for c in commands if "--path" not in c] == []


@pytest.mark.parametrize(
    "path",
    sorted(SKILLS.glob("*/SKILL.md")) + sorted(AGENTS.glob("*.md")),
    ids=lambda p: p.parent.name if p.name == "SKILL.md" else p.stem,
)
def test_front_matter_parses_with_a_name_and_description(path: Path) -> None:
    """A description with an unquoted ': ' breaks the YAML, and every harness then skips the skill."""
    import yaml

    meta = yaml.safe_load(path.read_text().split("---")[1])

    assert isinstance(meta, dict) and meta.get("name") and meta.get("description")
