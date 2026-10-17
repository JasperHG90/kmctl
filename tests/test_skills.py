"""The package's skills have the layout their tickets promise."""

from pathlib import Path

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
