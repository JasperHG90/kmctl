"""Builders for tests: chunks and a stand-in for the paid model."""

import asyncio
import hashlib
import json
from typing import Any

from langchain_core.messages import AIMessage

from audit_cli.claims.models import ChunkResult, Claim, SentenceNote, TokenCounts
from audit_cli.processing.chunker import Chunk


def make_chunk(chunk_id: str = "c#one", sentences: list[str] | None = None) -> Chunk:
    """Return a chunk with the given sentences; its key follows the text, as the chunker's does."""
    sentences = sentences or ["The CLI writes `jobs.db`.", "Workers retry twice."]
    return Chunk(
        id=chunk_id,
        concept=chunk_id.split("#")[0],
        type="decision",
        status=None,
        title="T",
        section="T > One",
        sentences=sentences,
        corrections="",
        key=hashlib.sha256(json.dumps([chunk_id, sentences]).encode()).hexdigest()[:16],
    )


class FakeExtractor:
    """Returns set claims per chunk, counts calls, and can fail a set number of times."""

    def __init__(
        self,
        claims: dict[str, list[Claim]],
        failures: int = 0,
        error: str | None = None,
        verdicts: list[SentenceNote] | None = None,
    ) -> None:
        self.claims = claims
        self.verdicts = verdicts or []
        self.failures = failures
        self.error = error
        self.calls = 0

    async def extract(self, chunk: Chunk) -> ChunkResult:
        """Return this chunk's set claims, or raise while failures remain.

        Every sentence gets a verdict, as from a real answer: the set ones, else the kind of a claim on it, else none.
        """
        self.calls += 1
        if self.failures:
            self.failures -= 1
            raise TimeoutError("the model timed out")
        claims = self.claims.get(chunk.id, [])
        kinds = {n: c.claim_type for c in claims for n in c.evidence}
        given = {v.n: v for v in self.verdicts}
        verdicts = [given.get(n) or note(n, kinds.get(n, "none")) for n in range(1, len(chunk.sentences) + 1)]
        return ChunkResult(
            id=chunk.id,
            key=chunk.extraction_key,
            claims=claims,
            verdicts=verdicts,
            error=self.error,
            tokens=TokenCounts(input=10, output=2),
        )


def claim(n: int, text: str, kind: str = "point") -> Claim:
    """Return a claim on sentence ``n``."""
    return Claim(evidence=[n], claim_type=kind, claim=text, how_to_check="open it")


class FakeStructured:
    """Stands in for a model with structured output: answers from a list and tracks calls in flight."""

    def __init__(self, answers: list[Any], delay: float = 0.0, fail_from_call: int | None = None) -> None:
        self.answers = list(answers)
        self.fail_from_call = fail_from_call
        self.delay = delay
        self.in_flight = 0
        self.most_in_flight = 0
        self.messages: list[str] = []

    async def ainvoke(self, messages: list[Any]) -> dict[str, Any]:
        """Return the next answer, as with_structured_output(include_raw=True) would."""
        self.in_flight += 1
        self.most_in_flight = max(self.most_in_flight, self.in_flight)
        self.messages.append(messages[-1].content)
        if self.fail_from_call is not None and len(self.messages) >= self.fail_from_call:
            self.in_flight -= 1
            raise TimeoutError("the model timed out")
        await asyncio.sleep(self.delay)
        self.in_flight -= 1
        answer = self.answers.pop(0) if len(self.answers) > 1 else self.answers[0]
        if isinstance(answer, AIMessage):  # a reply that did not validate: no parsed answer, the raw tool call kept
            return {"parsed": None, "raw": answer, "parsing_error": "1 validation error for Verdicts"}
        return {"parsed": answer, "raw": None, "parsing_error": None}


class FakeLLM:
    """Stands in for ChatOpenAI: hands out one FakeStructured."""

    def __init__(self, structured: FakeStructured) -> None:
        self.structured = structured

    def with_structured_output(self, *args: Any, **kwargs: Any) -> FakeStructured:
        """Return the stand-in structured model."""
        return self.structured


def note(n: int, kind: str) -> SentenceNote:
    """Return a sentence verdict with a reason naming its kind."""
    return SentenceNote(n=n, kind=kind, reason=f"why {kind}")
