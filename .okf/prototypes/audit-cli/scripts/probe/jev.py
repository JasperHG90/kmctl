"""Probe: ask Jev one noul at the TypeSafe systemone endpoint; print the status and the answer, never the key."""

import asyncio
import sys

import httpx

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from pilots import common  # the scripts folder is not a package on the path


async def main() -> None:
    """Send one yes/no question and print what came back."""
    common.settings()
    ledger = common.Ledger()
    ledger.check(jev_calls=1)
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            answer = await common.decide(
                client,
                common.JEV,
                {"claim": "kmctl check fails when a summary passes 500 words."},
                {"about_code": {"type": "noul", "instructions": "Is the claim about what code does?"}},
            )
        except httpx.HTTPStatusError as error:
            print("status", error.response.status_code, error.response.text[:200])
            return
    ledger.add("probe-jev", jev_calls=1)
    print(answer)


if __name__ == "__main__":
    asyncio.run(main())
