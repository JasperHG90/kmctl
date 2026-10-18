"""Can ROUTING say "Start at .okf/summary.md" and the state line say whether the
summary is current, and still keep the worst-case briefing under TOKEN_BUDGET?

Exits 0 when at least one candidate is < TOKEN_BUDGET in the worst case
(test_briefing_long_handoff_title_keeps_the_budget's repo) with the longest
summary status, and still holds the strings tests/test_briefing.py pins.
"""
import sys
import tempfile
from pathlib import Path

from typer.testing import CliRunner

import importlib
b = importlib.import_module("kmctl.briefing")
from kmctl import app

ORIG = b.ROUTING
OKF_OLD = """\
- .okf/: an OKF v0.2 bundle for people and agents working on it. Start at
  .okf/index.md. manifesto.md is the design;"""
OKF_NEW = """\
- .okf/: an OKF v0.2 bundle for people and agents working on it. Start at
  .okf/summary.md. manifesto.md is the design;"""
DOCS_OLD = """\
- docs/: pages for people who use the project, one folder per Diataxis type
  (tutorials, how-to, reference, explanation), each with a generated README.md."""
DOCS_NEW = """\
- docs/: pages for people who use the project, one folder per Diataxis type,
  each with a generated README.md."""
assert OKF_OLD in ORIG and DOCS_OLD in ORIG

CANDIDATES = {
    # 1: only swap the pointer; nothing cut.
    "swap-only": ORIG.replace(OKF_OLD, OKF_NEW),
    # 2: swap, and drop the Diataxis type list, which the Verbs line repeats
    #    (kmctl new doc tutorial|how-to|reference|explanation).
    "swap+drop-types": ORIG.replace(OKF_OLD, OKF_NEW).replace(DOCS_OLD, DOCS_NEW),
    # 3: as 2, and say the summary leads to index.md, so the pointer to the
    #    full list is not lost.
    "swap+drop-types+index": ORIG.replace(
        OKF_OLD,
        OKF_NEW.replace(".okf/summary.md.", ".okf/summary.md, then index.md."),
    ).replace(DOCS_OLD, DOCS_NEW),
}
#: Summary status appended to the state line, before its final full stop.
#: The behind form uses a 3-digit count as the longest plausible value.
STATUS = {
    "current": "; summary current",
    "behind-3": "; summary behind: 3 concepts changed",
    "behind-999": "; summary behind: 999 concepts changed",
}
PINNED = ["Knowledge in this repository", "Verbs:", "due for review", ".claude/rules/", "--fix"]


def inv(*a):
    r = CliRunner().invoke(app, list(a))
    assert r.exit_code == 0, r.output
    return r


def worst_repo(root: Path) -> Path:
    inv("init", "--path", str(root))
    for t in ("Earlier work", "Latest work"):
        inv("new", "handoff", t, "--description", f"Where {t} stands.", "--path", str(root))
    inv("new", "handoff", " ".join(["ab"] * 40), "--description", "x.", "--path", str(root))
    return root


def with_status(text: str, status: str) -> str:
    lines = text.split("\n")
    i = next(n for n, l in enumerate(lines) if l.startswith("State: "))
    assert lines[i].endswith(".")
    lines[i] = lines[i][:-1] + status + "."
    return "\n".join(lines)


best = None
with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as e:
    cases = {"worst (long handoff title)": worst_repo(Path(d)), "this repo": Path("/home/vscode/kmctl")}
    for case, root in cases.items():
        b.ROUTING = ORIG
        base = inv("briefing", "--path", str(root)).stdout
        print(f"== {case}: baseline {b.estimate_tokens(base)} / {b.TOKEN_BUDGET} ({len(base)} chars)")
        for name, routing in CANDIDATES.items():
            b.ROUTING = routing
            out = inv("briefing", "--path", str(root)).stdout
            assert routing in out
            missing = [p for p in PINNED if p not in out]
            sizes = {s: b.estimate_tokens(with_status(out, t)) for s, t in STATUS.items()}
            worst = max(sizes.values())
            print(f"  {name}: no status {b.estimate_tokens(out)}, "
                  + ", ".join(f"{s} {n}" for s, n in sizes.items())
                  + (f"  MISSING {missing}" if missing else ""))
            if case.startswith("worst") and worst < b.TOKEN_BUDGET and not missing:
                if best is None or worst < best[1]:
                    best = (name, worst)
        if case.startswith("worst"):
            sample = with_status(inv("briefing", "--path", str(root)).stdout, STATUS["behind-3"])
b.ROUTING = ORIG
print()
if best:
    print(f"best: {best[0]} at {best[1]} tokens worst case")
    print("---- ROUTING ----")
    print(CANDIDATES[best[0]])
    print("---- worst-case briefing with behind-3 (last candidate) ----")
    print(sample)
sys.exit(0 if best else 1)
