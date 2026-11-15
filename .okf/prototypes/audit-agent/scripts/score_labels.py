"""Score a ties file against every Opus label: retrieval, precision, checkability. Run from the prototype folder: python3 scripts/score_labels.py results/ties/kmctl/<run>.json"""
import json, sys, glob, os
from collections import Counter
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "labels")  # Opus labels, one file per batch
labels = {}
for l in json.load(open("judge_labels.json")):
    labels[l["claim_id"]] = (l["verdict"], "judged")
for f in sorted(glob.glob(f"{S}/prec_out_*.json")):
    for l in json.load(open(f)):
        labels[l["id"]] = (l["verdict"], "found-sample" if l["auditor_status"] != "needs a person" else "person-sample")
for f in sorted(glob.glob(f"{S}/rand_out_*.json") + glob.glob(f"{S}/rand2_out_*.json")):
    for l in json.load(open(f)):
        labels[l["id"]] = (l["verdict"], "random")
for f in sorted(glob.glob(f"{S}/rand3_out_*.json") + glob.glob(f"{S}/rand4_out_*.json")):
    for l in json.load(open(f)):
        labels[l["id"]] = (l["verdict"], "random3")
for f in sorted(glob.glob(f"{S}/neg_out_*.json")):
    for l in json.load(open(f)):
        labels[l["id"]] = (l["verdict"], "warning-sample")
ties = {r["claim_id"]: r for r in json.load(open(sys.argv[1]))["ties"]}
# Labels are keyed by claim id (a hash of the claim text); when extraction rewords a claim, fall back to the
# closest claim on the same sentence.
import difflib
meta = {}
for f in glob.glob(f"{S}/*_out_*.json"):
    for l in json.load(open(f)):
        if isinstance(l, dict) and "chunk_id" in l and "id" in l: meta[l["id"]] = l
for l in json.load(open("judge_labels.json")): meta[l["claim_id"]] = l
by_sentence = {}
for r in ties.values(): by_sentence.setdefault((r["chunk_id"], r["sentence_n"]), []).append(r)
remapped = 0
for i in list(labels):
    if i in ties or i not in meta: continue
    m = meta[i]; cands = by_sentence.get((m["chunk_id"], m["sentence_n"]), [])
    if not cands: continue
    best = max(cands, key=lambda r: difflib.SequenceMatcher(None, r["claim"].lower(), m["claim"].lower()).ratio())
    if difflib.SequenceMatcher(None, best["claim"].lower(), m["claim"].lower()).ratio() > 0.5 and best["claim_id"] not in labels:
        labels[best["claim_id"]] = labels.pop(i); remapped += 1
# Fresh labels of the current wording beat a remapped old label (scripts/stale_judged.py, then an Opus label).
# The fresh label replaces the verdict and keeps the sample the claim was drawn for.
for fresh in [os.path.join(S, "judged_relabel.json")] + sorted(glob.glob(f"{S}/stale_relabel_*.json")):
    if os.path.exists(fresh):
        for l in json.load(open(fresh)):
            group = labels[l["id"]][1] if l["id"] in labels else "judged"
            labels[l["id"]] = (l["verdict"], group)
print(f"remapped {remapped} labels to reworded claims")
POS = {"tied", "tied by context", "found", "partly", "holds", "confirmed by a person"}
CODE_NO = {"not code", "needs a person"}
rows = [(labels[i][0], labels[i][1], ties[i]["status"], ties[i]["claim"]) for i in labels if i in ties]
print(f"{len(rows)} of {len(labels)} labels match a claim in this run")
true = [r for r in rows if r[0] in {"supported", "partly"}]
nc = [r for r in rows if r[0] == "not_code"]
said = [r for r in rows if r[2] in POS]
print(f"retrieval: true claims the audit settles {sum(r[2] in POS for r in true)}/{len(true)} ({Counter(r[2] for r in true if r[2] not in POS)})")
print(f"precision: claims the audit settles that are true {sum(r[0] in {'supported','partly'} for r in said)}/{len(said)} ({Counter(r[0] for r in said if r[0] not in {'supported','partly'})})")
print(f"checkability: not-code claims held back {sum(r[2] in CODE_NO for r in nc)}/{len(nc)} ({Counter(r[2] for r in nc if r[2] not in CODE_NO)}); "
      f"true claims held back {sum(r[2] in CODE_NO for r in true)}/{len(true)}")
WARN = {"broken", "not found", "unconfirmed", "could not check", "contradicted", "no instances", "superseded"}
warned = [r for r in rows if r[2] in WARN]
print(f"false alarms: warnings on claims labelled supported or partly {sum(r[0] in {'supported','partly'} for r in warned)}/{len(warned)}; "
      f"on not_code {sum(r[0] == 'not_code' for r in warned)}; drifted {sum(r[0] == 'drifted' for r in warned)}")
for g in ["judged", "found-sample", "person-sample", "warning-sample"]:
    sub = [r for r in rows if r[1] == g]
    print(f"  {g}: {len(sub)}, labels {dict(Counter(r[0] for r in sub))}, statuses {dict(Counter(r[2] for r in sub))}")
if "-v" in sys.argv:
    for r in rows:
        bad = (r[0] in {"supported", "partly"} and r[2] not in POS) or (r[0] not in {"supported", "partly"} and r[2] in POS)
        if bad: print(f"  label {r[0]:10} status {r[2]:15} {r[3][:90]}")

rand = [r for r in rows if r[1] == "random"]
if rand:
    t = [r for r in rand if r[0] in {"supported", "partly"}]; n = [r for r in rand if r[0] == "not_code"]; d = [r for r in rand if r[0] == "drifted"]
    s_ = [r for r in rand if r[2] in POS]
    print(f"RANDOM SAMPLE ({len(rand)}): true claims settled {sum(r[2] in POS for r in t)}/{len(t)}; settled that are true {sum(r[0] in {'supported','partly'} for r in s_)}/{len(s_)}; "
          f"not-code held back {sum(r[2] in CODE_NO for r in n)}/{len(n)}; drifted flagged {sum(r[2] not in POS and r[2] not in CODE_NO for r in d)}/{len(d)}")
    for r in rand:
        bad = (r[0] in {"supported", "partly"}) != (r[2] in POS)
        if bad: print(f"  label {r[0]:10} status {r[2]:15} {r[3][:90]}")

r3 = [r for r in rows if r[1] == "random3"]
if r3:
    t = [r for r in r3 if r[0] in {"supported", "partly"}]; n = [r for r in r3 if r[0] == "not_code"]; d = [r for r in r3 if r[0] == "drifted"]
    s_ = [r for r in r3 if r[2] in POS]
    print(f"RANDOM 3 ({len(r3)}): true claims settled {sum(r[2] in POS for r in t)}/{len(t)}; settled that are true {sum(r[0] in {'supported','partly'} for r in s_)}/{len(s_)}; "
          f"not-code held back {sum(r[2] in CODE_NO for r in n)}/{len(n)}; drifted flagged {sum(r[2] not in POS and r[2] not in CODE_NO for r in d)}/{len(d)}")
    for r in r3:
        if (r[0] in {"supported", "partly"}) != (r[2] in POS): print(f"  label {r[0]:10} status {r[2]:15} {r[3][:90]}")
