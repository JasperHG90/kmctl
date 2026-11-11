"""Show how many claims each document and sentence produced, and how many look like rewordings of each other.

Run from the audit-cli folder: uv run python scripts/claim_density.py [CONCEPT]
"""

import difflib
import sqlite3
import sys
from collections import Counter

from platformdirs import user_data_dir

DB = f"{user_data_dir('audit-cli')}/projects/kmctl-f62c60167c76/audit.sqlite"


def main() -> None:
    """Print claims per sentence and the near-duplicate pairs within a sentence."""
    db = sqlite3.connect(DB)
    rows = db.execute(
        "SELECT chunk_id, sentence_n, claim_type, claim, run FROM claims ORDER BY chunk_id, sentence_n"
    ).fetchall()
    sentences = db.execute("SELECT id, sentences FROM chunks").fetchall()
    n_sentences = sum(len(__import__("json").loads(s)) for _, s in sentences)
    print(f"{len(rows)} claims from {n_sentences} sentences: {len(rows) / n_sentences:.1f} per sentence")
    per = Counter((c, n) for c, n, *_ in rows)
    print("claims per cited sentence:", sorted(Counter(per.values()).items()))
    print("by run:", Counter(r for *_, r in rows))
    near = 0
    by_sentence: dict[tuple[str, int], list[str]] = {}
    for c, n, _, text, _ in rows:
        by_sentence.setdefault((c, n), []).append(text)
    for texts in by_sentence.values():
        for i, a in enumerate(texts):
            near += any(difflib.SequenceMatcher(a=a, b=b).ratio() > 0.6 for b in texts[:i])
    print(f"claims that read like a rewording of another claim on the same sentence: {near}")
    focus = sys.argv[1] if len(sys.argv) > 1 else None
    worst = sorted(by_sentence.items(), key=lambda kv: -len(kv[1]))[:3]
    for (c, n), texts in worst if focus is None else [kv for kv in by_sentence.items() if kv[0][0].startswith(focus)]:
        print(f"\n{c} [{n}] ({len(texts)} claims)")
        for t in texts:
            print("  -", t)


if __name__ == "__main__":
    main()
