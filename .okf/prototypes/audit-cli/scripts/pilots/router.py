"""Pilot: a decision model as the router in front of the checker, asked typed questions about every stored claim.

Run from the audit-cli folder, with the shell's keys loaded:

    uv run python scripts/pilots/router.py [MODEL]      # ollama/clef:27b (default) or jev-latest

Two calls per claim. The first sees the claim, its sentence and section, and is asked:

- when: is it about the repository now, or history, a rule for people, an intent, or an outside tool;
- code_can_answer: could the repository's own files settle it;
- kind: the extractor's six kinds, to compare with what the extractor chose.

The second adds the lines the settle step found (scripts/pilots/common.py snippets) and asks whether they are
enough to decide the claim. Writes results/pilots/router-<model>.json (every answer's probabilities, per claim)
and prints the summary.
"""

import asyncio
import json
import sys
import time
from collections import Counter
from typing import Any

import httpx

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from pilots import common  # the scripts folder is not a package on the path

ROUTE = {
    "when": {
        "type": "choice",
        "instructions": "What is the claim about? The claim may have been rewritten in the present tense, so judge "
        "by the sentence it comes from.",
        "criteria": {
            "current": "what the repository's code, configuration or files do or hold now",
            "history": "what happened, was tried, decided or replaced before, or which record replaces which",
            "rule": "a rule, habit or duty for people or agents: what they must, should or may do",
            "intent": "a purpose, audience or reason: who something is for, why it exists or was chosen",
            "outside": "what a tool, service or platform outside the repository does on its own (GitHub, a runner, "
            "an operating system), not what the repository configures it to do",
        },
    },
    "code_can_answer": {
        "type": "noul",
        "instructions": "Could reading or running this repository's own files (code, configuration, workflows, "
        "tests) settle whether the claim is true today? Documents that restate the claim do not count.",
    },
    "kind": {
        "type": "choice",
        "instructions": "Which kind of claim is it?",
        "criteria": {
            "point": "one specific fact you can check at one place: a value, a name, a default, a flag, a file",
            "structural": "a fact about how parts relate or about every member of a set you can list: every "
            "workflow, no module imports another",
            "broad": "a sweeping statement about the whole system with no list to go through",
            "subjective": "a value judgement or opinion",
            "external": "a fact about something outside the repository",
            "none": "no claim about the repository at all",
        },
    },
}
ENOUGH = {
    "enough": {
        "type": "noul",
        "instructions": "Do the lines shown contain enough to decide whether the claim is true, without opening "
        "anything else? Lines that only mention a name the claim uses are not enough.",
    }
}


def argmax(probabilities: dict[str, float]) -> str:
    """Return the most likely answer of a choice."""
    return max(probabilities, key=lambda k: probabilities[k])


async def main(model: str) -> None:
    """Ask both question sets of every claim and save the answers."""
    common.settings()
    claims = common.claims()
    ledger = common.Ledger()
    if model == common.JEV:
        ledger.check(jev_calls=2 * len(claims))
    rows: list[dict[str, Any]] = []
    started = time.monotonic()
    limit = asyncio.Semaphore(4)
    async with httpx.AsyncClient(timeout=180) as client:

        async def one(claim: common.StoredClaim) -> None:
            """Route one claim."""
            state = {"claim": claim.text, "sentence": claim.sentence, "from": claim.chunk_id}
            async with limit:
                route = await common.decide(client, model, state, ROUTE)
                enough = await common.decide(client, model, state | {"lines": common.snippets(claim)}, ENOUGH)
            rows.append(
                {"claim_id": claim.claim_id, "claim": claim.text, "extractor_kind": claim.kind} | route | enough
            )

        await asyncio.gather(*(one(c) for c in claims))
    if model == common.JEV:
        ledger.add("router", jev_calls=2 * len(claims))
    when = Counter(argmax(r["when"]) for r in rows)
    kind_agree = sum(argmax(r["kind"]) == r["extractor_kind"] for r in rows)
    summary = {
        "model": model,
        "claims": len(rows),
        "seconds": round(time.monotonic() - started),
        "when": dict(when),
        "code_can_answer_yes": sum(r["code_can_answer"] > 0.5 for r in rows),
        "kind_agrees_with_extractor": f"{kind_agree} of {len(rows)}",
        "kind_confusion": dict(
            Counter(
                f"{r['extractor_kind']} -> {argmax(r['kind'])}"
                for r in rows
                if argmax(r["kind"]) != r["extractor_kind"]
            )
        ),
        "enough_yes": sum(r["enough"] > 0.5 for r in rows),
    }
    common.OUT.mkdir(parents=True, exist_ok=True)
    (common.OUT / f"router-{common.slug(model)}.json").write_text(
        json.dumps({"summary": summary, "rows": rows}, indent=1)
    )
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else common.CLEF))
