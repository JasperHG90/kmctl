"""Does the router's "enough information" answer predict which claims got a check that holds?

Run from the audit-cli folder: uv run python scripts/pilots/enough_vs_outcome.py [MODEL]
Compares results/pilots/router-<model>.json (Clef by default, or jev-latest) with the one-call results on the same
claims, and writes results/pilots/enough_vs_outcome-<model>.json.
"""

import json
import sys
from collections import Counter

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from pilots import common  # the scripts folder is not a package on the path


def main(model: str) -> None:
    """Print, for one router's enough above and below 0.5, how the one-call pilots ended."""
    rows = json.loads((common.OUT / f"router-{common.slug(model)}.json").read_text())["rows"]
    router = {r["claim_id"]: r for r in rows}
    out = {}
    for name in ("oneshot-lines-grouped-low", "oneshot-lines-single-low"):
        claims = json.loads((common.OUT / f"{name}.json").read_text())["claims"]
        table = Counter(
            ("enough" if router[cid]["enough"] > 0.5 else "not enough", entry["status"])
            for cid, entry in claims.items()
        )
        out[name] = {f"{a} -> {b}": n for (a, b), n in sorted(table.items())}
    (common.OUT / f"enough_vs_outcome-{common.slug(model)}.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else common.CLEF)
