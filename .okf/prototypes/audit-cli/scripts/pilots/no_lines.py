"""List the claims the settle step showed no lines for and Clef calls about the code now: the agent's share.

Run from the audit-cli folder: uv run python scripts/pilots/no_lines.py [--sample N]

Prints each claim with its kind and the anchors the settle step found, and with --sample N a fixed random N of them
(seed 7), the sample the agent-spend pilot runs on.
"""

import argparse
import json
import random
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from pilots import common  # the scripts folder is not a package on the path

EMPTY = "(the settle step found nothing to show)"


def agent_share() -> list[common.StoredClaim]:
    """Return the claims with no lines shown, not settled, that Clef calls about the code now, in document order."""
    settled = {
        row["claim_id"]
        for row in map(json.loads, (common.HERE / "results" / "settle" / "claims.jsonl").read_text().splitlines())
        if row["verdict"] is not None
    }
    router = {r["claim_id"]: r for r in json.loads((common.OUT / "router-ollama_clef_27b.json").read_text())["rows"]}

    def current(cid: str) -> bool:
        """Whether Clef's most likely answer is that the claim is about the code now."""
        p = router[cid]["when"]
        return bool(max(p, key=lambda k: p[k]) == "current")

    return [
        c for c in common.claims() if c.claim_id not in settled and common.snippets(c) == EMPTY and current(c.claim_id)
    ]


def sample(n: int) -> list[common.StoredClaim]:
    """Return a fixed random ``n`` of the agent's share (seed 7), in document order."""
    share = agent_share()
    return sorted(random.Random(7).sample(share, n), key=lambda c: (c.chunk_id, c.n))


def main() -> None:
    """Print the agent's share, or a sample of it."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--sample", type=int, default=0)
    args = parser.parse_args()
    claims = sample(args.sample) if args.sample else agent_share()
    print(len(claims))
    for c in claims:
        print(f"{c.claim_id} [{c.kind}] {c.text}  anchors={[a['text'] for a in c.anchors]}")


if __name__ == "__main__":
    main()
