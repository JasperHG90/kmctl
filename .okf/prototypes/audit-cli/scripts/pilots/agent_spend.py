"""Pilot: what the searching agent spends on the claims the one call could not settle, and what changes it.

Run from the audit-cli folder, with the shell's keys loaded:

    uv run python scripts/pilots/agent_spend.py before   # the agent as it was: no lines, history trimmed
    uv run python scripts/pilots/agent_spend.py after    # dossier lines up front, history sent as it grew
    uv run python scripts/pilots/agent_spend.py tools    # after, plus CodeSearch and Outline
    uv run python scripts/pilots/agent_spend.py hints    # tools, plus the syntax that often fails in the prompt
    uv run python scripts/pilots/agent_spend.py bare-tools   # code tools and hints, no lines up front
    uv run python scripts/pilots/agent_spend.py before --first 1 --tokens 80000   # one batch, a smaller budget
    uv run python scripts/pilots/agent_spend.py tools --all                       # all 15 claims, not 8

The sample is a fixed random 8 (seed 7), or with --all every one, of the agent's claims whose grouped one call with
dossier lines failed or came back unanswered (results/pilots/oneshot-agent-grouped-low-retry.json): 15. Claims go in
batches of at most four from one concept, at most three batches at a time, each through the ledger. "after" changes
two things at once: every claim's dossier lines (scripts/pilots/dossier.py) are in the first message, and older tool
results are not rewritten as notes, so each call's input starts with the last call's and the provider's prompt
cache can serve it.

Writes results/pilots/agent-spend-<variant>[-all][-firstN].json: per batch the turns, input, output and cached tokens and the tool
calls; per claim its check and whether it holds, or its reason.
"""

import argparse
import asyncio
import json
import random
import sys
import time
from collections import Counter, defaultdict
from typing import Any

from audit_cli.checks.steps import Repository
from audit_cli.checks.writer import Budget, ClaimInput, write_checks

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from pilots import common, oneshot  # the scripts folder is not a package on the path

SAMPLE = 8
BATCH = 4
BATCH_TOKENS = 120_000  # each batch's budget, and what the ledger keeps in reserve before it


def sample(every: bool = False) -> list[common.StoredClaim]:
    """Return the fixed sample of the agent's claims the one call failed on or left unanswered: 8, or all of them."""
    results = json.loads((common.OUT / "oneshot-agent-grouped-low-retry.json").read_text())["claims"]
    left = [c for c in common.claims() if results.get(c.claim_id, {}).get("status") in {"fails", "unanswered"}]
    chosen = left if every else random.Random(7).sample(left, SAMPLE)
    return sorted(chosen, key=lambda c: (c.chunk_id, c.n))


def batches(claims: list[common.StoredClaim]) -> list[list[common.StoredClaim]]:
    """Split claims into batches of at most four from one concept, in order."""
    by_concept: dict[str, list[common.StoredClaim]] = defaultdict(list)
    for claim in claims:
        by_concept[claim.concept].append(claim)
    return [group[i : i + BATCH] for group in by_concept.values() for i in range(0, len(group), BATCH)]


VARIANTS = {  # variant: (lines up front, trim history, code tools, hints)
    "before": (False, True, False, False),
    "after": (True, False, False, False),
    "tools": (True, False, True, False),
    "hints": (True, False, True, True),
    "bare-tools": (False, False, True, True),  # no lines up front: the code tools and hints in their place
}
MAX_BATCHES = 3


async def main(variant: str, first: int, tokens: int, every: bool, tag: str = "") -> None:
    """Run the agent on the first ``first`` batches of the sample (0: all), each with ``tokens`` to spend."""
    common.settings()
    lines, trim, code_tools, hints = VARIANTS[variant]
    claims = sample(every)
    repo = Repository(common.REPO)
    ledger = common.Ledger()
    llm = common.deepseek("low")
    budget = Budget(max_tokens=tokens, trim=trim)
    out: dict[str, Any] = {"variant": variant, "budget_tokens": tokens, "batches": [], "claims": {}}
    path = common.OUT / (
        f"agent-spend-{variant}{'-all' if every else ''}{f'-first{first}' if first else ''}{f'-{tag}' if tag else ''}.json"
    )
    limit = asyncio.Semaphore(MAX_BATCHES)

    async def one(batch: list[common.StoredClaim]) -> None:
        """Run one batch and record what it wrote and spent."""
        async with limit:
            try:
                ledger.check(tokens=tokens * 3 // 2)  # a batch can pass its budget by a call or two (see Budget)
            except common.CapReached as error:
                out["stopped"] = str(error)
                return
            inputs = [
                ClaimInput(
                    f"c{i}",
                    c.claim_id,
                    c.text,
                    located=common.located_files(c),
                    lines=oneshot.lines_for(c) if lines else "",
                )
                for i, c in enumerate(batch, 1)
            ]
            started = time.monotonic()
            result = await write_checks(llm, repo, inputs, budget, code_tools=code_tools, hints=hints)
            ledger.add(f"agent-spend-{variant}", tokens=result.tokens_in + result.tokens_out)
        out["batches"].append(
            {
                "claims": len(batch),
                "turns": result.turns,
                "in": result.tokens_in,
                "out": result.tokens_out,
                "cached": result.tokens_cached,
                "seconds": round(time.monotonic() - started),
                "stopped": result.stopped,
                "tools": dict(Counter(c.split(" ", 2)[1] for c in result.calls)),
                "calls": result.calls,
            }
        )
        text = {c.claim_id: c.text for c in batch}
        for written in result.checks:
            out["claims"][written.claim_id] = {
                "claim": text[written.claim_id],
                "status": "holds" if written.holds else "fails",
                "check": written.check.model_dump(mode="json"),
                "results": [r.model_dump() for r in written.results],
            }
        for claim_id, reason in result.no_checks.items():
            out["claims"][claim_id] = {"claim": text[claim_id], "status": "no check", "reason": reason}
        for claim_id in result.unfinished:
            out["claims"][claim_id] = {"claim": text[claim_id], "status": "unfinished"}
        path.write_text(json.dumps(out, indent=1))  # kept if a later batch stops

    await asyncio.gather(*(one(b) for b in batches(claims)[: first or None]))
    done = sum(b["claims"] for b in out["batches"]) or 1
    spent = {k: sum(b[k] for b in out["batches"]) for k in ("turns", "in", "out", "cached")}
    out["summary"] = spent | {
        "claims": done,
        "tokens_per_claim": round((spent["in"] + spent["out"]) / done),
        "uncached_per_claim": round((spent["in"] - spent["cached"] + spent["out"]) / done),
        "tools": dict(sum((Counter(b["tools"]) for b in out["batches"]), Counter())),
        "status": dict(Counter(e["status"] for e in out["claims"].values())),
        "ledger_total": ledger.data["tokens"],
    }
    path.write_text(json.dumps(out, indent=1))
    print(json.dumps(out["summary"], indent=1))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("variant", choices=list(VARIANTS))
    parser.add_argument("--all", action="store_true", help="Run on all 15 claims, not the fixed 8.")
    parser.add_argument("--tag", default="", help="A word added to the results file name, to keep an earlier run.")
    parser.add_argument("--first", type=int, default=0, help="Run only the first N batches (0: all).")
    parser.add_argument("--tokens", type=int, default=BATCH_TOKENS, help="Each batch's token budget.")
    args = parser.parse_args()
    asyncio.run(main(args.variant, args.first, args.tokens, args.all, args.tag))
