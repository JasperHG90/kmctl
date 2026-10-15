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
