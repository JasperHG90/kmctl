"""Probe: send one claim to the one-call check writer and print the raw tool-call arguments it sends back.

Run from the audit-cli folder: uv run python scripts/probe/oneshot_raw.py CLAIM_ID

To see why an answer came back with neither a check nor a reason.
"""

import asyncio
import json
import sys

from langchain_core.messages import HumanMessage, SystemMessage

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from pilots import common, oneshot  # the scripts folder is not a package on the path


async def main(claim_id: str) -> None:
    """Send the claim and print what came back, before and after parsing."""
    common.settings()
    claim = next(c for c in common.claims() if c.claim_id == claim_id)
    ledger = common.Ledger()
    ledger.check(tokens=20_000)
    llm = common.deepseek("low")
    output = await llm.with_structured_output(oneshot.Answers, method="function_calling", include_raw=True).ainvoke(
        [SystemMessage(oneshot.PROMPT), HumanMessage(oneshot.message([("c1", claim)]))]
    )
    tokens = oneshot.usage(output["raw"])
    ledger.add("probe-oneshot-raw", tokens=tokens["in"] + tokens["out"])
    print(tokens)
    for call in output["raw"].tool_calls:
        print(json.dumps(call["args"], indent=1)[:3000])
    print("parsed:", output["parsed"])
    print("content:", str(output["raw"].content)[:1500])


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
