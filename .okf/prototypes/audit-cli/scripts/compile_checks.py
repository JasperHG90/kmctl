"""Pilot: turn stored claims into checks once with a model, then run the saved checks with none.

Claims are grouped by section, at most --batch per batch, and each batch goes to the check writer
(src/audit_cli/checks/writer.py) with its own turn and token budget. Where settle_claims.py found each claim's named
things is passed along (results/settle/claims.jsonl, when it exists). Run from the audit-cli folder:

    uv run python scripts/compile_checks.py write --repo ../../.. [--batches N]   # calls the model
    uv run python scripts/compile_checks.py rerun --repo ../../..                  # runs the saved checks, no model

write saves results/checks/checks.json (one entry per claim: the check and whether it held, the reason no check
fits, or unfinished) and results/checks/batches.json (turns, tokens, trimming, stops per batch); a claim already
saved is not sent again. rerun runs every saved check and prints how many hold and how long it took.
"""

import argparse
import asyncio
import json
import pathlib as plb
import sqlite3
import time
from collections import Counter
from itertools import islice
from typing import Any

from dotenv import find_dotenv, load_dotenv
from langchain_openai import ChatOpenAI
from platformdirs import user_data_dir
from pydantic import TypeAdapter

from audit_cli.checks.steps import Repository, Step, run_check
from audit_cli.checks.writer import PROMPT_HASH, Budget, ClaimInput, write_checks
from audit_cli.config import load_config
from audit_cli.logs import configure_logging

HERE = plb.Path(__file__).resolve().parent.parent
OUT = HERE / "results" / "checks"
DB = plb.Path(user_data_dir("audit-cli")) / "projects" / "kmctl-f62c60167c76" / "audit.sqlite"
STEPS = TypeAdapter(list[Step])


def located() -> dict[str, list[str]]:
    """Return, per claim id, where settle_claims.py found the claim's named things."""
    path = HERE / "results" / "settle" / "claims.jsonl"
    if not path.exists():
        return {}
    found: dict[str, list[str]] = {}
    for line in path.read_text().splitlines():
        row = json.loads(line)
        found[row["claim_id"]] = sorted({w for a in row["anchors"] for w in a["where"]})
    return found


def batches(size: int, skip: set[str]) -> list[list[ClaimInput]]:
    """Return the stored claims not yet saved, grouped by section, at most ``size`` per batch."""
    rows = sqlite3.connect(DB).execute("SELECT claim_id, chunk_id, claim FROM claims ORDER BY chunk_id, sentence_n")
    where = located()
    by_chunk: dict[str, list[tuple[str, str]]] = {}
    for claim_id, chunk_id, text in rows:
        if claim_id not in skip:
            by_chunk.setdefault(chunk_id, []).append((claim_id, text))
    found = []
    for claims in by_chunk.values():
        it = iter(claims)
        while part := list(islice(it, size)):
            found.append([ClaimInput(f"c{i}", cid, text, where.get(cid, [])) for i, (cid, text) in enumerate(part, 1)])
    return found


async def write(args: argparse.Namespace) -> None:
    """Write checks for the claims not yet saved, a bounded number of batches at once."""
    load_dotenv(find_dotenv(usecwd=True))
    config = load_config(None, search=[HERE])
    agent = config.agents["extractor"]
    provider = config.providers[agent.provider]
    llm = ChatOpenAI(
        base_url=provider.base_url,
        api_key=provider.api_key(),
        model=agent.model,
        timeout=agent.timeout,
        max_retries=agent.max_retries,
        reasoning_effort=args.effort,
    )
    repo = Repository(args.repo.resolve())
    OUT.mkdir(parents=True, exist_ok=True)
    saved: dict[str, Any] = json.loads((OUT / "checks.json").read_text()) if (OUT / "checks.json").exists() else {}
    spent: list[Any] = json.loads((OUT / "batches.json").read_text()) if (OUT / "batches.json").exists() else []
    todo = batches(args.batch, {cid for cid, e in saved.items() if e["status"] != "unfinished"})[: args.batches]
    limit = asyncio.Semaphore(config.concurrency.max_model_calls)
    budget = Budget(max_turns=args.max_turns, max_tokens=args.max_tokens)

    async def one(batch: list[ClaimInput]) -> None:
        """Write one batch and save what it produced."""
        started = time.monotonic()
        async with limit:
            try:
                result = await write_checks(llm, repo, batch, budget)
            except Exception as error:  # noqa: BLE001  # one failed batch is recorded, not fatal
                spent.append({"claims": len(batch), "error": f"{type(error).__name__}: {error}"})
                return
        texts = {c.claim_id: c.text for c in batch}
        for check in result.checks:
            saved[check.claim_id] = {
                "status": "holds" if check.holds else "fails",
                "claim": texts[check.claim_id],
                "check": check.check.model_dump(mode="json"),
                "results": [r.model_dump() for r in check.results],
            }
        for cid, reason in result.no_checks.items():
            saved[cid] = {"status": "no check", "claim": texts[cid], "reason": reason}
        for cid in result.unfinished:
            saved.setdefault(cid, {"status": "unfinished", "claim": texts[cid]})
        spent.append(
            {
                "claims": len(batch),
                "turns": result.turns,
                "tokens_in": result.tokens_in,
                "tokens_out": result.tokens_out,
                "trimmed": result.trimmed,
                "chars_sent": result.chars_sent,
                "chars_untrimmed": result.chars_untrimmed,
                "stopped": result.stopped,
                "seconds": round(time.monotonic() - started),
                "model": agent.model,
                "effort": args.effort,
                "prompt": PROMPT_HASH,
                "calls": result.calls,
            }
        )
        (OUT / "checks.json").write_text(json.dumps(saved, indent=1))
        (OUT / "batches.json").write_text(json.dumps(spent, indent=1))
        print(
            f"batch of {len(batch)}: {result.turns} turns, {result.tokens_in}+{result.tokens_out} tokens, "
            f"{len(result.checks)} checks, {len(result.no_checks)} reasons, {len(result.unfinished)} unfinished"
        )

    await asyncio.gather(*(one(b) for b in todo))
    summary(saved, spent)


def summary(saved: dict[str, Any], spent: list[Any]) -> None:
    """Print claims per status and strength, and what the batches spent."""
    print("claims by status:", dict(Counter(e["status"] for e in saved.values())))
    print("checks by strength:", dict(Counter(e["check"]["strength"] for e in saved.values() if "check" in e)))
    done = [b for b in spent if "turns" in b]
    print(
        f"batches: {len(done)} done, {len(spent) - len(done)} failed; turns {sum(b['turns'] for b in done)}; "
        f"tokens in {sum(b['tokens_in'] for b in done)}, out {sum(b['tokens_out'] for b in done)}; "
        f"stopped by budget {sum(bool(b['stopped']) for b in done)}"
    )


def rerun(args: argparse.Namespace) -> None:
    """Run every saved check with no model and print how many hold and how long it took."""
    saved: dict[str, Any] = json.loads((OUT / "checks.json").read_text())
    repo = Repository(args.repo.resolve())
    started = time.monotonic()
    outcome: Counter[str] = Counter()
    for entry in saved.values():
        if "check" in entry:
            holds, _ = run_check(repo, STEPS.validate_python(entry["check"]["steps"]))
            outcome["holds" if holds else "fails"] += 1
    print(f"{sum(outcome.values())} checks in {time.monotonic() - started:.1f}s, no model: {dict(outcome)}")


def main() -> None:
    """Parse the command line and run write or rerun."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("mode", choices=["write", "rerun"])
    parser.add_argument("--repo", type=plb.Path, required=True, help="The repository the claims describe.")
    parser.add_argument("--batch", type=int, default=8, help="Claims per batch, from one section.")
    parser.add_argument("--batches", type=int, default=None, help="Write at most this many batches (a trial).")
    parser.add_argument("--max-turns", type=int, default=20, help="Model calls per batch.")
    parser.add_argument("--max-tokens", type=int, default=250_000, help="Input plus output tokens per batch.")
    parser.add_argument("--effort", default="low", help="reasoning_effort sent to the model.")
    args = parser.parse_args()
    configure_logging(OUT / "compile.log", "info")
    if args.mode == "write":
        asyncio.run(write(args))
    else:
        rerun(args)


if __name__ == "__main__":
    main()
