"""Tests for tying corrections to the sentences and claims they correct."""

import asyncio
import pathlib as plb
from typing import Any, cast

from helpers import FakeLLM, FakeStructured, claim, make_chunk
from langchain_openai import ChatOpenAI

from audit_cli.claims.corrections import (
    CorrectionAnswer,
    CorrectionJudge,
    Overturn,
    Record,
    judge_corrections,
    pending_corrections,
    records,
)
from audit_cli.claims.runner import stored_claims
from audit_cli.db import Store, StoredClaim
from audit_cli.processing.chunker import Chunk

DECISION = make_chunk(
    "d#decision", ["The worker retries a failed job three times and logs each failure.", "Jobs live in jobs.db."]
)
CONTEXT = make_chunk("d#context", ["Retries used to be unlimited."])
CORRECTION = make_chunk("d#correction", ["The worker retries twice, not three times."]).model_copy(
    update={"is_correction": True}
)
CHUNKS = [CONTEXT, DECISION, CORRECTION]


def decision_claims() -> list[StoredClaim]:
    """Return the decision's stored claims: two on sentence 1 (c1 retries, c2 logs) and one on sentence 2 (c3)."""
    return stored_claims(
        DECISION,
        [
            claim(1, "The worker retries a failed job three times"),
            claim(1, "The worker logs each failed job"),
            claim(2, "Jobs live in jobs.db"),
        ],
    )


def store_with_claims(path: plb.Path) -> Store:
    """Return a store holding the chunks and the decision's claims."""
    store = Store(path)
    store.replace_chunks(CHUNKS)
    store.replace_claims(DECISION.id, decision_claims())
    return store


def judge_answering(*overturns: Overturn, fail: bool = False) -> tuple[CorrectionJudge, FakeStructured]:
    """Return a judge whose model gives these overturns, and the stand-in to count its calls."""
    structured = FakeStructured([CorrectionAnswer(overturns=list(overturns))], fail_from_call=1 if fail else None)
    return CorrectionJudge(cast(ChatOpenAI, cast(Any, FakeLLM(structured))), asyncio.Semaphore(2)), structured


def test_only_corrections_with_a_record_are_judged() -> None:
    """A correction is judged against its concept's other sections; a concept without one gives no record."""
    found = records([*CHUNKS, make_chunk("e#one")], decision_claims())
    assert [(r.correction.id, [t.id for t in r.targets]) for r in found] == [
        ("d#correction", ["d#context", "d#decision"])
    ]


def test_the_message_labels_sentences_and_claims() -> None:
    """Each record sentence is labelled [s.n] with its claims c1, c2 under it, or (no claim)."""
    (record,) = records(CHUNKS, decision_claims())
    message = record.message()
    assert "[1.1] Retries used to be unlimited.\n    (no claim)" in message
    assert "[2.1] The worker retries" in message and "    c1 The worker retries a failed job three times" in message
    assert "    c3 Jobs live in jobs.db" in message and "[1] The worker retries twice" in message


def test_links_keep_only_the_overturned_claim_of_a_shared_sentence() -> None:
    """Overturning c1 links the retry claim and leaves the logging claim on the same sentence alone."""
    (record,) = records(CHUNKS, decision_claims())
    links = record.links(
        CorrectionAnswer(overturns=[Overturn(by=1, sentence="[2.1]", claims=["c1"], reason="two, not three")])
    )
    retry = decision_claims()[0]
    assert [(l.target_chunk, l.target_n, l.claim_id) for l in links] == [("d#decision", 1, retry.claim_id)]


def test_a_sentence_without_claims_is_linked_by_itself() -> None:
    """A corrected sentence with no claim still gets a link, with no claim id."""
    (record,) = records(CHUNKS, decision_claims())
    links = record.links(CorrectionAnswer(overturns=[Overturn(by=1, sentence="[1.1]", reason="no longer unlimited")]))
    assert [(l.target_chunk, l.target_n, l.claim_id) for l in links] == [("d#context", 1, None)]


def test_labels_that_name_nothing_are_dropped() -> None:
    """A made-up sentence, a claim from another sentence, or a correction sentence out of range gives no link."""
    (record,) = records(CHUNKS, decision_claims())
    answer = CorrectionAnswer(
        overturns=[
            Overturn(by=1, sentence="[9.1]", reason="x"),
            Overturn(by=5, sentence="[2.1]", reason="x"),
            Overturn(by=1, sentence="[2.2]", claims=["c1"], reason="c1 is on [2.1]"),
        ]
    )
    assert [(l.target_n, l.claim_id) for l in record.links(answer)] == [(2, None)]


def test_a_judgement_is_stored_and_reused(tmp_path: plb.Path) -> None:
    """The first pass calls the model and stores the links; a second pass with nothing changed calls nothing."""
    judge, structured = judge_answering(Overturn(by=1, sentence="[2.1]", claims=["c1"], reason="two, not three"))
    with store_with_claims(tmp_path / "audit.sqlite") as store:
        first = asyncio.run(judge_corrections(store, CHUNKS, judge))
        second = asyncio.run(judge_corrections(store, CHUNKS, judge))
        (link,) = store.correction_links()
        assert pending_corrections(store, CHUNKS, judge.model, set()) == []
    assert (first.judged, first.links, second.judged, second.stored) == (1, 1, 0, 1)
    assert len(structured.messages) == 1 and link.correction_chunk == "d#correction"


def test_changed_claims_make_the_judgement_out_of_date(tmp_path: plb.Path) -> None:
    """When the record's claims change, the correction is pending again."""
    judge, _ = judge_answering()
    with store_with_claims(tmp_path / "audit.sqlite") as store:
        asyncio.run(judge_corrections(store, CHUNKS, judge))
        store.replace_claims(DECISION.id, decision_claims()[:1])
        assert pending_corrections(store, CHUNKS, judge.model, set()) == ["d#correction"]


def test_a_failed_call_is_reported_and_not_stored(tmp_path: plb.Path) -> None:
    """A call that fails leaves no judgement, so the next pass tries again."""
    judge, _ = judge_answering(fail=True)
    with store_with_claims(tmp_path / "audit.sqlite") as store:
        report = asyncio.run(judge_corrections(store, CHUNKS, judge))
        assert store.correction_key("d#correction") is None
    assert list(report.failed) == ["d#correction"]


def test_a_record_with_a_failed_section_is_skipped(tmp_path: plb.Path) -> None:
    """A correction is not judged while a section of its record has no extraction."""
    judge, structured = judge_answering()
    with store_with_claims(tmp_path / "audit.sqlite") as store:
        report = asyncio.run(judge_corrections(store, CHUNKS, judge, failed_chunks=["d#decision"]))
    assert report.skipped == ["d#correction"] and structured.messages == []


def test_a_changed_target_drops_its_links(tmp_path: plb.Path) -> None:
    """Rechunking edited record text drops the links into it, until the correction is judged again."""
    judge, _ = judge_answering(Overturn(by=1, sentence="[2.1]", claims=["c1"], reason="two, not three"))
    with store_with_claims(tmp_path / "audit.sqlite") as store:
        asyncio.run(judge_corrections(store, CHUNKS, judge))
        edited: Chunk = DECISION.model_copy(update={"key": "edited"})
        store.replace_chunks([CONTEXT, edited, CORRECTION])
        assert store.correction_links() == []


def test_claims_are_numbered_in_the_order_shown() -> None:
    """The record numbers its claims c1, c2, ... section by section, sentence by sentence."""
    (record,) = records(CHUNKS, decision_claims())
    assert isinstance(record, Record) and list(record.labels) == ["c1", "c2", "c3"]
