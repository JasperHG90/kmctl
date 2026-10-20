"""The Hermes issue triage: a short comment and allowed labels (ADR 0035)."""

from __future__ import annotations

from pathlib import Path

import yaml

from scripts.hermes_triage import MAX_CHARS, allowed_labels, cut, parse

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "hermes-issue-triage.yaml"
PROMPT = ROOT / ".github" / "prompts" / "issue-triage-system.md"
AREAS = ["src", "action", "apm", "starter", "tests", "scripts", "docs", "okf", "ci"]
TRAILER = (
    '<!-- hermes-triage: {"priority":"high","labels":["bug","area/src","made-up"]} -->'
)


def test_cut_keeps_a_long_comment_within_800_characters_at_a_line_break() -> None:
    """A 2000-character response is cut to at most 800 characters, at the end of a line."""
    lines = [f"- line {i}: " + "x" * 40 for i in range(40)]
    text = "\n".join(lines)
    assert len(text) > 2000

    out = cut(text)

    assert MAX_CHARS == 800
    assert len(out) <= MAX_CHARS
    body = out.rsplit("\n\n", 1)[0]
    assert all(line in lines for line in body.splitlines())


def test_cut_leaves_a_short_comment_alone() -> None:
    """A comment within the limit is posted as written."""
    assert cut("### Summary\nShort.") == "### Summary\nShort."


def test_parse_strips_the_trailer_and_returns_allowed_labels() -> None:
    """The trailer leaves the comment; only allowed labels, with priority first, are returned."""
    comment, labels = parse(f"### Summary\nA bug.\n\n{TRAILER}\n", AREAS)

    assert "hermes-triage" not in comment
    assert comment == "### Summary\nA bug."
    assert labels == ["priority/high", "bug", "area/src"]


def test_parse_cuts_the_comment_after_removing_the_trailer() -> None:
    """A long comment is cut, and its labels still come from the trailer at its end."""
    long = "\n".join("y" * 60 for _ in range(50))

    comment, labels = parse(f"{long}\n{TRAILER}", AREAS)

    assert len(comment) <= MAX_CHARS
    assert labels == ["priority/high", "bug", "area/src"]


def test_parse_without_a_trailer_returns_no_labels() -> None:
    """No trailer, no labels: the comment is still posted."""
    assert parse("Just text.", AREAS) == ("Just text.", [])


def test_allowed_labels_cover_type_area_and_priority() -> None:
    """The allowlist is the five types, one area/* per area and the four priorities."""
    allowed = allowed_labels(["src", "ci"])

    assert {"bug", "enhancement", "rfc", "question", "documentation"} <= allowed
    assert {"area/src", "area/ci", "priority/low", "priority/critical"} <= allowed
    assert "area/tests" not in allowed


def test_the_triage_prompt_asks_for_under_200_tokens() -> None:
    """The system prompt states the 200-token limit and that the workflow cuts past it."""
    text = PROMPT.read_text()

    assert "200 tokens" in text
    assert "800 characters" in text


def test_triage_areas_match_kmctl_s_top_level_folders() -> None:
    """Each area is a top-level folder, except okf (.okf/) and ci (.github/)."""
    env = yaml.safe_load(WORKFLOW.read_text())["jobs"]["triage"]["env"]
    areas = env["TRIAGE_AREAS"].split()

    assert areas == AREAS
    folders = {"okf": ".okf", "ci": ".github"}
    for area in areas:
        assert (ROOT / folders.get(area, area)).is_dir(), area
