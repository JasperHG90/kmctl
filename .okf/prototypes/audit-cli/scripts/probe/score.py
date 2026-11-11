"""Probe: ask Clef and Jev one score question each; print the answers, to see that both models take scores."""

import asyncio
import sys

import httpx

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from pilots import common  # the scripts folder is not a package on the path

QUESTION = {
    "specific": {
        "type": "score",
        "instructions": "How specific is the sentence about the repository?",
        "criteria": ["names nothing", "names a part", "names a file or symbol", "names a value"],
    }
}


async def main() -> None:
    """Send the same score question to both models."""
    common.settings()
    ledger = common.Ledger()
    ledger.check(jev_calls=1)
    async with httpx.AsyncClient(timeout=60) as client:
        for model in (common.CLEF, common.JEV):
            try:
                answer = await common.decide(
                    client, model, {"sentence": "kmctl check exits 1 on a dead link."}, QUESTION
                )
                print(model, answer)
            except httpx.HTTPStatusError as error:
                print(model, "status", error.response.status_code, error.response.text[:300])
    ledger.add("probe-score", jev_calls=1)


if __name__ == "__main__":
    asyncio.run(main())
