"""Compare the decision model's link answers before and after the link question was reworded.

Run from the repository root, after judging every check again with the new
wording (``kmctl audit judge link ID... --config audit.toml``):

    uv run python .okf/prototypes/link-question/compare.py 2026-11-14T08:26:06+00:00

The argument is the moment the new wording was first asked. For each check
id the script takes its latest link answer asked before that moment and its
latest asked after, from the ``decisions`` table of ``.kmctl/audit.sqlite``,
and prints the level counts, the median score, and how many moved, overall
and for "wording" checks (every step a grep, query, file or help step: they
find text or values) against "code" checks (at least one code, definition or
imports step). A check rewritten between the two answers is compared all the
same; the count of those is printed. It writes ``results.csv``: one row per
check, ids and numbers only.
"""

import csv
import json
import sqlite3
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEVELS = ["unrelated", "keyword", "nearby", "the claim"]
WORDING_OPS = {"grep", "query", "file", "help"}


def score(answer: dict[str, object]) -> tuple[float, str]:
    """(score 0 to 1, most likely level) from one stored link answer."""
    probabilities = answer["link"]["probabilities"]  # type: ignore[index]
    weights = {int(k): float(p) for k, p in probabilities.items()}
    value = sum(k * p for k, p in weights.items()) / (len(LEVELS) - 1)
    return value, LEVELS[max(weights, key=lambda k: weights[k])]


def latest(db: sqlite3.Connection, before: bool, cutoff: str) -> dict[str, tuple[float, str]]:
    """Each check's latest link answer asked before (or from) ``cutoff``."""
    op = "<" if before else ">="
    rows = db.execute(
        f"SELECT subject, answers FROM decisions WHERE question = 'link' AND asked_at {op} ? ORDER BY asked_at",
        (cutoff,),
    )
    return {subject: score(json.loads(answers)) for subject, answers in rows}


def kind_of(db: sqlite3.Connection, claim_id: str) -> tuple[str, str]:
    """("wording" or "code", submitted_at) for a stored check."""
    row = db.execute("SELECT steps, submitted_at FROM checks WHERE claim_id = ?", (claim_id,)).fetchone()
    ops = {s["op"] for s in json.loads(row[0])}
    return ("wording" if ops <= WORDING_OPS else "code"), row[1]


def report(name: str, pairs: list[tuple[float, str, float, str]]) -> None:
    """Print level counts, medians and movement for one group of (old score, old level, new score, new level)."""
    if not pairs:
        return
    old = {lvl: sum(1 for p in pairs if p[1] == lvl) for lvl in LEVELS}
    new = {lvl: sum(1 for p in pairs if p[3] == lvl) for lvl in LEVELS}
    up = sum(1 for p in pairs if p[2] - p[0] > 0.05)
    down = sum(1 for p in pairs if p[0] - p[2] > 0.05)
    print(f"{name}: {len(pairs)} checks")
    print(f"  levels before: {old}")
    print(f"  levels after:  {new}")
    print(f"  median score {statistics.median(p[0] for p in pairs):.2f} -> {statistics.median(p[2] for p in pairs):.2f}")
    print(f"  below 0.5: {sum(p[0] < 0.5 for p in pairs)} -> {sum(p[2] < 0.5 for p in pairs)}")
    print(f"  up {up}, down {down}, about the same {len(pairs) - up - down} (moved more than 0.05)")


def main(cutoff: str) -> None:
    """Print the before and after comparison and write results.csv."""
    db = sqlite3.connect(Path.cwd() / ".kmctl" / "audit.sqlite")
    before, after = latest(db, True, cutoff), latest(db, False, cutoff)
    live = {r[0] for r in db.execute("SELECT claim_id FROM checks WHERE kind = 'check'")}
    rows, groups, rewritten = [], {"wording": [], "code": []}, 0
    for claim_id in sorted(set(before) & set(after) & live):
        kind, submitted = kind_of(db, claim_id)
        (s0, l0), (s1, l1) = before[claim_id], after[claim_id]
        groups[kind].append((s0, l0, s1, l1))
        asked_before = db.execute(
            "SELECT max(asked_at) FROM decisions WHERE question = 'link' AND subject = ? AND asked_at < ?",
            (claim_id, cutoff),
        ).fetchone()[0]
        rewritten += submitted > asked_before
        rows.append({"check": claim_id, "kind": kind, "before": round(s0, 3), "level_before": l0,
                     "after": round(s1, 3), "level_after": l1})  # fmt: skip
    print(f"checks judged after {cutoff}: {len(after)}; with an answer from before too: {len(rows)}")
    print(f"  of those, rewritten between the two answers: {rewritten}")
    report("all", groups["wording"] + groups["code"])
    report("wording checks (grep, query, file, help only)", groups["wording"])
    report("code checks (a code, definition or imports step)", groups["code"])
    with (HERE / "results.csv").open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=["check", "kind", "before", "level_before", "after", "level_after"])
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main(sys.argv[1])
