"""Pilot: can a decision model tell a failing check that found drift from a check that is wrong?

Run from the audit-cli folder, with the shell's keys loaded:

    uv run python scripts/pilots/failure_judge.py [MODEL]   # ollama/clef:27b (default) or jev-latest

Asks, for every failing check in results/pilots/failures.jsonl (scripts/pilots/failures.py), given the claim, its
sentence, the check's steps and why, and what each step saw: a noul "does this show the claim is false?" and a
choice between the claim being false, the check being wrong, and unclear. Scores both against the hand labels in
results/pilots/failure_labels.json ("unsure" ones left out) and writes results/pilots/failure-judge-<model>.json.
"""

import asyncio
import json
import sys
from typing import Any

import httpx

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from pilots import common, questions  # the scripts folder is not a package on the path

MAX_CONCURRENT = 4
JUDGE = {
    "claim_false": {
        "type": "noul",
        "instructions": "A check was written to test the claim and it failed. Does what its steps saw show that the "
        "claim is false about the repository, rather than that the check was written wrong (wrong files, a guessed "
        "pattern, a syntax error, a word that does not have to be there)?",
    },
    "cause": {
        "type": "choice",
        "instructions": "Why did the check fail?",
        "criteria": {
            "claim_false": "what the steps saw contradicts the claim: the repository is not as the claim says",
            "check_wrong": "the check looked in the wrong place, guessed code it was not shown, could not run, or "
            "tested something the claim does not need",
            "unclear": "what the steps saw does not settle it either way",
        },
    },
}


def state(failure: dict[str, Any]) -> dict[str, Any]:
    """Return what the decision model sees about one failing check."""
    return {
        "claim": failure["claim"],
        "sentence": failure["sentence"],
        "check_why": failure["why"],
        "steps": [
            {"step": step, "held": seen["holds"], "saw": seen["detail"]}
            for step, seen in zip(failure["steps"], failure["saw"], strict=False)
        ],
    }


async def main(model: str) -> None:
    """Ask every failing check, score and save."""
    common.settings()
    failures = [json.loads(line) for line in (common.OUT / "failures.jsonl").read_text().splitlines()]
    labels = json.loads((common.OUT / "failure_labels.json").read_text())
    drift, unsure = set(labels["drift"]), set(labels["unsure"])
    ledger = common.Ledger()
    if model == common.JEV:
        ledger.check(jev_calls=len(failures))
    limit = asyncio.Semaphore(MAX_CONCURRENT)
    answers: dict[str, Any] = {}
    async with httpx.AsyncClient(timeout=180) as client:

        async def one(failure: dict[str, Any]) -> None:
            """Ask about one failing check."""
            async with limit:
                answers[failure["id"]] = await common.decide(client, model, state(failure), JUDGE)

        await asyncio.gather(*(one(f) for f in failures))
    if model == common.JEV:
        ledger.add("failure-judge", jev_calls=len(failures))
    scored = [f for f in failures if f["id"] not in unsure]
    truth = [f["id"] in drift for f in scored]
    noul = [answers[f["id"]]["claim_false"] for f in scored]
    cause = [questions.argmax(answers[f["id"]]["cause"]) for f in scored]
    ranked = sorted(scored, key=lambda f: -answers[f["id"]]["claim_false"])
    summary = {
        "model": model,
        "failures": len(failures),
        "scored": len(scored),
        "drift": sum(truth),
        "auc_claim_false": questions.auc(noul, truth),
        "drift_ranks": [ranked.index(f) + 1 for f in scored if f["id"] in drift],
        "noul_above_half": {
            "drift": sum(n > 0.5 for n, t in zip(noul, truth, strict=True) if t),
            "check": sum(n > 0.5 for n, t in zip(noul, truth, strict=True) if not t),
        },
        "cause_by_label": {
            "drift": questions.by_option([c for c, t in zip(cause, truth, strict=True) if t], [True] * sum(truth)),
            "check": questions.by_option(
                [c for c, t in zip(cause, truth, strict=True) if not t], [True] * (len(truth) - sum(truth))
            ),
        },
        "unsure": {i: answers[i] for i in sorted(unsure)},
    }
    out = common.OUT / f"failure-judge-{common.slug(model)}.json"
    out.write_text(json.dumps({"summary": summary, "answers": answers}, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else common.CLEF))
