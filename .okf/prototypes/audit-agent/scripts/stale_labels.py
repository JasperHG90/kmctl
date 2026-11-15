"""List every label (except the judged set, see stale_judged.py) whose claim the latest run reworded, with the run's closest claim.

Run from the prototype folder: python3 scripts/stale_labels.py results/ties/kmctl/<run>.json
Writes labels/stale_blind_<n>.json in three batches (no old verdict, no audit status) for a fresh label, and labels/stale_all.json.
"""
import difflib, glob, json, sys

ties = json.load(open(sys.argv[1]))["ties"]
ids = {t["claim_id"] for t in ties}
by_sentence = {}
for t in ties:
    by_sentence.setdefault((t["chunk_id"], str(t["sentence_n"])), []).append(t)
out, taken = [], set()
for f in sorted(glob.glob("labels/*_out_*.json")):
    if "localstack" in f or "judge_out" in f:
        continue
    for label in json.load(open(f)):
        if label["id"] in ids or "chunk_id" not in label:
            continue
        candidates = by_sentence.get((label["chunk_id"], str(label["sentence_n"])), [])
        if not candidates:
            continue
        best = max(candidates, key=lambda t: difflib.SequenceMatcher(None, t["claim"].lower(), label["claim"].lower()).ratio())
        if difflib.SequenceMatcher(None, best["claim"].lower(), label["claim"].lower()).ratio() <= 0.5 or best["claim_id"] in taken:
            continue
        taken.add(best["claim_id"])
        out.append({"id": best["claim_id"], "file": f, "old_verdict": label["verdict"], "concept": best["concept"], "section": best["section"],
                    "sentence": best["sentence"], "claim": best["claim"], "auditor_status": best["status"]})
json.dump(out, open("labels/stale_all.json", "w"), indent=1)
for n in range(3):
    batch = [{k: x[k] for k in ["id", "concept", "section", "sentence", "claim"]} for x in out[n::3]]
    json.dump(batch, open(f"labels/stale_blind_{n}.json", "w"), indent=1)
print(len(out), "stale labels")
