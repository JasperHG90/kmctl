"""Ask a model for a verdict on every sentence of a chunk, then turn the verdicts into claims."""

import asyncio
import re
from typing import Any, TypedDict, cast

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError

from audit_cli.claims.models import (
    ChunkResult,
    Claim,
    ClaimText,
    SentenceNote,
    SentenceVerdict,
    TokenCounts,
    Verdicts,
)
from audit_cli.config import AgentConfig, ProviderConfig
from audit_cli.jsontext import read_list
from audit_cli.logs import get_logger
from audit_cli.processing.chunker import Chunk

SYSTEM_PROMPT = """
You read one section of a design document from a software repository and
decide, sentence by sentence, which claims it makes about that repository.

Why: an auditor checks each claim against the code and reports the ones that
no longer hold. A claim it cannot check wastes its time; a claim you miss is
drift nobody sees.

Go through every numbered sentence in order and give each one a verdict,
including sentences that hold no claim. Do not stop early.

Kinds, by how a claim is checked. Each kind has examples of what it is, and
near misses that are another kind:

- point: look at one named thing in this repository (function, command,
  flag, config key, file, workflow, test).
  Is: "`audit init` writes audit.toml." "Retries stop after `MAX_RETRIES`."
  "The release workflow runs on every tag push" (the trigger is in that
  workflow file).
  Not: "Every command accepts --json" (structural: all commands). "The CLI is
  easy to use" (subjective). "GitHub keeps workflow logs for 90 days"
  (external).

- structural: check many files for a pattern ("every X does Y", "nothing
  imports Z", "only the CLI writes").
  Is: "Every workflow pins its actions to a commit." "Nothing outside cli.py
  imports typer." "Only the store writes to the database."
  Not: "The release workflow pins its actions" (point: one file). "The code
  is well organised" (subjective). "The system has three layers" (broad: no
  pattern to search for).

- broad: about this repository, but too sweeping for any one file to settle
  ("the tool covers every task a user needs", "the system has three
  layers"). A later step decides whether code can settle it.
  Is: "The CLI covers everything a user needs to keep docs current." "The
  design keeps configuration in one place."
  Not: "Configuration is read only from audit.toml" (structural: search for
  other reads). "The design is elegant" (subjective).

- subjective: a principle or value a person must judge; no file settles it.
  Is: "Plain language beats jargon." "Small changes are easier to review."
  Not: "Every docstring follows the numpy format" (structural: a value turned
  into a rule you can check). "Users find the CLI confusing" (external: about
  people, not the repository).

- external: about a tool, service or people outside this repository.
  Is: "uv resolves dependencies faster than pip." "GitHub runs scheduled
  workflows in UTC."
  Not: "CI pins uv to 0.5" (point: the version is in a file here). "The
  action runs on ubuntu-latest" (point: the workflow says so).

- none: no claim. Status, dates, authors; history ("came out of", "used
  to", "was"); measurements from a past run; the reasons for a choice; the
  alternatives a decision rejected; what an operator asked for; headings.
  Is: "Status: accepted." "We first tried Redis, which was too slow." "In
  the March run, recall was 93%." "Considered: a message queue." "The
  operator asked for a dry run."
  Not: "Since 0.4 the CLI reads audit.toml" (point: it still does; the date
  is history, the reading is a claim). "We chose SQLite because it needs no
  server" (point: the project uses SQLite; only the reason is none).

Give every point or structural claim a quantifier, by how many places in
this repository settle it:
- exists: one place proves it; find the function, file, flag, key or step
  that does it.
- all: every instance of something must comply ("every concept has a type",
  "each workflow pins its actions"); you must find every instance.
- none: no instance may exist anywhere ("never writes outside .okf/",
  "nothing imports the CLI", "only the CLI writes X"); you must search
  everywhere.
Judge the meaning, not the words: "the hook stays silent when the bundle is
clean" is exists, because one hook settles it.

Fill how_to_check, then reason, before you choose the kind. If you cannot
name what to open or run in this repository, the kind is subjective,
external, broad or none. In reason, say in one short sentence why the
sentence is that kind: what in this repository settles it, or why nothing
does ("names the `audit init` command", "a value judgement; no file settles
it", "history: says what was tried before").

A sentence can hold several claims; list each one. Write each so it stands
alone: replace "it", "this", "the code", "both commits" and "the tool" with
the names they refer to, from this section or the earlier sections shown.
Keep what the sentence says, no more and no less:
- Keep its conditions: "If the child exits 0, it prints the line" is a claim
  that says "When the child exits 0, it prints the line", never "the child
  exits 0".
- Keep its tense: a sentence about the past is history (none); never restate
  it in the present.
- Keep its negation and its list's heading: an item under "Not built", "Out
  of scope" or "What it does not do" is a claim that it is not done, never
  that it is; an option under "Considered" or "Rejected" is none.
In refers_to, list the labels of the sentences a claim
needs to be understood: [s.n] for an earlier section, [n] for this one; leave
it empty when the claim stands alone.

Earlier sections of the document are shown for context only: give no
verdicts for them.

If the record has later corrections, they are shown for context only: give
no verdicts for them, and mark a sentence they overturn as none.
""".strip()

# A model sometimes skips a run of sentences despite the prompt; the sentences it skipped are asked again.
log = get_logger("claims.extractor")
FILL_NOTE = "You gave no verdict for some sentences. Give a verdict for each of these sentences, and only these: {}"


def build_llm(agent: AgentConfig, provider: ProviderConfig) -> ChatOpenAI:
    """Build the chat model for one agent on its OpenAI-compatible provider.

    Raises
    ------
    ConfigError
        If the provider's key variable is not set.
    """
    extra: dict[str, Any] = {"reasoning_effort": agent.reasoning_effort} if agent.reasoning_effort else {}
    return ChatOpenAI(
        base_url=provider.base_url,
        api_key=provider.api_key(),
        model=agent.model,
        temperature=agent.temperature,
        timeout=agent.timeout,
        max_retries=agent.max_retries,
        **extra,
    )


class ExtractionState(TypedDict, total=False):
    """The extraction graph's state: the chunk in, the model's output, the result out."""

    chunk: Chunk
    output: dict[str, Any]
    result: ChunkResult


class ClaimExtractor:
    """A two-node graph: ask the model for a verdict per sentence, then turn verdicts into claims.

    Parameters
    ----------
    llm :
        The chat model to send each chunk to.
    limit :
        Bounds the chunks in extraction at once, shared with every other extractor. A chunk holds its slot through
        its graph run, so its second ask for skipped sentences never waits behind other chunks, and a trace shows only
        the graph runs that are going.
    """

    def __init__(self, llm: ChatOpenAI, limit: asyncio.Semaphore) -> None:
        self._model = str(getattr(llm, "model_name", "") or getattr(llm, "model", ""))
        self._structured: Runnable[Any, dict[str, Any]] = llm.with_structured_output(
            Verdicts, method="function_calling", include_raw=True
        )
        self._limit = limit
        self.graph = self._build()

    def _build(self) -> Any:
        """Compile the verdicts -> claims graph."""
        builder = StateGraph(ExtractionState)
        builder.add_node("verdicts", self._verdicts)
        builder.add_node("claims", self._claims)
        builder.add_edge(START, "verdicts")
        builder.add_edge("verdicts", "claims")
        builder.add_edge("claims", END)
        return builder.compile()

    @staticmethod
    def user_message(chunk: Chunk) -> str:
        """Build the user message with the concept's context, numbered sentences and any corrections."""
        parts = [
            f"Concept: {chunk.concept} (type: {chunk.type}, status: {chunk.status or 'n/a'})",
            f"Title: {chunk.title}",
            f"Section: {chunk.section}",
        ]
        if chunk.earlier:
            parts += ["", "Earlier sections of this document (context only):", chunk.earlier]
        parts += ["", "This section:", chunk.numbered_sentences()]
        if chunk.corrections:
            parts += ["", "Later corrections in this record (context only):", chunk.corrections]
        return "\n".join(parts)

    async def _ask(self, message: str) -> dict[str, Any]:
        """Send one message; the caller holds a slot under the shared limit."""
        answer: dict[str, Any] = await self._structured.ainvoke([SystemMessage(SYSTEM_PROMPT), HumanMessage(message)])
        return answer

    async def _verdicts(self, state: ExtractionState) -> dict[str, Any]:
        """Node: ask for a verdict on every numbered sentence, then once more for any the model skipped.

        An answer that does not read as a whole keeps each sentence verdict that does; the rest are asked again with
        the skipped ones, so one wrong field costs a sentence's second ask, not the section. A sentence still without
        a verdict after the second ask sets ``parsing_error``, so the answer is reported and not stored. A verdict of
        kind none is an answer: a section with no claims is fine.
        """
        chunk = state["chunk"]
        message = self.user_message(chunk)
        log.debug("model_call", chunk=chunk.id, model=self._model, sentences=len(chunk.sentences), chars=len(message))
        output = await self._ask(message)
        output["tokens"] = self._tokens(output.get("raw"))
        parsed: Verdicts | None = output["parsed"]
        if parsed is None:
            parsed, dropped = self._salvage(output.get("raw"))
            if parsed is None:
                log.debug(
                    "model_answer_unreadable", chunk=chunk.id, model=self._model, error=str(output.get("parsing_error"))
                )
                return {"output": output}
            log.info(
                "verdicts_unreadable_asking_again",
                chunk=chunk.id,
                model=self._model,
                dropped=dropped,
                error=str(output.get("parsing_error"))[:300],
            )
            output["parsed"], output["parsing_error"] = parsed, None
        missing = sorted(set(range(1, len(chunk.sentences) + 1)) - {v.n for v in parsed.sentences})
        log.debug(
            "model_answer",
            chunk=chunk.id,
            model=self._model,
            verdicts=len(parsed.sentences),
            tokens_in=output["tokens"].input,
            tokens_out=output["tokens"].output,
        )
        if not missing:
            return {"output": output}
        log.info("sentences_skipped_asking_again", chunk=chunk.id, model=self._model, sentences=missing)
        try:
            more = await self._ask(message + "\n\n" + FILL_NOTE.format(", ".join(f"[{n}]" for n in missing)))
        except Exception as error:  # noqa: BLE001  # reported below as sentences with no verdict
            log.warning("fill_call_failed", chunk=chunk.id, model=self._model, error=f"{type(error).__name__}: {error}")
            more = {"parsed": None}
        extra = self._tokens(more.get("raw"))
        output["tokens"] = TokenCounts(
            input=output["tokens"].input + extra.input, output=output["tokens"].output + extra.output
        )
        again: Verdicts | None = more["parsed"] or self._salvage(more.get("raw"))[0]
        if again is not None:
            filled = [v for v in again.sentences if v.n in missing]
            output["parsed"] = Verdicts(sentences=parsed.sentences + filled)
        still = sorted(set(missing) - {v.n for v in output["parsed"].sentences})
        if still:  # a sentence with no verdict is a claim nobody sees, so the answer counts as failed
            output["parsing_error"] = f"no verdict for sentences {still} of {len(chunk.sentences)}, after asking twice"
        return {"output": output}

    def _claims(self, state: ExtractionState) -> dict[str, Any]:
        """Node: one claim per claim in each verdict that is not none and names a sentence in the chunk."""
        chunk, output = state["chunk"], state["output"]
        parsed: Verdicts | None = output["parsed"]
        claims: list[Claim] = []
        notes: dict[int, SentenceNote] = {}
        for verdict in parsed.sentences if parsed is not None else []:
            if not 1 <= verdict.n <= len(chunk.sentences):
                continue
            notes.setdefault(verdict.n, SentenceNote(n=verdict.n, kind=verdict.kind, reason=verdict.reason))
            if verdict.kind != "none":
                claims.extend(self._verdict_claims(verdict, chunk))
        error = str(output["parsing_error"]) if output.get("parsing_error") else None
        result = ChunkResult(
            id=chunk.id,
            key=chunk.extraction_key,
            claims=claims,
            verdicts=[notes[n] for n in sorted(notes)],
            error=error,
            tokens=output["tokens"],
        )
        return {"result": result}

    async def extract(self, chunk: Chunk) -> ChunkResult:
        """Wait for a free slot under the shared limit, then run one chunk through the graph and return its claims."""
        async with self._limit:
            state = await self.graph.ainvoke({"chunk": chunk})
        return cast(ChunkResult, state["result"])

    @staticmethod
    def _refers_to(labels: list[str], chunk: Chunk, own: int) -> list[str]:
        """Turn [s.n] and [n] labels into 'chunk id|n', dropping the claim's own sentence and labels that name nothing."""
        found = []
        for label in labels:
            match = re.fullmatch(r"\[?\s*(?:(\d+)\.)?(\d+)\s*\]?", label.strip())
            if not match:
                continue
            section, n = match.group(1), int(match.group(2))
            if section is None:
                if 1 <= n <= len(chunk.sentences) and n != own:
                    found.append(f"{chunk.id}|{n}")
            elif 1 <= int(section) <= len(chunk.earlier_ids):
                found.append(f"{chunk.earlier_ids[int(section) - 1]}|{n}")
        return found

    @staticmethod
    def _verdict_claims(verdict: SentenceVerdict, chunk: Chunk) -> list[Claim]:
        """Turn one verdict into one claim per listed claim, or one empty claim."""
        return [
            Claim(
                evidence=[verdict.n],
                claim_type=verdict.kind,
                claim=text.claim,
                how_to_check=verdict.how_to_check,
                quantifier=text.quantifier,
                refers_to=ClaimExtractor._refers_to(text.refers_to, chunk, verdict.n),
                reason=verdict.reason,
            )
            for text in verdict.claims or [ClaimText(claim="", quantifier="exists")]
        ]

    @staticmethod
    def _salvage(raw: BaseMessage | None) -> tuple[Verdicts | None, int]:
        """From an answer that did not read as a whole, keep each sentence verdict that reads.

        Returns
        -------
        tuple[Verdicts | None, int]
            The verdicts kept, or None when the reply holds no sentences list at all, and how many were dropped.
        """
        for call in getattr(raw, "tool_calls", None) or []:
            items = read_list((call.get("args") or {}).get("sentences"))
            if not isinstance(items, list):
                continue
            kept: list[SentenceVerdict] = []
            for item in items:
                try:
                    kept.append(SentenceVerdict.model_validate(item))
                except ValidationError:
                    continue
            return Verdicts(sentences=kept), len(items) - len(kept)
        return None, 0

    @staticmethod
    def _tokens(message: BaseMessage | None) -> TokenCounts:
        """Read the tokens a model call used from its message; 0 when unknown."""
        usage = getattr(message, "usage_metadata", None) or {}
        return TokenCounts(input=usage.get("input_tokens", 0), output=usage.get("output_tokens", 0))
