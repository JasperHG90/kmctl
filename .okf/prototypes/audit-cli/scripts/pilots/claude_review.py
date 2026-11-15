"""Claude as the checker: draw a sample of stored claims, then compare Claude's verdicts with the pipeline's.

Run from the audit-cli folder:

    uv run python scripts/pilots/claude_review.py sample [--size N] [--seed S]
    uv run python scripts/pilots/claude_review.py compare [--model opus|haiku]

``sample`` writes results/pilots/claude-review/sample.json: every claim that has a check or a reason (the pipeline's
verdict to compare against), plus a seeded random draw of point and structural claims with no check, up to N.
Claude's reviewers write one verdicts-MODEL-*.json per batch beside it. ``compare`` joins them with the pipeline's
and writes compare-MODEL.json: per claim the pipeline's status and the model's verdict, the counts where they agree
and disagree, and, for a model other than opus, where it agrees with opus.
"""

import argparse
import collections
import json
import pathlib as plb
import random
import subprocess
from typing import Any

HERE = plb.Path(__file__).resolve().parents[2]
OUT = HERE / "results" / "pilots" / "claude-review"
FIELDS = ("claim_id", "concept", "section", "kind", "claim", "status", "steps", "why", "failed_steps", "trust")


def stored() -> list[dict[str, Any]]:
    """Return every stored claim with its check status, from audit checks list."""
    out = subprocess.run(
        ["uv", "run", "audit", "checks", "list", "--json"], cwd=HERE, capture_output=True, text=True, check=True
    )
    return list(json.loads(out.stdout)["claims"])


def sample(size: int, seed: int) -> None:
    """Write the sample: claims with a pipeline verdict, then random unchecked point and structural claims."""
    claims = stored()
    judged = [c for c in claims if c["status"] != "no check"]
    unchecked = [c for c in claims if c["status"] == "no check" and c["kind"] in {"point", "structural"}]
    drawn = random.Random(seed).sample(unchecked, max(0, min(size - len(judged), len(unchecked))))
    rows = [{k: c.get(k) for k in FIELDS} for c in judged + drawn]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "sample.json").write_text(json.dumps(rows, indent=2))
    print(f"{len(rows)} claims: {len(judged)} with a pipeline verdict, {len(drawn)} unchecked (seed {seed})")


def compare(model: str) -> None:
    """Join Claude's verdicts with the pipeline's and print where they agree."""
    rows = {r["claim_id"]: r for r in json.loads((OUT / "sample.json").read_text())}
    verdicts = {
        v["claim_id"]: v for f in sorted(OUT.glob(f"verdicts-{model}-*.json")) for v in json.loads(f.read_text())
    }
    opus = {v["claim_id"]: v for f in sorted(OUT.glob("verdicts-opus-*.json")) for v in json.loads(f.read_text())}
    joined = [{**rows[cid], "claude": v} for cid, v in verdicts.items() if cid in rows]
    pairs = collections.Counter((r["status"], r["claude"]["verdict"]) for r in joined)
    worth = collections.Counter(r["claude"]["worth_checking"] for r in joined)
    with_opus = collections.Counter(
        (opus[r["claim_id"]]["verdict"], r["claude"]["verdict"]) for r in joined if r["claim_id"] in opus
    )
    (OUT / f"compare-{model}.json").write_text(
        json.dumps(
            {"pairs": {f"{a} / {b}": n for (a, b), n in pairs.items()}, "worth_checking": worth, "claims": joined},
            indent=2,
        )
    )
    print(f"{len(joined)} of {len(rows)} claims reviewed")
    for (status, verdict), n in sorted(pairs.items()):
        print(f"  pipeline {status:9} / claude {verdict:11} {n}")
    print(f"  worth checking: {dict(worth)}")
    if model != "opus":
        same = sum(n for (a, b), n in with_opus.items() if a == b)
        print(f"  agrees with opus on {same} of {sum(with_opus.values())}")
        for (a, b), n in sorted(with_opus.items()):
            if a != b:
                print(f"    opus {a:10} / {model} {b:10} {n}")


def main() -> None:
    """Draw the sample or compare the verdicts."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("step", choices=["sample", "compare"])
    parser.add_argument("--size", type=int, default=60, help="Claims in the sample, with a pipeline verdict first.")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--model", default="opus", help="Whose verdicts to compare: the MODEL in verdicts-MODEL-*.")
    args = parser.parse_args()
    sample(args.size, args.seed) if args.step == "sample" else compare(args.model)


if __name__ == "__main__":
    main()
