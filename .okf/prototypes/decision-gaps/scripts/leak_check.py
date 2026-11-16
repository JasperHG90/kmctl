"""Can a check that shares nothing with hide.strip tell hidden positives from negatives?

Two detectors, each scored as AUC (0.5 is chance) of positives against
negatives over the text and files the judge sees:

- bookkeeping words: counts of words about writing records down (record,
  cites, number, index, log, summary, bundle, written, entry), a list
  separate from hide.LEAK;
- visible bookkeeping paths: count of .okf/ or .loop/ paths left in the
  unit's visible files (0 for every unit when hiding works).

Usage::

    python3 scripts/leak_check.py REPO results/units.jsonl
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hide import intent, strip, visible_files

WORDS = re.compile(r"\b(record\w*|cites?|cited|number\w*|index\w*|log|summary|bundle|written|entry|entries)\b", re.I)


def auc(pos, neg):
    """The probability that a random positive scores above a random negative, ties counting half."""
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


repo = Path(sys.argv[1])
units = [json.loads(line) for line in open(sys.argv[2])]
rows = []
words = {True: {}, False: {}}
total = {True: 0, False: 0}
for u in units:
    vis = visible_files(u["files"])
    if u["adds_decisions"] and not vis:
        continue  # record-only, reported apart
    text = strip(" ".join([u["subject"].split(":", 1)[-1], u["body"], intent(repo, u["slug"])]))
    n = max(1, len(text.split()))
    group = bool(u["adds_decisions"])
    total[group] += n
    for w in WORDS.findall(text):
        words[group][w.lower()] = words[group].get(w.lower(), 0) + 1
    rows.append((bool(u["adds_decisions"]), len(WORDS.findall(text)) / n, sum(p.startswith((".okf/", ".loop/")) for s, p in vis)))
pos = [r for r in rows if r[0]]
neg = [r for r in rows if not r[0]]
print(f"positives={len(pos)} negatives={len(neg)}")
print(f"bookkeeping words per word: AUC {auc([r[1] for r in pos], [r[1] for r in neg]):.2f}")
print(f"visible bookkeeping paths: AUC {auc([r[2] for r in pos], [r[2] for r in neg]):.2f}")
print("record-keeping words per 10k words, positives v negatives:")
for w in sorted(set(words[True]) | set(words[False]), key=lambda w: -(words[True].get(w, 0) + words[False].get(w, 0)))[:5]:
    print(f"  {w}: {1e4 * words[True].get(w, 0) / total[True]:.1f} v {1e4 * words[False].get(w, 0) / total[False]:.1f}")
