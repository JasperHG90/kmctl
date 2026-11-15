"""select-tests risk 1: how much of the suite would the ported selector run per commit?

Usage: python risk1_saving.py MAP_JSON UPSTREAM_DIR [N]

MAP_JSON is a per-test coverage map of the default suite recorded at one commit
(BASE, in the file). UPSTREAM_DIR holds select_tests.py from
JasperHG90/loop-engineering-harness@9bc19cb6; its select() runs unchanged, with
the fallback and read rules swapped for this repo's. For each of the last N
non-merge commits before BASE that touch a path outside .loop/, the commit's own
diff is applied to the BASE map: its old-side lines are carried to BASE's line
numbers through `git diff C^ BASE`. Run from the repository.

Exits 0 when the saving is real (fewer than half the commits fall back to a
full run and the median commit runs under half the suite), 1 otherwise.
"""
import json, re, statistics, subprocess, sys
from collections import Counter
from pathlib import Path

MAP, UP = Path(sys.argv[1]), sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 40
sys.path.insert(0, UP)
import select_tests as st  # noqa: E402

# This repo's rules (plan O2): fall back on fixtures, tooling, conftest, apm/, deps.
st.FALLBACK_PREFIXES = ("tests/fixtures/", "tests/tools/", "apm/")
st.FALLBACK_FILES = frozenset({"pyproject.toml", "uv.lock"})
st.PLUGIN_NARROWED = ()
st.DIRECTORY_TESTS = {"scripts/": "tests/scripts"}
st.READABLE_ROOTS = frozenset({"src", "apm", "docs", ".okf", "scripts", "starter", "action"})
st.ALWAYS = "tests/structure"  # no such folder here; nothing is always run

def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, check=True).stdout

raw = json.loads(MAP.read_text())
BASE = raw["base"]
lines = {f: {int(l): frozenset(ids) for l, ids in per.items()}
         for f, per in raw["lines"].items() if not f.startswith("/")}
tests = frozenset(raw["tests"])
tmap = st.TestMap(snapshot=BASE, base=BASE, lines=lines, tests=tests)
uncovered = {t for t in tests - tmap.covered()}
present = set(git("ls-tree", "-r", "--name-only", BASE).splitlines())
reads = st.scan_reads(Path.cwd())

HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

def translate(path, old_lines, parent):
    """Carry line numbers of `path` at `parent` to BASE's numbering."""
    hunks = []
    for ln in git("diff", "-U0", "--no-renames", parent, BASE, "--", path).splitlines():
        if m := HUNK.match(ln):
            os_, oc, ns, nc = int(m[1]), int(m[2] or 1), int(m[3]), int(m[4] or 1)
            hunks.append((os_, oc, ns, nc))
    out = set()
    for L in old_lines:
        delta, placed = 0, False
        for os_, oc, ns, nc in hunks:
            if oc and os_ <= L < os_ + oc:
                out |= set(range(ns, ns + nc)) if nc else {max(ns, 1)}
                placed = True
                break
            if (oc and os_ + oc - 1 < L) or (not oc and os_ < L):
                delta += nc - oc
        if not placed:
            out.add(L + delta)
    return out

def count(targets):
    n = 0
    for t in tests:
        f = t.split("::", 1)[0]
        if t in targets or f in targets or any(t.startswith(d + "/") for d in targets):
            n += 1
    return n

commits = []
for h in git("log", "--no-merges", "--format=%H", BASE).splitlines():
    files = git("diff-tree", "--no-commit-id", "-r", "--name-only", "--root", h).splitlines()
    if any(not f.startswith(".loop/") for f in files):
        commits.append(h)
    if len(commits) == N:
        break

total = len(tests)
rows, fractions, reasons = [], [], Counter()
for h in commits:
    parent = h + "^"
    diff = git("diff", "--no-renames", parent, h)
    changed = st.parse_diff(diff)
    ins = st.parse_insertions(diff)
    changed.pop(".loop", None)
    changed = {p: l for p, l in changed.items() if not p.startswith(".loop/")}
    srcs, carried, carried_ins = {}, {}, {}
    for p, l in changed.items():
        if p.startswith("src/") and p.endswith(".py") and p in present:
            carried[p] = translate(p, l, parent)
            carried_ins[p] = translate(p, ins.get(p, set()), parent) if p in ins else set()
            srcs[p] = git("show", f"{BASE}:{p}")
        else:
            carried[p] = l
    sel = st.select(tmap, carried, present, old_sources=srcs, insertions=carried_ins, reads=reads)
    subj = git("log", "-1", "--format=%h %s", h).strip()[:70]
    if sel.full:
        why = sel.reasons[-1].removeprefix("full run: ")
        path = why.split(" ", 1)[0].rstrip(":")
        kind = ("conftest" if path.endswith("conftest.py") else
                next((p for p in st.FALLBACK_PREFIXES if path.startswith(p)), None) or
                (path if path in st.FALLBACK_FILES else
                 "non-Python file in src" if path.startswith("src/") else "test support code"))
        reasons[kind] += 1
        fractions.append(1.0)
        rows.append(f"FULL  {total:5d}/{total}  {subj}  [{why}]")
    else:
        n = count(sel.targets)
        fractions.append(n / total)
        rows.append(f"SEL   {n:5d}/{total}  {subj}")

full = sum(1 for r in rows if r.startswith("FULL"))
sel_counts = sorted(int(r.split()[1].split("/")[0]) for r in rows if r.startswith("SEL"))
print(f"map recorded at {BASE[:8]}: {total} tests, {len(uncovered)} with no kmctl line "
      f"(always selected), {len(lines)} measured files")
print(f"commits: last {len(commits)} non-merge commits touching a path outside .loop/")
print("\n".join(rows))
print(f"\nfull-run fallbacks: {full}/{len(commits)}  by cause: {dict(reasons)}")
if sel_counts:
    print(f"selected runs: {len(sel_counts)}; tests run min {sel_counts[0]}, median "
          f"{statistics.median(sel_counts):.0f}, max {sel_counts[-1]} of {total}")
med = statistics.median(fractions)
print(f"median share of the suite per commit, fallbacks counted as 100%: {med:.0%}")
print(f"mean share: {statistics.mean(fractions):.0%}")

# Sensitivity, not the verdict: 21 test files build their own .okf/ in a temp repo
# and name ".okf", so any .okf/ change runs them all. Without .okf as a readable
# root, what would the selected commits run?
st.READABLE_ROOTS = st.READABLE_ROOTS - {".okf"}
reads2 = st.scan_reads(Path.cwd())
alt = []
for h, row in zip(commits, rows):
    if row.startswith("FULL"):
        continue
    parent = h + "^"
    diff = git("diff", "--no-renames", parent, h)
    changed = {p: l for p, l in st.parse_diff(diff).items() if not p.startswith(".loop/")}
    ins = st.parse_insertions(diff)
    srcs, carried, carried_ins = {}, {}, {}
    for p, l in changed.items():
        if p.startswith("src/") and p.endswith(".py") and p in present:
            carried[p] = translate(p, l, parent)
            carried_ins[p] = translate(p, ins.get(p, set()), parent) if p in ins else set()
            srcs[p] = git("show", f"{BASE}:{p}")
        else:
            carried[p] = l
    sel = st.select(tmap, carried, present, old_sources=srcs, insertions=carried_ins, reads=reads2)
    alt.append(count(sel.targets))
if alt:
    print(f"sensitivity, .okf not a readable root: selected runs median "
          f"{statistics.median(alt):.0f}, min {min(alt)}, max {max(alt)} of {total}")
sys.exit(0 if full < len(commits) / 2 and med < 0.5 else 1)
