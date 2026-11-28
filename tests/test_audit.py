"""The audit is read-only by its tool list, and its findings have one shape (ADR 0005, I2)."""

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages" / "kmctl" / "apm" / ".apm"
AGENT = PACKAGE / "agents" / "kmctl-auditor.md"
SKILLS = PACKAGE / "skills"
#: The files that run the CI agent (ADR 0060).
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


def test_ci_agent_ships_its_one_prompt_and_no_skills() -> None:
    """The CI agent reads only its own prompt, next to it, and no skills or old paths (ADR 0060)."""
    texts = {rel: (ROOT / rel).read_text() for rel in AUDIT_FILES}

    assert [rel for rel, text in texts.items() if "plugin/" in text] == []
    script = texts["action/agent.py"]
    assert 'PROMPT = HERE / "prompt.md"' in script
    assert (ROOT / "action" / "prompt.md").is_file()
    assert not (ROOT / "action" / "prompts").exists()
    for gone in ("DEFAULT_SKILLS", "PROMPTS", "SKILL.md"):
        assert gone not in script, gone
