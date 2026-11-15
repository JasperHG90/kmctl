"""Count how far steps 4 to 7 of the claim-to-code pipeline get on all stored claims, from the saved pilot results.

Run from the audit-cli folder: uv run python scripts/pilots/funnel.py

No calls. Step 4 is whether the settle step found anything for a claim and showed lines; step 5 whether it settled
it; step 6 Clef's answers (results/pilots/router-ollama_clef_27b.json); step 7 what the grouped one-call pilot did
with the 30 sampled claims, split by Clef's "enough". Writes results/pilots/funnel.json.
"""

import json
import sys
from collections import Counter

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from pilots import common  # the scripts folder is not a package on the path

EMPTY = "(the settle step found nothing to show)"


def main() -> None:
    """Print the funnel: how many claims each step settles, sends on, or leaves for the agent."""
    claims = common.claims()
    settled = {
        json.loads(line)["claim_id"]
        for line in (common.HERE / "results" / "settle" / "claims.jsonl").read_text().splitlines()
        if json.loads(line)["verdict"] is not None
    }
    router = {r["claim_id"]: r for r in json.loads((common.OUT / "router-ollama_clef_27b.json").read_text())["rows"]}
    grouped = json.loads((common.OUT / "oneshot-lines-grouped-low.json").read_text())["claims"]

    def when(cid: str) -> str:
        """Return Clef's most likely answer to what the claim is about."""
        p = router[cid]["when"]
        return str(max(p, key=lambda k: p[k]))

    rest = [c for c in claims if c.claim_id not in settled]
    lines = [c for c in rest if common.snippets(c) != EMPTY]
    no_lines = [c for c in rest if common.snippets(c) == EMPTY]
    enough = [c for c in lines if router[c.claim_id]["enough"] > 0.5]
    not_enough = [c for c in lines if router[c.claim_id]["enough"] <= 0.5]
    away = [c for c in no_lines if when(c.claim_id) != "current"]
    out = {
        "claims": len(claims),
        "step4_anchor_found": sum(bool(c.anchors) for c in claims),
        "step5_settled_free": len(settled),
        "step4_lines_shown": len(lines),
        "step4_no_lines": len(no_lines),
        "step6_lines_enough": len(enough),
        "step6_lines_not_enough": len(not_enough),
        "step6_no_lines_not_current": len(away),
        "step6_no_lines_current": len(no_lines) - len(away),
        "step7_sample_outcome": {
            label: dict(Counter(grouped[c.claim_id]["status"] for c in group if c.claim_id in grouped))
            for label, group in (("enough", enough), ("not enough", not_enough))
        },
    }
    (common.OUT / "funnel.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
