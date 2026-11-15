"""List judged labels whose claim the latest run reworded, paired with the run's closest claim on the same sentence.

Run from the prototype folder: python3 scripts/stale_judged.py results/ties/kmctl/<run>.json > labels/stale_judged.json
The output is the input for a fresh label of the reworded claims (labels/judged_relabel.json).
"""
import difflib, json, sys

ties = json.load(open(sys.argv[1]))["ties"]
ids = {t["claim_id"] for t in ties}
by_sentence = {}
for t in ties:
    by_sentence.setdefault((t["chunk_id"], t["sentence_n"]), []).append(t)
out = []
for label in json.load(open("judge_labels.json")):
    if label["claim_id"] in ids:
        continue
    candidates = by_sentence.get((label["chunk_id"], str(label["sentence_n"])), []) + by_sentence.get((label["chunk_id"], label["sentence_n"]), [])
    if not candidates:
        continue
    best = max(candidates, key=lambda t: difflib.SequenceMatcher(None, t["claim"].lower(), label["claim"].lower()).ratio())
    out.append({"id": best["claim_id"], "old_claim": label["claim"], "old_verdict": label["verdict"], "claim": best["claim"],
                "sentence": best["sentence"], "concept": best["concept"], "section": best["section"], "chunk_id": best["chunk_id"],
                "sentence_n": best["sentence_n"], "auditor_status": best["status"]})
json.dump(out, sys.stdout, indent=1)
