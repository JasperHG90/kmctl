"""Tests for comparing a bundle's text with the database."""

import asyncio
import pathlib as plb

from helpers import FakeExtractor, claim, make_chunk
from test_runner import run_of

from audit_cli.claims.diff import diff
from audit_cli.claims.runner import ClaimsRunner
from audit_cli.db import Store
from audit_cli.processing.chunker import Chunk

RUNS = [("a", "model-a", "")]


def extracted(store: Store, chunks: list[Chunk]) -> None:
    """Store the chunks and extract them with one fake run."""
    store.replace_chunks(chunks)
    fake = FakeExtractor({c.id: [claim(1, "x")] for c in chunks})
    asyncio.run(ClaimsRunner(store, [run_of("a", fake)]).run(chunks))


def test_everything_is_new_without_a_database() -> None:
    """With nothing stored, every section is new and needs every run."""
    with Store(None) as store:
        report = diff(store, [make_chunk("c#one")], None, RUNS)
    assert not report.up_to_date and report.pending_calls == 1
    assert report.concepts[0].status == "new"


def test_an_extracted_bundle_is_up_to_date(tmp_path: plb.Path) -> None:
    """After extraction the same text diffs clean, with no calls to make."""
    chunks = [make_chunk("c#one"), make_chunk("c#two")]
    with Store(tmp_path / "audit.sqlite") as store:
        extracted(store, chunks)
        report = diff(store, chunks, None, RUNS)
    assert report.up_to_date and report.pending_calls == 0


def test_edited_text_shows_as_changed_with_sentence_counts(tmp_path: plb.Path) -> None:
    """An edited section is changed, with the sentences added and removed, and needs its runs again."""
    old = make_chunk("c#one", ["Keep this one.", "Drop this one."])
    new = make_chunk("c#one", ["Keep this one.", "A new sentence.", "Another new one."])
    with Store(tmp_path / "audit.sqlite") as store:
        extracted(store, [old])
        report = diff(store, [new], None, RUNS)
    (entry,) = report.concepts[0].chunks
    assert (entry.status, entry.sentences_added, entry.sentences_removed, entry.pending_runs) == (
        "changed",
        2,
        1,
        ["a"],
    )


def test_a_new_run_makes_extracted_text_incomplete(tmp_path: plb.Path) -> None:
    """Adding a run to the settings leaves unchanged text incomplete until that run is made."""
    chunk = make_chunk()
    with Store(tmp_path / "audit.sqlite") as store:
        extracted(store, [chunk])
        report = diff(store, [chunk], None, [*RUNS, ("b", "model-b", "")])
    assert report.concepts[0].status == "incomplete" and report.pending_calls == 1


def test_a_gone_section_is_removed_but_only_within_scope(tmp_path: plb.Path) -> None:
    """A section no longer in the text is removed; a single-file diff ignores other concepts."""
    one, two, other = make_chunk("c#one"), make_chunk("c#two"), make_chunk("d#one")
    with Store(tmp_path / "audit.sqlite") as store:
        extracted(store, [one, two, other])
        whole = diff(store, [one, other], None, RUNS)
        single = diff(store, [other], {"d"}, RUNS)
    assert [(c.concept, c.status) for c in whole.concepts] == [("c", "changed"), ("d", "up to date")]
    assert [c.status for c in whole.concepts[0].chunks] == ["up to date", "removed"]
    assert single.up_to_date
