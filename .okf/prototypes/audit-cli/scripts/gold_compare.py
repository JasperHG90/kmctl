"""Score the CLI's prompt against the notebook's on the gold sentences of kmctl's bundle.

Every prompt is run with the config's extractor model, twice, and saved under results/gold/<model>/, so a rerun is
free. Run from the audit-cli folder:

    uv run python scripts/gold_compare.py --config path/to/audit.toml

Five prompts: the notebook's (old); the notebook's plus the reason field (reason only); the CLI's (new: the reason
plus examples and near misses per kind); new with the reason after the claims (reason last); and new without the
reason (examples only). Writes results/gold_compare.json and prints one row per run: recall, precision, type ok and checkable precision
(the notebook's sentence-level measures), plus claims and output tokens.
"""

import argparse
import asyncio
import hashlib
import json
import pathlib as plb
from collections import Counter

from dotenv import find_dotenv, load_dotenv
from pydantic import BaseModel, Field

from audit_cli.claims import extractor as extractor_module
from audit_cli.claims.extractor import SYSTEM_PROMPT, ClaimExtractor, build_llm
from audit_cli.claims.models import ChunkResult, ClaimText, Kind, Verdicts, merge_runs
from audit_cli.config import load_config
from audit_cli.logs import configure_logging
from audit_cli.processing.chunker import BundleChunker, Chunk, SentenceSplitter

HERE = plb.Path(__file__).resolve().parent.parent
AGENT = HERE.parent / "audit-agent"
CHECKABLE = {"point", "structural"}
RUNS = ["", "@2"]


def old_prompt() -> str:
    """Return the notebook's extraction prompt, read from its cell so the hash matches its cache."""
    cells = json.loads((AGENT / "notebook.ipynb").read_text())["cells"]
    source = next("".join(c["source"]) for c in cells if 'SYSTEM_PROMPT = """' in "".join(c["source"]))
    return source.split('SYSTEM_PROMPT = """', 1)[1].split('""".strip()', 1)[0].strip()


OLD_CHECK_NOTE = """Fill how_to_check before you choose the kind: if you cannot name what to open
or run in this repository, the kind is subjective, external or none."""


def reason_only_prompt() -> str:
    """Return the notebook's prompt with only the reason instruction added: no examples, so its effect shows alone."""
    new_note = SYSTEM_PROMPT[SYSTEM_PROMPT.index("Fill how_to_check, then reason") :].split("\n\n", 1)[0]
    prompt = old_prompt()
    assert OLD_CHECK_NOTE in prompt
    return prompt.replace(OLD_CHECK_NOTE, new_note)


REASON_LAST_NOTE = """Fill how_to_check before you choose the kind. If you cannot name what to open or
run in this repository, the kind is subjective, external, broad or none. After
the claims, say in reason, in one short sentence, why the sentence is that
kind: what in this repository settles it, or why nothing does ("names the
`audit init` command", "a value judgement; no file settles it", "history:
says what was tried before")."""


class ReasonLastVerdict(BaseModel):
    """A sentence verdict with the reason asked for after the kind and claims."""

    n: int = Field(description="The sentence number.")
    how_to_check: str = Field(
        description="What to open or run in this repository to confirm it; empty if nothing would."
    )
    kind: Kind
    claims: list[ClaimText] = Field(
        description="Each claim the sentence makes, standalone and in the present tense; empty for none."
    )
    reason: str = Field(default="", description="One short sentence: why this kind, naming what settles it or why not.")


class ReasonLastVerdicts(BaseModel):
    """One verdict per numbered sentence, in order."""

    sentences: list[ReasonLastVerdict]


class NoReasonVerdict(BaseModel):
    """A sentence verdict without a reason, as the notebook asked for it."""

    n: int = Field(description="The sentence number.")
    how_to_check: str = Field(
        description="What to open or run in this repository to confirm it; empty if nothing would."
    )
    kind: Kind
    claims: list[ClaimText] = Field(
        description="Each claim the sentence makes, standalone and in the present tense; empty for none."
    )

    @property
    def reason(self) -> str:
        """No reason: the extractor reads one, so give it an empty one outside the schema."""
        return ""


class NoReasonVerdicts(BaseModel):
    """One verdict per numbered sentence, in order."""

    sentences: list[NoReasonVerdict]


def examples_only_prompt() -> str:
    """Return the CLI's prompt, examples and near misses included, without the reason instruction."""
    note = SYSTEM_PROMPT[SYSTEM_PROMPT.index("Fill how_to_check, then reason") :].split("\n\n", 1)[0]
    return SYSTEM_PROMPT.replace(
        note, OLD_CHECK_NOTE.replace("subjective, external or none", "subjective, external, broad or none")
    )


def reason_last_prompt() -> str:
    """Return the CLI's prompt with the reason asked for after the claims instead of before the kind."""
    note = SYSTEM_PROMPT[SYSTEM_PROMPT.index("Fill how_to_check, then reason") :].split("\n\n", 1)[0]
    return SYSTEM_PROMPT.replace(note, REASON_LAST_NOTE)


def predicted(result: ChunkResult) -> dict[int, set[str]]:
    """Return the kinds each cited sentence was cited for."""
    found: dict[int, set[str]] = {}
    for claim in result.claims:
        for n in claim.evidence:
            found.setdefault(n, set()).add(claim.claim_type)
    return found


def percent(part: int, whole: int) -> float:
    """Return part as a percentage of whole, to one decimal."""
    return round(100 * part / whole, 1) if whole else 0.0


def score(gold: dict[str, dict[int, set[str]]], results: dict[str, ChunkResult]) -> dict[str, float | int]:
    """Score results the way the notebook's Scorer does, per sentence."""
    required = cited_required = cited = allowed = typed = typed_ok = checkable = checkable_ok = 0
    for chunk_id, labels in gold.items():
        if chunk_id not in results:
            continue
        found = predicted(results[chunk_id])
        must = {n for n, kinds in labels.items() if "none" not in kinds}
        required += len(must)
        cited_required += len(must & found.keys())
        for n, kinds in found.items():
            allowed_kinds = labels.get(n, {"none"})
            cited += 1
            if allowed_kinds != {"none"}:
                allowed += 1
                typed += 1
                typed_ok += bool(kinds & allowed_kinds)
            if kinds & CHECKABLE:
                checkable += 1
                checkable_ok += bool(allowed_kinds & CHECKABLE)
    return {
        "recall": percent(cited_required, required),
        "precision": percent(allowed, cited),
        "type_ok": percent(typed_ok, typed),
        "checkable_precision": percent(checkable_ok, checkable),
        "claims": sum(len(r.claims) for r in results.values()),
        "tokens_out": sum(r.tokens.output for r in results.values()),
        "chunks": sum(cid in results for cid in gold),
    }


async def run_new(chunks: list[Chunk], extractor: ClaimExtractor, folder: plb.Path) -> dict[str, ChunkResult]:
    """Return one prompt's results for one run, calling the model only for chunks not saved yet.

    A chunk whose call fails twice, or whose answer is unreadable or lacks a verdict for some sentence twice (as the
    CLI counts it failed), is left out of the result and printed; a rerun tries it again. A saved answer with such a
    gap, saved before gaps counted as failed, is asked again.
    """
    folder.mkdir(parents=True, exist_ok=True)

    def complete(chunk: Chunk, result: ChunkResult) -> bool:
        """Whether the answer is readable and gives every sentence a verdict."""
        return not result.error and {v.n for v in result.verdicts} >= set(range(1, len(chunk.sentences) + 1))

    async def one(chunk: Chunk) -> tuple[str, ChunkResult | None]:
        """Load or extract one chunk."""
        path = folder / f"{chunk.extraction_key}.json"
        if path.exists():
            saved = ChunkResult.model_validate_json(path.read_text())
            if complete(chunk, saved):
                return chunk.id, saved
        for attempt in range(2):  # a failed call or answer is tried once more
            try:
                result = await extractor.extract(chunk)
                problem = None if complete(chunk, result) else (result.error or "a sentence has no verdict")
            except Exception as error:  # noqa: BLE001  # report and score without this chunk, not crash
                problem = f"{type(error).__name__}: {error}"
            if problem is None:
                path.write_text(result.model_dump_json())
                return chunk.id, result
            if attempt:
                print(f"left out {chunk.id}: {problem}")
        return chunk.id, None

    found = dict(await asyncio.gather(*(one(c) for c in chunks)))
    return {cid: result for cid, result in found.items() if result is not None}


async def main() -> None:
    """Score both prompts and write the comparison."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--config", type=plb.Path, required=True, help="audit.toml naming the extractor's model.")
    parser.add_argument("--bundle", type=plb.Path, default=HERE.parents[2] / ".okf", help="kmctl's bundle.")
    args = parser.parse_args()
    load_dotenv(find_dotenv(usecwd=True))
    configure_logging(HERE / "results" / "gold" / "compare.log", "info")
    config = load_config(args.config)
    agent = config.agents["extractor"]

    gold_records = [json.loads(line) for line in (AGENT / "gold.jsonl").read_text().splitlines()]
    chunks_by_id = {c.id: c for c in BundleChunker(SentenceSplitter()).chunks(args.bundle)}
    fresh = [r for r in gold_records if r["id"] in chunks_by_id and chunks_by_id[r["id"]].key == r["key"]]
    chunks = [chunks_by_id[r["id"]] for r in fresh]
    gold = {r["id"]: {int(n): set(kinds) for n, kinds in r["labels"].items()} for r in fresh}

    limit = asyncio.Semaphore(config.concurrency.max_model_calls)
    llm = build_llm(agent, config.providers[agent.provider])
    rows: dict[str, dict[str, float | int]] = {}
    merged: dict[str, dict[str, ChunkResult]] = {}
    variants: list[tuple[str, str, type[BaseModel]]] = [
        ("old", old_prompt(), NoReasonVerdicts),
        ("reason only", reason_only_prompt(), Verdicts),
        ("new", SYSTEM_PROMPT, Verdicts),
        ("new, reason last", reason_last_prompt(), ReasonLastVerdicts),
        ("examples only", examples_only_prompt(), NoReasonVerdicts),
    ]
    for name, prompt, schema in variants:
        per_run = []
        for run in RUNS:
            extractor_module.SYSTEM_PROMPT = prompt  # the extractor reads the module's prompt on each call
            extractor_module.Verdicts = schema  # type: ignore[assignment,attr-defined]  # and its answer schema when it is built
            prompt_hash = hashlib.sha256((prompt + schema.__name__).encode()).hexdigest()[:8]
            if schema is Verdicts:
                prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:8]  # keep the saved runs
            folder = HERE / "results" / "gold" / agent.model.replace("/", "_") / prompt_hash / (run or "@1")
            results = await run_new(chunks, ClaimExtractor(llm, limit), folder)
            rows[f"{name} {run or '@1'}"] = score(gold, results)
            per_run.append(results)
        merged[name] = {cid: merge_runs(per_run[0][cid], per_run[1][cid]) for cid in per_run[0] if cid in per_run[1]}
        rows[f"{name} merged"] = score(gold, merged[name])

    kinds = {name: dict(Counter(c.claim_type for r in res.values() for c in r.claims)) for name, res in merged.items()}
    reasons = [
        {"chunk": cid, "n": v.n, "kind": v.kind, "reason": v.reason}
        for cid, r in list(merged["new"].items())[:4]
        for v in r.verdicts
    ]
    out = {
        "model": agent.model,
        "gold_chunks": len(chunks),
        "gold_chunks_stale": len(gold_records) - len(fresh),
        "rows": rows,
        "kinds_merged": kinds,
        "sample_reasons": reasons,
    }
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results" / "gold_compare.json").write_text(json.dumps(out, indent=2))
    print(f"{agent.model}: {len(chunks)} gold chunks ({out['gold_chunks_stale']} stale, left out)")
    print(f"{'run':18} {'recall':>7} {'prec':>6} {'type':>6} {'check':>6} {'claims':>7} {'tok out':>8}")
    for name, row in rows.items():
        print(
            f"{name:18} {row['recall']:7} {row['precision']:6} {row['type_ok']:6} {row['checkable_precision']:6} "
            f"{row['claims']:7} {row['tokens_out']:8} {row['chunks']:6}"
        )
    print("kinds (merged):", kinds)


if __name__ == "__main__":
    asyncio.run(main())
