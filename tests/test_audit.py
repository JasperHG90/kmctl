"""The audit is read-only by its tool list, and its findings have one shape (ADR 0005, I2)."""

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "apm" / ".apm"
AGENT = PACKAGE / "agents" / "kmctl-auditor.md"
SKILLS = PACKAGE / "skills"
#: The files that set or read the folder the CI audit takes the skills and agent from.
AUDIT_FILES = (
    "action.yml",
    ".github/workflows/knowledge-audit.yml",
    "action/agent.py",
)


def _front_matter(path: Path) -> dict:
    text = path.read_text()
    return yaml.safe_load(text[4 : text.index("\n---", 4)])


def test_auditor_tools_are_read_only() -> None:
    tools = _front_matter(AGENT).get("tools")

    assert tools is not None, "no tools line means the agent inherits every tool"
    assert sorted(t.strip() for t in tools.split(",")) == ["Glob", "Grep", "Read"]


def test_findings_sample_has_shape() -> None:
    sample = json.loads(
        (SKILLS / "audit" / "evals" / "sample-findings.json").read_text()
    )

    assert isinstance(sample, list) and sample
    for finding in sample:
        assert set(finding) == {
            "concept",
            "path",
            "review",
            "verdict",
            "summary",
            "evidence",
        }
        assert finding["review"] in {"architecture", "decision", "practice"}
        assert finding["verdict"] in {"holds", "drifted", "unsure"}
        assert finding["evidence"] and all(
            re.fullmatch(r"[^\s:]+:\d+", e) for e in finding["evidence"]
        )


def test_audit_skill_routes() -> None:
    text = (SKILLS / "audit" / "SKILL.md").read_text()

    assert "kmctl review due --json" in text
    for section in ("architecture/", "decisions/", "practices/"):
        assert section in text
    assert "batch" in text.lower()
    assert "kmctl-auditor" in text


def test_review_skills_exist() -> None:
    prompt = AGENT.read_text()

    for name in ("architecture-review", "decision-log-review", "practices-review"):
        assert (SKILLS / name / "SKILL.md").is_file(), name
        assert name in prompt, name


def test_audit_paths_read_the_apm_package() -> None:
    """The CI audit takes the skills and agent from apm/.apm, and nothing names plugin/."""
    texts = {rel: (ROOT / rel).read_text() for rel in AUDIT_FILES}

    assert [rel for rel, text in texts.items() if "plugin/" in text] == []
    script = texts["action/agent.py"]
    assert 'PACKAGE = HERE.parent / "apm" / ".apm"' in script
    assert 'DEFAULT_SKILLS = PACKAGE / "skills"' in script
    assert 'PROMPTS = HERE / "prompts"' in script
    assert (PACKAGE / "skills").is_dir() and AGENT.is_file()
