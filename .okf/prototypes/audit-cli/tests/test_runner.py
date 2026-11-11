"""Tests for running extraction over chunks and storing merged claims."""

import asyncio
import pathlib as plb
from typing import Any, cast

from helpers import FakeExtractor, FakeLLM, FakeStructured, claim, make_chunk, note
from langchain_openai import ChatOpenAI

from audit_cli.claims.extractor import ClaimExtractor
from audit_cli.claims.models import Verdicts
from audit_cli.claims.runner import ClaimsRunner, Run, pending
from audit_cli.db import Store


def run_of(label: str, fake: FakeExtractor) -> Run:
    """Wrap a fake extractor as a run."""
    name, _, salt = label.partition("@")
    return Run(label=label, model="model-" + name, salt=salt, extractor=cast(ClaimExtractor, cast(Any, fake)))


def test_later_runs_only_add_claims_for_skipped_sentences(tmp_path: plb.Path) -> None:
    """The first run's claims stand; the second adds only sentence 2, which the first skipped."""
    chunk = make_chunk()
    first = FakeExtractor({chunk.id: [claim(1, "The CLI writes jobs.db")]})
    second = FakeExtractor({chunk.id: [claim(1, "A rewording"), claim(2, "Workers retry twice")]})
    with Store(tmp_path / "audit.sqlite") as store:
        store.replace_chunks([chunk])
        report = asyncio.run(ClaimsRunner(store, [run_of("a", first), run_of("b", second)]).run([chunk]))
        stored = store.claims()
    assert [(c.claim, c.run) for c in stored] == [("The CLI writes jobs.db", "a"), ("Workers retry twice", "b")]
    assert report.fresh == 2 and report.tokens_in == 20


def test_a_second_pass_reads_the_database(tmp_path: plb.Path) -> None:
    """Results stored for unchanged chunks are reused, so no model is called again."""
    chunk = make_chunk()
    fake = FakeExtractor({chunk.id: [claim(1, "x")]})
    with Store(tmp_path / "audit.sqlite") as store:
        store.replace_chunks([chunk])
        runner = ClaimsRunner(store, [run_of("a", fake), run_of("a@2", fake)])
        assert pending(store, [chunk], [("model-a", ""), ("model-a", "2")]) == 2
        asyncio.run(runner.run([chunk]))
        again = asyncio.run(runner.run([chunk]))
        assert pending(store, [chunk], [("model-a", ""), ("model-a", "2")]) == 0
    assert fake.calls == 2 and again.cached == 2 and again.fresh == 0


def test_a_first_run_that_fails_twice_marks_the_chunk_failed(tmp_path: plb.Path) -> None:
    """The first run is tried twice; after two failures the chunk is reported and keeps no claims."""
    chunk = make_chunk()
    with Store(tmp_path / "audit.sqlite") as store:
        store.replace_chunks([chunk])
        report = asyncio.run(ClaimsRunner(store, [run_of("a", FakeExtractor({}, failures=2))]).run([chunk]))
        assert store.claims() == []
    assert list(report.failed) == [chunk.id] and "timed out" in report.failed[chunk.id]


def test_a_first_run_that_fails_once_is_retried(tmp_path: plb.Path) -> None:
    """One failure of the first run is retried, and the chunk gets its claims."""
    chunk = make_chunk()
    with Store(tmp_path / "audit.sqlite") as store:
        store.replace_chunks([chunk])
        report = asyncio.run(
            ClaimsRunner(store, [run_of("a", FakeExtractor({chunk.id: [claim(1, "x")]}, failures=1))]).run([chunk])
        )
        assert [c.claim for c in store.claims()] == ["x"]
    assert report.failed == {}


def test_a_later_run_that_fails_is_skipped(tmp_path: plb.Path) -> None:
    """A failing later run is reported, and the chunk keeps the first run's claims."""
    chunk = make_chunk()
    with Store(tmp_path / "audit.sqlite") as store:
        store.replace_chunks([chunk])
        runs = [run_of("a", FakeExtractor({chunk.id: [claim(1, "x")]})), run_of("b", FakeExtractor({}, failures=1))]
        report = asyncio.run(ClaimsRunner(store, runs).run([chunk]))
        assert [c.claim for c in store.claims()] == ["x"]
    assert list(report.skipped_runs) == [f"{chunk.id}|b"]


def test_a_claim_without_text_takes_its_sentence(tmp_path: plb.Path) -> None:
    """A verdict with a kind but no claim text stores the sentence, minus a list bullet."""
    chunk = make_chunk(sentences=["- Workers retry twice."])
    with Store(tmp_path / "audit.sqlite") as store:
        store.replace_chunks([chunk])
        asyncio.run(ClaimsRunner(store, [run_of("a", FakeExtractor({chunk.id: [claim(1, "")]}))]).run([chunk]))
        (stored,) = store.claims()
    assert stored.claim == "Workers retry twice." and stored.sentence == "- Workers retry twice."


def test_a_renamed_concept_does_not_reuse_results(tmp_path: plb.Path) -> None:
    """Same text under a new concept id is extracted again, so refers_to never names the old chunk."""
    old = make_chunk("old#one")
    new = old.model_copy(update={"id": "new#one", "concept": "new"})
    fake = FakeExtractor({old.id: [claim(1, "x")], new.id: [claim(1, "x")]})
    with Store(tmp_path / "audit.sqlite") as store:
        store.replace_chunks([old])
        asyncio.run(ClaimsRunner(store, [run_of("a", fake)]).run([old]))
        store.replace_chunks([new])
        report = asyncio.run(ClaimsRunner(store, [run_of("a", fake)]).run([new]))
    assert report.fresh == 1 and report.cached == 0


def test_an_unreadable_answer_is_reported_and_not_stored(tmp_path: plb.Path) -> None:
    """An answer the model gave in a broken form is reported, and the next pass asks again."""
    chunk = make_chunk()
    fake = FakeExtractor({}, error="could not parse")
    with Store(tmp_path / "audit.sqlite") as store:
        store.replace_chunks([chunk])
        first = asyncio.run(ClaimsRunner(store, [run_of("a", fake)]).run([chunk]))
        second = asyncio.run(ClaimsRunner(store, [run_of("a", fake)]).run([chunk]))
    assert list(first.unreadable) == [f"{chunk.id}|a"]
    assert second.fresh == 1 and fake.calls == 2


def test_a_failed_first_run_drops_claims_of_the_old_text(tmp_path: plb.Path) -> None:
    """When the first run fails, the chunk keeps no claims from an earlier pass."""
    chunk = make_chunk()
    with Store(tmp_path / "audit.sqlite") as store:
        store.replace_chunks([chunk])
        asyncio.run(ClaimsRunner(store, [run_of("a", FakeExtractor({chunk.id: [claim(1, "x")]}))]).run([chunk]))
        changed = chunk.model_copy(update={"key": "edited"})
        store.replace_chunks([changed])
        asyncio.run(ClaimsRunner(store, [run_of("a", FakeExtractor({}, failures=2))]).run([changed]))
        assert store.counts().claims == 0


def test_a_sentence_verdict_comes_from_the_run_whose_claims_it_keeps(tmp_path: plb.Path) -> None:
    """The first run's verdicts stand, except where a later run added the sentence's claims."""
    chunk = make_chunk()
    first = FakeExtractor({chunk.id: [claim(1, "x")]}, verdicts=[note(1, "point"), note(2, "none")])
    second = FakeExtractor({chunk.id: [claim(2, "y")]}, verdicts=[note(1, "subjective"), note(2, "point")])
    with Store(tmp_path / "audit.sqlite") as store:
        store.replace_chunks([chunk])
        asyncio.run(ClaimsRunner(store, [run_of("a", first), run_of("b", second)]).run([chunk]))
        stored = store.verdicts(chunk.id)
    assert [(v.n, v.kind, v.run) for v in stored] == [(1, "point", "a"), (2, "point", "b")]


def test_an_answer_with_no_verdicts_is_not_stored(tmp_path: plb.Path) -> None:
    """A model that answers an empty list twice leaves the section unextracted, so the next pass asks again."""
    chunk = make_chunk()
    structured = FakeStructured([Verdicts(sentences=[]), Verdicts(sentences=[])])
    llm = cast(ChatOpenAI, cast(Any, FakeLLM(structured)))
    run = Run(label="a", model="m", salt="", extractor=ClaimExtractor(llm, asyncio.Semaphore(1)))
    with Store(tmp_path / "audit.sqlite") as store:
        store.replace_chunks([chunk])
        report = asyncio.run(ClaimsRunner(store, [run]).run([chunk]))
        assert list(report.unreadable) == [f"{chunk.id}|a"]
        assert report.incomplete_chunks == {chunk.id}  # so no correction is judged over it this pass
        assert pending(store, [chunk], [("m", "")]) == 1
