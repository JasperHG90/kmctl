"""Tests for the extractor graph, with a stand-in for the paid model."""

import asyncio
from typing import Any, cast

from helpers import FakeLLM, FakeStructured, make_chunk
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from audit_cli.claims.extractor import ClaimExtractor
from audit_cli.claims.models import ClaimText, SentenceVerdict, Verdicts


def verdict(n: int, kind: str = "point", text: str = "a claim", refers: list[str] | None = None) -> SentenceVerdict:
    """Return a verdict on sentence ``n`` with one claim, or none, and a reason naming its kind."""
    claims = [] if kind == "none" else [ClaimText(claim=text, quantifier="exists", refers_to=refers or [])]
    return SentenceVerdict(n=n, how_to_check="open it", reason=f"why {kind}", kind=kind, claims=claims)


def extractor(structured: FakeStructured, limit: int = 4) -> ClaimExtractor:
    """Build an extractor around the stand-in model."""
    return ClaimExtractor(cast(ChatOpenAI, cast(Any, FakeLLM(structured))), asyncio.Semaphore(limit))


def test_skipped_sentences_are_asked_again() -> None:
    """When the model skips sentence 2, a second call asks for it alone, and its verdict is kept."""
    structured = FakeStructured([Verdicts(sentences=[verdict(1)]), Verdicts(sentences=[verdict(2, text="second")])])
    result = asyncio.run(extractor(structured).extract(make_chunk()))
    assert [c.claim for c in result.claims] == ["a claim", "second"]
    assert "only these: [2]" in structured.messages[1]


def test_none_verdicts_and_out_of_range_sentences_give_no_claims() -> None:
    """A none verdict, or one for a sentence the chunk does not have, adds nothing."""
    structured = FakeStructured([Verdicts(sentences=[verdict(1, "none"), verdict(2), verdict(9)])])
    result = asyncio.run(extractor(structured).extract(make_chunk()))
    assert [c.evidence for c in result.claims] == [[2]]


def test_refers_to_labels_become_chunk_ids() -> None:
    """[n] points into this chunk and [s.n] into an earlier section; the claim's own sentence is dropped."""
    chunk = make_chunk().model_copy(update={"earlier_ids": ["c#zero"]})
    structured = FakeStructured(
        [Verdicts(sentences=[verdict(1, refers=["[2]", "[1.3]", "[1]", "junk"]), verdict(2, "none")])]
    )
    result = asyncio.run(extractor(structured).extract(chunk))
    assert result.claims[0].refers_to == [f"{chunk.id}|2", "c#zero|3"]


def test_model_calls_stay_under_the_shared_limit() -> None:
    """Many chunks at once never put more calls in flight than the limit allows."""
    structured = FakeStructured([Verdicts(sentences=[verdict(1), verdict(2)])], delay=0.01)
    shared = extractor(structured, limit=3)

    async def all_chunks() -> None:
        """Extract twenty chunks at once."""
        await asyncio.gather(*(shared.extract(make_chunk(f"c#{i}")) for i in range(20)))

    asyncio.run(all_chunks())
    assert structured.most_in_flight == 3


def test_a_failed_fill_call_marks_the_answer_failed() -> None:
    """When asking again for a skipped sentence fails, the answer is an error, not a section with a gap."""
    structured = FakeStructured([Verdicts(sentences=[verdict(1)])], fail_from_call=2)
    result = asyncio.run(extractor(structured).extract(make_chunk()))
    assert result.error == "no verdict for sentences [2] of 2, after asking twice"


def test_an_empty_answer_twice_is_an_error() -> None:
    """A model that gives no verdict at all, twice, fails the section instead of storing it with no claims."""
    structured = FakeStructured([Verdicts(sentences=[]), Verdicts(sentences=[])])
    result = asyncio.run(extractor(structured).extract(make_chunk()))
    assert result.error == "no verdict for sentences [1, 2] of 2, after asking twice"
    assert len(structured.messages) == 2


def test_none_for_every_sentence_is_an_answer() -> None:
    """A section whose every sentence is none has no claims and no error: nothing in it is checkable."""
    structured = FakeStructured([Verdicts(sentences=[verdict(1, "none"), verdict(2, "none")])])
    result = asyncio.run(extractor(structured).extract(make_chunk()))
    assert (result.claims, result.error, len(result.verdicts)) == ([], None, 2)


def test_every_sentence_keeps_its_kind_and_reason() -> None:
    """A claim carries its verdict's reason, and a none verdict is kept as a sentence verdict with its reason."""
    structured = FakeStructured([Verdicts(sentences=[verdict(1, "none"), verdict(2)])])
    result = asyncio.run(extractor(structured).extract(make_chunk()))
    assert [c.reason for c in result.claims] == ["why point"]
    assert [(v.n, v.kind, v.reason) for v in result.verdicts] == [(1, "none", "why none"), (2, "point", "why point")]


def test_the_prompt_gives_examples_and_near_misses_for_every_kind() -> None:
    """Each kind in the prompt has an Is: line and a Not: line."""
    from audit_cli.claims.extractor import SYSTEM_PROMPT

    for kind in ["point", "structural", "broad", "subjective", "external", "none"]:
        section = SYSTEM_PROMPT.split(f"- {kind}:", 1)[1].split("\n- ", 1)[0]
        assert "Is:" in section and "Not:" in section, kind


def unreadable(*sentences: dict[str, Any]) -> AIMessage:
    """Return a raw reply whose sentences did not validate as a whole, as the model sent them."""
    return AIMessage("", tool_calls=[{"name": "Verdicts", "args": {"sentences": list(sentences)}, "id": "t1"}])


def test_one_wrong_field_costs_its_sentence_a_second_ask_not_the_section() -> None:
    """A claim with a kind where its quantifier belongs drops that sentence, which is asked again; the rest is kept."""
    good = verdict(1).model_dump()
    wrong = verdict(2).model_dump()
    wrong["claims"][0]["quantifier"] = "broad"
    structured = FakeStructured([unreadable(good, wrong), Verdicts(sentences=[verdict(2, text="second")])])
    result = asyncio.run(extractor(structured).extract(make_chunk()))
    assert result.error is None and [c.claim for c in result.claims] == ["a claim", "second"]
    assert "only these: [2]" in structured.messages[1]


def test_a_sentence_still_wrong_when_asked_again_fails_the_section() -> None:
    """When the second ask is unreadable for the same sentence too, the section fails rather than store a gap."""
    wrong = verdict(2).model_dump()
    wrong["claims"][0]["quantifier"] = "broad"
    structured = FakeStructured([unreadable(verdict(1).model_dump(), wrong), unreadable(wrong)])
    result = asyncio.run(extractor(structured).extract(make_chunk()))
    assert result.error == "no verdict for sentences [2] of 2, after asking twice"


def test_graph_runs_wait_for_a_slot_before_they_start() -> None:
    """Chunks wait for a slot before their graph starts, so no more graph runs (and traces) are going than the limit."""
    structured = FakeStructured([Verdicts(sentences=[verdict(1)]), Verdicts(sentences=[verdict(2)])], delay=0.01)
    shared = extractor(structured, limit=2)
    graph, going, most = shared.graph, 0, 0

    class Counted:
        """Counts the graph runs going at once."""

        async def ainvoke(self, state: dict[str, Any]) -> Any:
            """Run the real graph, counting it while it runs."""
            nonlocal going, most
            going += 1
            most = max(most, going)
            try:
                return await graph.ainvoke(state)
            finally:
                going -= 1

    shared.graph = Counted()

    async def all_chunks() -> None:
        """Extract ten chunks at once."""
        await asyncio.gather(*(shared.extract(make_chunk(f"c#{i}")) for i in range(10)))

    asyncio.run(all_chunks())
    assert most == 2 and structured.most_in_flight <= 2
