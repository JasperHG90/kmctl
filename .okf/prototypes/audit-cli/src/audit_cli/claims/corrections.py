"""Tie each correction to the sentences it corrects and the claims it overturns.

After extraction, every correction section is shown to a model with the rest of its record: each sentence, labelled
``[s.n]``, with the claims taken from it, labelled ``c1``, ``c2``. The model says which sentences each correction
sentence corrects and which of their claims it overturns. The answer is stored as links, so a claim a correction
overturns is marked superseded and every link can be checked.
"""

import asyncio
import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from audit_cli.claims.models import CorrectionLink
from audit_cli.db import Store, StoredClaim
from audit_cli.logs import get_logger
from audit_cli.processing.chunker import Chunk

log = get_logger("claims.corrections")

CORRECTION_PROMPT = """
You read a correction to a design record, and the record's other sentences, each with the claims an earlier step
took from it. Say which sentences the correction corrects, and which of their claims it overturns.

Why: a claim the correction overturns no longer describes the repository, so an auditor must not check it. A claim
the correction leaves alone must stay.

For each correction sentence, list every record sentence it changes, by its label ([s.n]), with the labels (c1,
c2, ...) of that sentence's claims it overturns. A claim it does not touch stays off the list, even when it shares
the sentence: "The worker retries three times and logs each failure", corrected to "it retries twice", overturns the
retry claim, not the logging claim. A sentence with no claims can still be corrected: list it with no claims. Give
a one-sentence reason for each. A correction sentence that corrects nothing (a date, why the correction was made)
gets no entry, and a record sentence the correction does not change is not listed.
""".strip()
PROMPT_HASH = hashlib.sha256(CORRECTION_PROMPT.encode()).hexdigest()[:8]
_LABEL = re.compile(r"\[?\s*(\d+)\.(\d+)\s*\]?")


class Overturn(BaseModel):
    """One record sentence a correction sentence changes, and the claims of it that it overturns."""

    by: int = Field(description="The number of the correction sentence that makes the change.")
    sentence: str = Field(description="The label of the record sentence it changes, like [2.4].")
    claims: list[str] = Field(default=[], description="Labels of that sentence's claims it overturns, like c3.")
    reason: str = Field(description="One sentence: what the correction changes.")


class CorrectionAnswer(BaseModel):
    """Every record sentence the correction changes."""

    overturns: list[Overturn]


@dataclass
class Record:
    """A correction section and the rest of its concept, as shown to the model.

    Attributes
    ----------
    correction : Chunk
        The correction section.
    targets : list[Chunk]
        The concept's other sections, in order; section s of a label ``[s.n]`` is ``targets[s - 1]``.
    claims : dict[str, list[StoredClaim]]
        Each target section's stored claims.
    labels : dict[str, StoredClaim]
        The claims by the label (``c1``, ``c2``) they are shown with.
    """

    correction: Chunk
    targets: list[Chunk]
    claims: dict[str, list[StoredClaim]]
    labels: dict[str, StoredClaim] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Number the claims c1, c2, ... in the order they are shown."""
        claims = [c for t in self.targets for n in range(1, len(t.sentences) + 1) for c in self._on(t.id, n)]
        self.labels = {f"c{i}": claim for i, claim in enumerate(claims, 1)}

    def _on(self, chunk_id: str, n: int) -> list[StoredClaim]:
        """Return the claims stored for one sentence."""
        return [c for c in self.claims.get(chunk_id, []) if c.sentence_n == n]

    def key(self, model: str) -> str:
        """Return a hash of everything the judgement depends on: the correction, the record, its claims and model."""
        content = [
            PROMPT_HASH,
            model,
            self.correction.extraction_key,
            [
                (t.id, t.extraction_key, [(c.claim_id, c.sentence_n) for c in self.claims.get(t.id, [])])
                for t in self.targets
            ],
        ]
        return hashlib.sha256(json.dumps(content).encode()).hexdigest()[:16]

    def message(self) -> str:
        """Build the user message: the correction's sentences, then each record sentence with its claims."""
        by_claim = {id(claim): label for label, claim in self.labels.items()}
        lines = [
            f"Concept: {self.correction.concept} (title: {self.correction.title})",
            "",
            f"The correction ({self.correction.section}):",
            self.correction.numbered_sentences(),
            "",
            "The record's other sentences, each with its claims:",
        ]
        for s, target in enumerate(self.targets, 1):
            lines.append(f"{target.section}:")
            for n, sentence in enumerate(target.sentences, 1):
                lines.append(f"[{s}.{n}] {sentence}")
                claims = self._on(target.id, n)
                lines.extend(f"    {by_claim[id(c)]} {c.claim}" for c in claims)
                if not claims:
                    lines.append("    (no claim)")
        return "\n".join(lines)

    def links(self, answer: CorrectionAnswer) -> list[CorrectionLink]:
        """Turn the model's labels into links, dropping and logging any label that names nothing."""
        found: list[CorrectionLink] = []
        for item in answer.overturns:
            match = _LABEL.fullmatch(item.sentence.strip())
            if not 1 <= item.by <= len(self.correction.sentences) or match is None:
                log.warning(
                    "correction_label_dropped", correction=self.correction.id, by=item.by, sentence=item.sentence
                )
                continue
            s, n = int(match.group(1)), int(match.group(2))
            if not 1 <= s <= len(self.targets) or not 1 <= n <= len(self.targets[s - 1].sentences):
                log.warning("correction_label_dropped", correction=self.correction.id, sentence=item.sentence)
                continue
            target = self.targets[s - 1]
            claims = []
            for label in item.claims:
                claim = self.labels.get(label.strip())
                if claim is None or claim.chunk_id != target.id or claim.sentence_n != n:
                    log.warning(
                        "correction_claim_dropped", correction=self.correction.id, claim=label, sentence=item.sentence
                    )
                    continue
                claims.append(claim)
            base = {
                "correction_chunk": self.correction.id,
                "correction_n": item.by,
                "target_chunk": target.id,
                "target_n": n,
            }
            found += [CorrectionLink(**base, claim_id=c.claim_id, reason=item.reason) for c in claims] or [
                CorrectionLink(**base, reason=item.reason)
            ]
        return found


def records(chunks: Iterable[Chunk], claims: list[StoredClaim]) -> list[Record]:
    """Return one record per correction section whose concept has other sections to correct."""
    by_chunk: dict[str, list[StoredClaim]] = {}
    for claim in claims:
        by_chunk.setdefault(claim.chunk_id, []).append(claim)
    by_concept: dict[str, list[Chunk]] = {}
    for chunk in chunks:
        by_concept.setdefault(chunk.concept, []).append(chunk)
    found = []
    for sections in by_concept.values():
        targets = [c for c in sections if not c.is_correction]
        for correction in (c for c in sections if c.is_correction):
            if targets:
                found.append(Record(correction, targets, {t.id: by_chunk.get(t.id, []) for t in targets}))
    return found


class CorrectionJudge:
    """Ask a model which sentences and claims each correction overturns.

    Parameters
    ----------
    llm :
        The chat model to ask.
    limit :
        Bounds model calls in flight, shared with the extractors.
    """

    def __init__(self, llm: ChatOpenAI, limit: asyncio.Semaphore) -> None:
        self.model = str(getattr(llm, "model_name", "") or getattr(llm, "model", ""))
        self._structured: Runnable[Any, dict[str, Any]] = llm.with_structured_output(
            CorrectionAnswer, method="function_calling", include_raw=True
        )
        self._limit = limit

    async def judge(self, record: Record) -> tuple[list[CorrectionLink], str | None]:
        """Return the record's links, and why the answer could not be read when it could not."""
        async with self._limit:
            output: dict[str, Any] = await self._structured.ainvoke(
                [SystemMessage(CORRECTION_PROMPT), HumanMessage(record.message())]
            )
        answer: CorrectionAnswer | None = output["parsed"]
        if answer is None:
            return [], str(output.get("parsing_error") or "no answer")
        return record.links(answer), None


@dataclass
class CorrectionsReport:
    """What the corrections pass did.

    Attributes
    ----------
    judged : int
        Correction sections sent to the model.
    stored : int
        Correction sections whose judgement was still current.
    links : int
        Links written by this pass.
    failed : dict[str, str]
        Correction sections whose call failed or whose answer could not be read; judged again next pass.
    skipped : list[str]
        Correction sections not judged because a section of their record failed to extract.
    """

    judged: int = 0
    stored: int = 0
    links: int = 0
    failed: dict[str, str] = field(default_factory=dict)
    skipped: list[str] = field(default_factory=list)


async def judge_corrections(
    store: Store, chunks: list[Chunk], judge: CorrectionJudge, failed_chunks: Iterable[str] = ()
) -> CorrectionsReport:
    """Judge every correction section among ``chunks`` whose judgement is missing or out of date, and store it.

    Parameters
    ----------
    store :
        The project's database, with the chunks' claims already stored.
    chunks :
        The extracted chunks; a correction is judged against the other chunks of its concept.
    judge :
        Asks the model.
    failed_chunks :
        Chunks whose extraction failed or was unreadable; a correction whose record holds one is skipped this pass.
    """
    report = CorrectionsReport()
    failed = set(failed_chunks)

    async def one(record: Record) -> None:
        """Judge one correction, or keep its stored judgement."""
        cid = record.correction.id
        if failed & {cid, *(t.id for t in record.targets)}:
            report.skipped.append(cid)
            log.warning("correction_skipped", correction=cid, reason="a section of its record failed to extract")
            return
        key = record.key(judge.model)
        if store.correction_key(cid) == key:
            report.stored += 1
            return
        try:
            links, error = await judge.judge(record)
        except Exception as caught:  # noqa: BLE001  # one failed call is reported per correction, not fatal
            links, error = [], f"{type(caught).__name__}: {caught}"
        if error is not None:
            report.failed[cid] = error
            log.warning("correction_failed", correction=cid, error=error)
            return
        store.save_correction(cid, key, judge.model, links)
        report.judged += 1
        report.links += len(links)
        overturned = sum(link.claim_id is not None for link in links)
        log.info(
            "correction_judged",
            correction=cid,
            sentences=len({(l.target_chunk, l.target_n) for l in links}),
            claims_overturned=overturned,
        )

    await asyncio.gather(*(one(r) for r in records(chunks, store.claims())))
    return report


def pending_corrections(store: Store, chunks: list[Chunk], model: str, stale: set[str]) -> list[str]:
    """Return the correction sections that would be judged: never judged, out of date, or with a stale record.

    Parameters
    ----------
    store :
        The project's database.
    chunks :
        The chunks the path holds now.
    model :
        The model that judges corrections.
    stale :
        Chunks that are not up to date; their claims will change, so a correction over them will be judged again.
    """
    return [
        r.correction.id
        for r in records(chunks, store.claims())
        if stale & {r.correction.id, *(t.id for t in r.targets)}
        or store.correction_key(r.correction.id) != r.key(model)
    ]
