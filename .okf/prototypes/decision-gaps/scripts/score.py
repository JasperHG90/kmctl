"""Print every number the README reports, from the committed results and labels.

Usage::

    python3 scripts/score.py results/

It reads ``units.jsonl``, ``signals.jsonl``, ``judge.jsonl`` and
``labels.json`` from the folder and prints the filter table, the judge's
recall with a 95% Wilson interval, its claims on negatives by label, its
precision, cost and time, and the verdict against the bars set in the
ticket's plan before the judge ran.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

#: Bars set in the plan before the judge ran.
MIN_RECALL = 0.70
MIN_RECALL_LOWER = 0.50
MIN_PRECISION = 0.50
MAX_RANGE_COST = 10.0


def wilson(hits: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """The 95% Wilson score interval for ``hits`` out of ``n``."""
    if n == 0:
        return (0.0, 0.0)
    p = hits / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (centre - half, centre + half)


def record_only(unit: dict) -> bool:
    """Whether a positive unit changes nothing outside .okf/ and .loop/."""
    return not [p for _, p in unit["files"] if not p.startswith((".okf/", ".loop/"))]


def main() -> int:
    """Print the README's numbers."""
    folder = Path(sys.argv[1])
    units = {u["sha"]: u for u in map(json.loads, (folder / "units.jsonl").read_text().splitlines())}
    signals = [json.loads(line) for line in (folder / "signals.jsonl").read_text().splitlines()]
    judge = {j["sha"]: j for j in map(json.loads, (folder / "judge.jsonl").read_text().splitlines())}
    labels = json.loads((folder / "labels.json").read_text())

    counted = [s for s in units if units[s]["adds_decisions"] and not record_only(units[s])]
    apart = [s for s in units if units[s]["adds_decisions"] and record_only(units[s])]
    negatives = [s for s in units if not units[s]["adds_decisions"]]
    print(f"units {len(units)}, positives counted {len(counted)}, record-only apart {len(apart)} "
          f"({', '.join('ADR ' + a for s in apart for a in units[s]['adds_decisions'])}), negatives {len(negatives)}")

    print("\nfilter: threshold | units kept | hidden decisions caught")
    by_sha = {s["sha"]: s for s in signals}
    for k in range(1, 6):
        kept = [s for s in units if by_sha[s]["score"] >= k]
        caught = sum(1 for s in counted if by_sha[s]["score"] >= k)
        print(f"  score >= {k} | {len(kept)}/{len(units)} ({len(kept) / len(units):.0%}) | "
              f"{caught}/{len(counted)} ({caught / len(counted):.0%})")

    missing = [s for s in judge if judge[s]["verdict"] == "missing"]
    hits = sum(1 for s in counted if s in missing and labels["positives"].get(s, {}).get("matches_hidden_decision"))
    low, high = wilson(hits, len(counted))
    recall = hits / len(counted)
    print(f"\njudge recall {hits}/{len(counted)} ({recall:.0%}), 95% Wilson {low:.0%} to {high:.0%}")
    missed = [a for s in counted if s not in missing for a in units[s]["adds_decisions"]]
    print(f"judge missed ADR {', '.join(missed)}")

    claims = [s for s in negatives if s in missing]
    unlabelled = [s for s in claims if s not in labels["claims"]]
    assert not unlabelled, f"claims without a label: {unlabelled}"
    count = {k: sum(1 for s in claims if labels["claims"][s]["label"] == k) for k in ("gap", "false_alarm", "recorded_in_unit")}
    print(f"claims on negatives {len(claims)}/{len(negatives)} ({len(claims) / len(negatives):.0%}): "
          f"{count['gap']} gap, {count['false_alarm']} false alarm, {count['recorded_in_unit']} recorded in the unit")
    judged = count["gap"] + count["false_alarm"]
    precision = count["gap"] / judged
    plow, phigh = wilson(count["gap"], judged)
    print(f"precision {count['gap']}/{judged} ({precision:.0%}), 95% Wilson {plow:.0%} to {phigh:.0%}")
    print("precision under other readings:")
    once = len(labels.get("same_change", [])) - 1 if labels.get("same_change") else 0
    print(f"  one change claimed twice counted once: {count['gap'] - once}/{judged - once} "
          f"({(count['gap'] - once) / (judged - once):.0%})")
    correct = count["gap"] + count["recorded_in_unit"]
    print(f"  recorded in the unit counted as correct: {correct}/{len(claims)} ({correct / len(claims):.0%})")
    print(f"  recorded in the unit counted as false alarms: {count['gap']}/{len(claims)} "
          f"({count['gap'] / len(claims):.0%})")
    for flips in (1, 2):
        print(f"  {flips} gap label(s) flipped: {count['gap'] - flips}/{judged} ({(count['gap'] - flips) / judged:.0%})")
    covered = sum(1 for s in negatives if judge[s]["verdict"] == "covered")
    print(f"negatives judged covered {covered}, none {sum(1 for s in negatives if judge[s]['verdict'] == 'none')}")

    assert set(judge) == set(units), "a unit lacks a judge result"
    cost = sum(j["cost_usd"] or 0 for j in judge.values())
    seconds = sum(j["seconds"] for j in judge.values())
    print(f"cost ${cost:.2f} for the range, ${cost / len(judge):.3f} per unit; "
          f"{seconds / 60:.0f} minutes, {seconds / len(judge):.1f} s per unit")

    bars = {
        f"recall >= {MIN_RECALL:.0%}": recall >= MIN_RECALL,
        f"Wilson lower >= {MIN_RECALL_LOWER:.0%}": low >= MIN_RECALL_LOWER,
        f"precision >= {MIN_PRECISION:.0%}": precision >= MIN_PRECISION,
        f"range cost <= ${MAX_RANGE_COST:.0f}": cost <= MAX_RANGE_COST,
    }
    print("\nbars: " + ", ".join(f"{k} {'met' if v else 'NOT met'}" for k, v in bars.items()))
    print("verdict: " + ("build" if all(bars.values()) else "do not build"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
