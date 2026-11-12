"""List every claim answered with a reason, for labelling by hand.

Run from the repository root, in the project environment:

    uv run python .okf/prototypes/mixed-claims/dump.py

It reads the audit store (``.kmctl/audit.sqlite``) and writes ``reasons.tsv``
next to this file: one row per claim whose stored answer is a reason, with the
claim's id, concept, kind, quantifier, text and the reason given.
"""

import csv
import sys
from pathlib import Path

from kmctl.claims.check_store import check
from kmctl.claims.check_verbs import list_checks
from kmctl.claims.store import Store

HERE = Path(__file__).resolve().parent


def main(root: Path) -> None:
    """Write reasons.tsv for the bundle under ``root``."""
    reasoned = {r.claim for r in list_checks(root).claims if r.status == "reason"}
    rows = []
    with Store(root) as store:
        for c in store.claims():
            if c.id in reasoned:
                found = check(store, c.id)
                rows.append(
                    [c.id, c.concept, c.kind, c.quantifier, c.claim, found.reason]
                )
    rows.sort(key=lambda r: (r[1], r[0]))
    with (HERE / "reasons.tsv").open("w", newline="", encoding="utf-8") as f:
        out = csv.writer(f, delimiter="\t")
        out.writerow(["id", "concept", "kind", "quantifier", "claim", "reason"])
        out.writerows(rows)
    print(f"wrote {len(rows)} reasons")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd())
