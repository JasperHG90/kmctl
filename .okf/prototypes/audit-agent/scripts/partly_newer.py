"""Drift among labelled partly claims whose cited code changed after the sentence, against other settled claims.

Run from the prototype folder: python3 scripts/partly_newer.py results/ties/kmctl/<run>.json [<run>.json ...]
A claim labelled in more than one run counts once (by claim text); not-code labels are left out.
"""
import contextlib, io, pathlib, sys
from collections import Counter

SCORER = pathlib.Path(__file__).with_name("score_labels.py").read_text().split("POS = ")[0]
SETTLED = {"found", "partly", "holds", "tied"}
group, rest = {}, {}
for path in sys.argv[1:]:
    ns = {"__file__": str(pathlib.Path(__file__).with_name("score_labels.py"))}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(SCORER.replace("sys.argv[1]", repr(path)), ns)
    labels, ties = ns["labels"], ns["ties"]
    for i, (label, sample) in labels.items():
        t = ties.get(i)
        if t is None or label == "not_code" or t["status"] not in SETTLED:
            continue
        key = t["claim"].lower()
        if t["status"] == "partly" and t["code_newer"]:
            group[key] = (label, sample)
        else:
            rest.setdefault(key, (label, sample))
rest = {k: v for k, v in rest.items() if k not in group}
for name, d in [("partly, code changed after the sentence", group), ("other settled claims", rest)]:
    drifted = sum(v[0] == "drifted" for v in d.values())
    print(f"{name}: drifted {drifted} of {len(d)} ({100 * drifted / max(len(d), 1):.1f}%); samples of the drifted: "
          f"{dict(Counter(v[1] for v in d.values() if v[0] == 'drifted'))}")
