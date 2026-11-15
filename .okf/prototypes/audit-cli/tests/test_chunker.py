"""Tests for cutting the bundle into chunks."""

import pathlib as plb

import pytest

from audit_cli.processing.chunker import BundleChunker, SentenceSplitter


@pytest.mark.parametrize(
    ("text", "units"),
    [
        ("One. Two sentences here.", ["One. Two sentences here."]),
        ("The first holds. The second holds too.", ["The first holds.", "The second holds too."]),
        ("- An item here.\n- Another item here.", ["- An item here.", "- Another item here."]),
        ("Before it.\n\n```\ncode block\n```\n\nAfter it.", ["Before it.", "```\ncode block\n```", "After it."]),
        ("| a | b |\n| - | - |", ["| a | b |\n| - | - |"]),
    ],
)
def test_sentence_splitter(text: str, units: list[str]) -> None:
    """Sentences split, a short fragment joins the next, and a code block or table stays whole."""
    assert SentenceSplitter().split(text) == units


def test_chunks_only_live_concepts_outside_skipped_folders(repo: plb.Path) -> None:
    """index.md, deprecated concepts and the prototypes folder give no chunks."""
    chunks = list(BundleChunker(SentenceSplitter()).chunks(repo / ".okf"))
    assert {c.concept for c in chunks} == {"decisions/0001-use-a-queue"}
    assert [c.id for c in chunks] == [
        "decisions/0001-use-a-queue#context",
        "decisions/0001-use-a-queue#decision",
        "decisions/0001-use-a-queue#correction-2026-01-02",
    ]


def test_a_chunk_carries_earlier_sections_and_corrections(repo: plb.Path) -> None:
    """A later section sees earlier sentences labelled [s.n], and every non-correction section sees the correction."""
    context, decision, correction = BundleChunker(SentenceSplitter()).chunks(repo / ".okf")
    assert decision.earlier_ids == [context.id]
    assert "[1.1] The CLI writes jobs to `jobs.db`." in decision.earlier
    assert "retries twice" in decision.corrections
    assert correction.corrections == ""


def test_the_key_changes_only_with_what_the_model_sees(repo: plb.Path) -> None:
    """Rechunking unchanged text gives the same keys; editing a sentence changes that chunk's key."""
    chunker = BundleChunker(SentenceSplitter())
    before = {c.id: c.cache_key for c in chunker.chunks(repo / ".okf")}
    path = repo / ".okf" / "decisions" / "0001-use-a-queue.md"
    path.write_text(path.read_text().replace("a failed job three times", "a failed job four times"))
    after = {c.id: c.cache_key for c in chunker.chunks(repo / ".okf")}
    assert before["decisions/0001-use-a-queue#context"] == after["decisions/0001-use-a-queue#context"]
    assert before["decisions/0001-use-a-queue#decision"] != after["decisions/0001-use-a-queue#decision"]
