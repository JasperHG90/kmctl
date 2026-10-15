"""The plugin's skills have the layout their tickets promise."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "plugin" / "skills"


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
