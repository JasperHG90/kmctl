"""What if text a later part of the page replaces (the 'confirm: superseded' rule) were a warning instead of not code?

Run from the prototype folder: python3 scripts/superseded_as_drift.py results/ties/kmctl/<run>.json
Scores the random samples and all labels both ways; changes nothing in the notebook.
"""
import contextlib, io, pathlib, sys

ns = {"__file__": str(pathlib.Path(__file__).with_name("score_labels.py"))}
with contextlib.redirect_stdout(io.StringIO()):
    exec(pathlib.Path(ns["__file__"]).read_text().split("POS = ")[0].replace("sys.argv[1]", repr(sys.argv[1])), ns)
labels, ties = ns["labels"], ns["ties"]
POS = {"tied", "tied by context", "found", "partly", "holds", "confirmed by a person"}
HELD = {"not code", "needs a person"}


def score(rows, superseded_warns):
    def status(t):
        return "superseded" if superseded_warns and t["how"].startswith("confirm: superseded") else t["status"]
    true = [s for lab, s in rows if lab in {"supported", "partly"}]
    nc = [s for lab, s in rows if lab == "not_code"]
    drift = [s for lab, s in rows if lab == "drifted"]
    rows_s = [(lab, status(t)) for lab, t in rows]
    true = [s for lab, s in rows_s if lab in {"supported", "partly"}]
    nc = [s for lab, s in rows_s if lab == "not_code"]
    drift = [s for lab, s in rows_s if lab == "drifted"]
    warned = [lab for lab, s in rows_s if s not in POS and s not in HELD]
    return (f"settled {sum(s in POS for s in true)}/{len(true)}, not-code held {sum(s in HELD for s in nc)}/{len(nc)}, "
            f"drift flagged {sum(s not in POS and s not in HELD for s in drift)}/{len(drift)}, "
            f"warnings {len(warned)} of which true {sum(l in {'supported', 'partly'} for l in warned)}")


for name, keep in [("random 120", lambda g: g == "random3"), ("random 83", lambda g: g == "random"), ("all labels", lambda g: True)]:
    rows = [(lab, ties[i]) for i, (lab, g) in labels.items() if i in ties and keep(g)]
    print(f"{name:11} now:        {score(rows, False)}")
    print(f"{name:11} superseded: {score(rows, True)}")
