"""The decision-gaps skill: it ships with kmctl, reports without writing, and keeps the skill-creator's tests (ADR 0007, ADR 0047)."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from kmctl import plugin

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "packages" / "kmctl" / "apm" / ".apm" / "skills" / "decision-gaps"
EVALS = SKILL / "evals"
CASES = (
    "known-range-finds-labelled-gaps",
    "default-range-recent",
    "write-named-record-no-scan",
)
HOW_TO = ROOT / "docs" / "how-to" / "find-unrecorded-decisions.md"


def _front_matter(path: Path) -> dict:
    """The YAML front matter of a markdown file."""
    text = path.read_text()
    return yaml.safe_load(text.split("---\n", 2)[1])


def _body(path: Path) -> str:
    """A markdown file's body after its front matter, whitespace collapsed."""
    return " ".join(path.read_text().split("---\n", 2)[2].split())


def test_skill_ships_with_valid_front_matter() -> None:
    """SKILL.md names itself decision-gaps and its description says when to use it and when not."""
    meta = _front_matter(SKILL / "SKILL.md")

    assert meta["name"] == "decision-gaps"
    assert "kmctl decision candidates" in meta["description"]
    assert "Use this whenever" in meta["description"]
    assert "Not for writing a record" in meta["description"]
    assert (plugin.skills_dir() / "decision-gaps" / "SKILL.md").is_file()


def test_skill_body_lists_judges_reports_and_writes_nothing() -> None:
    """The body runs the verb, judges every change in batches with one shared reference, asks to narrow a long range, and writes nothing."""
    body = _body(SKILL / "SKILL.md")

    for needle in (
        "kmctl decision candidates",
        "kmctl decision candidates --json",
        "judge every change",
        "batches of about ten",
        "[references/judging.md](references/judging.md)",
        "subagent",
        "Past about forty, ask whether to go ahead or narrow the range with `--since`",
        "Records with no change of their own",
        "**It writes nothing.**",
        "kmctl new decision",
        "Instead of:",
    ):
        assert needle in body, needle


def test_judging_reference_defines_the_answers() -> None:
    """references/judging.md defines covered (recorded counts), missing, not a decision and record-only, and returns one block per change."""
    text = " ".join((SKILL / "references" / "judging.md").read_text().split())

    for needle in (
        "This answer wins over covered.",
        "**covered**: otherwise, `recorded` is not empty",
        "**missing**",
        "**not a decision**",
        "**record-only**",
        "still missing when no record covers the practice itself",
        "which checks are required and how CI jobs are split",
        "promises to users about stability or compatibility",
        "One block per change, every change in the batch",
    ):
        assert needle in text, needle


def test_install_pages_count_eight_skills() -> None:
    """Both install pages count eight kmctl skills, and the APM page names decision-gaps."""
    apm = (ROOT / "docs" / "how-to" / "install-kmctl-with-apm.md").read_text()
    plugin_page = (
        ROOT / "docs" / "how-to" / "install-the-plugin-and-the-ci-action.md"
    ).read_text()

    assert "seven skills" not in apm + plugin_page
    assert "kmctl's eight skills" in apm and "`decision-gaps`" in apm
    assert plugin_page.count("kmctl's eight skills") == 2


def test_evals_are_skill_creator_case_folders() -> None:
    """Each test case is a folder with prompt.md, case.yaml and at least one grader in the skill-creator's format."""
    for name in CASES:
        case = EVALS / name
        meta = yaml.safe_load((case / "case.yaml").read_text())
        graders = sorted((case / "graders").glob("*.md"))
        prompt = (case / "prompt.md").read_text()

        assert meta["schema_version"] == "1.1" and meta["name"] == name
        assert meta["expected_outcome"].strip()
        assert prompt.startswith("---\n") and prompt.split("---\n", 2)[2].strip()
        assert graders
        for grader in graders:
            assert _front_matter(grader) == {
                "type": "llm",
                "focus": "trace",
                "weight": 1,
            }


def test_evals_cover_a_named_range_no_range_and_a_record_to_write() -> None:
    """The known-answer case names a range holding labelled gaps, the default case names none, and the write case must not scan."""
    known = (EVALS / CASES[0] / "prompt.md").read_text()
    default = (EVALS / CASES[1] / "prompt.md").read_text()
    write = " ".join(p.read_text() for p in (EVALS / CASES[2] / "graders").glob("*.md"))

    assert "since commit 2cf55821c" in known
    assert not re.search(r"since (commit|v\d)", default)
    assert "did not run kmctl decision candidates" in write


def test_evals_results_record_each_case_and_the_known_answer_counts() -> None:
    """results.md has a section per case, the known-answer counts against the labels, and whether .okf/ stayed unchanged."""
    results = (EVALS / "results.md").read_text()

    for name in CASES:
        assert f"## {name}" in results
    assert "labels.json" in results
    assert re.search(r"labelled gaps found: \d+ of \d+", results)
    assert re.search(r"labelled false alarms raised: \d+ of \d+", results)
    assert ".okf/ unchanged" in results


def test_how_to_page_runs_the_skill_and_leaves_records_to_the_user() -> None:
    """The how-to page asks the agent, says the skill writes nothing and the user records what they choose; the index lists it."""
    body = _body(HOW_TO)
    index = (ROOT / "docs" / "how-to" / "README.md").read_text()

    assert "`decision-gaps`" in body
    assert "It writes nothing" in body
    assert "kmctl new decision" in body
    assert "you read the report and decide which findings become records" in body
    assert "(find-unrecorded-decisions.md)" in index
