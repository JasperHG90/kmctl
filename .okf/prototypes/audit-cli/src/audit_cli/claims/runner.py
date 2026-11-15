"""Extract every chunk with each configured run, reusing stored results, and store the merged claims."""

import asyncio
import hashlib
import re
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field

from audit_cli.claims.extractor import FILL_NOTE, SYSTEM_PROMPT, ClaimExtractor
from audit_cli.claims.models import ChunkResult, Claim, claim_id, merge_runs
from audit_cli.db import Store, StoredClaim
from audit_cli.logs import get_logger
from audit_cli.processing.chunker import Chunk

PROMPT_HASH = hashlib.sha256((SYSTEM_PROMPT + FILL_NOTE).encode()).hexdigest()[:8]
_BULLET = re.compile(r"^[-*]\s+")
log = get_logger("claims.runner")


def pending(store: Store, chunks: list[Chunk], runs: list[tuple[str, str]]) -> int:
    """Return how many chunk-and-run results are not stored yet: the ones that would call a model.

    Parameters
    ----------
    store :
        The database to look in.
    chunks :
        The chunks to extract.
    runs :
        Each run's model and salt; no client is needed, so no key either.
    """
    return sum(store.extraction(chunk, model, PROMPT_HASH, salt) is None for chunk in chunks for model, salt in runs)


@dataclass(frozen=True)
class Run:
    """One extraction run: an agent's model, plus a salt that makes a repeat run a separate one.

    Attributes
    ----------
    label : str
        The name in the config's ``claims.runs``, such as ``extractor@2``.
    model : str
        The model the run calls; part of the cache key.
    salt : str
        The part after ``@``, empty for none; part of the cache key.
    extractor : ClaimExtractor
        Sends chunks to the model.
    """

    label: str
    model: str
    salt: str
    extractor: ClaimExtractor


@dataclass
class ClaimsReport:
    """What one extraction pass did.

    Attributes
    ----------
    chunks : int
        Chunks processed.
    fresh : int
        Run results that needed model calls.
    cached : int
        Run results read from the database.
    failed : dict[str, str]
        Chunks whose first run failed twice, with the error; they have no claims this pass.
    skipped_runs : dict[str, str]
        Later runs that failed, as ``chunk id|run``, with the error; the chunk keeps the other runs' claims.
    unreadable : dict[str, str]
        Fresh answers that could not be parsed, as ``chunk id|run``; not stored, so the next pass asks again.
    claims_by_type : Counter[str]
        Merged claims per kind.
    tokens_in : int
        Tokens sent in fresh calls.
    tokens_out : int
        Tokens returned by fresh calls.
    """

    chunks: int = 0
    fresh: int = 0
    cached: int = 0
    failed: dict[str, str] = field(default_factory=dict)
    skipped_runs: dict[str, str] = field(default_factory=dict)
    unreadable: dict[str, str] = field(default_factory=dict)
    claims_by_type: Counter[str] = field(default_factory=Counter)
    tokens_in: int = 0
    tokens_out: int = 0

    @property
    def incomplete_chunks(self) -> set[str]:
        """Chunks whose first run failed or whose answer was unreadable this pass: their claims are not settled."""
        return set(self.failed) | {key.split("|", 1)[0] for key in self.unreadable}


def stored_claims(chunk: Chunk, claims: list[Claim]) -> list[StoredClaim]:
    """Turn a chunk's merged claims into rows; a claim with no text takes its sentence's text."""
    rows = []
    for position, claim in enumerate(c for c in claims if c.evidence):
        n = claim.evidence[0]
        sentence = chunk.sentences[n - 1] if 1 <= n <= len(chunk.sentences) else ""
        text = claim.claim.strip() or _BULLET.sub("", sentence).strip()
        rows.append(
            StoredClaim(
                chunk_id=chunk.id,
                position=position,
                claim_id=claim_id(chunk.concept, text),
                concept=chunk.concept,
                sentence_n=n,
                sentence=sentence,
                claim_type=claim.claim_type,
                claim=text,
                how_to_check=claim.how_to_check,
                quantifier=claim.quantifier,
                refers_to=claim.refers_to,
                run=claim.run,
                reason=claim.reason,
            )
        )
    return rows


class ClaimsRunner:
    """Run each chunk through every run in order and store the merged claims.

    The first run's claims stand; each later run adds claims for sentences the
    runs before it gave none. A run whose result is stored for the chunk's
    current content is read, not called again.

    Parameters
    ----------
    store :
        Where results are read from and written to.
    runs :
        The runs, in order; the first is required, the rest only add claims.
    """

    def __init__(self, store: Store, runs: list[Run]) -> None:
        self._store = store
        self._runs = runs

    async def run(self, chunks: list[Chunk], on_done: Callable[[], object] | None = None) -> ClaimsReport:
        """Extract every chunk; the shared limit inside each extractor bounds the model calls in flight.

        Parameters
        ----------
        chunks :
            The chunks to extract.
        on_done :
            Called once as each chunk finishes, for a progress bar.
        """
        report = ClaimsReport(chunks=len(chunks))

        async def one(chunk: Chunk) -> None:
            """Extract one chunk, then report it done."""
            await self._chunk(chunk, report)
            if on_done is not None:
                on_done()

        await asyncio.gather(*(one(chunk) for chunk in chunks))
        return report

    async def _once(self, run: Run, chunk: Chunk, report: ClaimsReport) -> ChunkResult:
        """Return one run's result for the chunk, from the database or from the model."""
        result = self._store.extraction(chunk, run.model, PROMPT_HASH, run.salt)
        if result is None:
            result = await run.extractor.extract(chunk)
            report.fresh += 1
            report.tokens_in += result.tokens.input
            report.tokens_out += result.tokens.output
            if result.error:  # not stored, so the next pass asks again
                report.unreadable[f"{chunk.id}|{run.label}"] = result.error
                log.warning("answer_unreadable", chunk=chunk.id, run=run.label, model=run.model, error=result.error)
            else:
                self._store.save_extraction(result, run.model, PROMPT_HASH, run.salt)
            log.debug(
                "run_called",
                chunk=chunk.id,
                run=run.label,
                model=run.model,
                claims=len(result.claims),
                tokens_in=result.tokens.input,
                tokens_out=result.tokens.output,
            )
        else:
            report.cached += 1
            log.debug("run_cached", chunk=chunk.id, run=run.label, model=run.model)
        claims = [c.model_copy(update={"run": run.label}) for c in result.claims]
        verdicts = [v.model_copy(update={"run": run.label}) for v in result.verdicts]
        return result.model_copy(update={"claims": claims, "verdicts": verdicts})

    async def _chunk(self, chunk: Chunk, report: ClaimsReport) -> None:
        """Extract one chunk with every run and store its merged claims."""
        started = time.monotonic()
        fresh_before, cached_before, tokens_before = report.fresh, report.cached, report.tokens_in + report.tokens_out
        merged: ChunkResult | None = None
        for index, run in enumerate(self._runs):
            attempts = 2 if index == 0 else 1  # a timed-out first run is tried once more
            for attempt in range(attempts):
                try:
                    result = await self._once(run, chunk, report)
                    break
                except Exception as error:  # noqa: BLE001  # any failure of one call is reported per chunk
                    if attempt + 1 < attempts:
                        log.warning(
                            "run_retry", chunk=chunk.id, run=run.label, error=f"{type(error).__name__}: {error}"
                        )
                        continue
                    if index == 0:
                        report.failed[chunk.id] = f"{type(error).__name__}: {error}"
                        self._store.replace_claims(chunk.id, [])  # no claims from text that may have changed
                        self._store.replace_verdicts(chunk.id, [])
                        log.error("chunk_failed", chunk=chunk.id, run=run.label, error=report.failed[chunk.id])
                        return
                    report.skipped_runs[f"{chunk.id}|{run.label}"] = f"{type(error).__name__}: {error}"
                    log.warning("run_skipped", chunk=chunk.id, run=run.label, error=f"{type(error).__name__}: {error}")
                    result = None
            if result is not None:
                merged = result if merged is None else merge_runs(merged, result)
        rows = stored_claims(chunk, merged.claims if merged else [])
        self._store.replace_claims(chunk.id, rows)
        self._store.replace_verdicts(chunk.id, merged.verdicts if merged else [])
        report.claims_by_type.update(row.claim_type for row in rows)
        log.info(
            "section_extracted",
            chunk=chunk.id,
            claims=len(rows),
            by_run=dict(Counter(row.run for row in rows)),
            runs_called=report.fresh - fresh_before,
            runs_stored=report.cached - cached_before,
            tokens=report.tokens_in + report.tokens_out - tokens_before,
            seconds=round(time.monotonic() - started, 2),
        )
