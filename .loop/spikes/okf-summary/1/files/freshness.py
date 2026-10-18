#!/usr/bin/env python3
"""Spike: does the commit-order freshness rule for .okf/summary.md hold?"""

import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REAL = "/home/vscode/kmctl"
SUMMARY = ".okf/summary.md"
CONCEPT = re.compile(
    r"^\.okf/(manifesto\.md|(decisions|practices|proposals|architecture)/[^/]+\.md"
    r"|prototypes/[^/]+/README\.md)$"
)


def is_concept(p):
    return bool(CONCEPT.match(p)) and not p.endswith("/index.md")


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", repo, *args], check=True, capture_output=True, text=True
    ).stdout


def stale(repo):
    """Concepts changed since the summary, by commit order and working tree."""
    base = git(repo, "log", "-1", "--format=%H", "--", SUMMARY).strip()
    changed = set()
    if base:
        changed |= set(git(repo, "diff", "--name-only", f"{base}..HEAD", "--", ".okf").split())
    else:
        changed |= set(git(repo, "ls-files", "--", ".okf").split())
    wt = set()
    for line in git(repo, "status", "--porcelain", "--untracked-files=all", "--", ".okf").splitlines():
        wt.add(line[3:].split(" -> ")[-1])
    if SUMMARY in wt:
        # an uncommitted summary edit covers everything up to now
        return []
    changed |= wt
    return sorted(p for p in changed if is_concept(p))


failures = []


def check(name, got, want):
    ok = got == want
    print(f"{'PASS' if ok else 'FAIL'} {name}: got {got} want {want}")
    if not ok:
        failures.append(name)


def write(repo, rel, text, append=False):
    p = Path(repo, rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a" if append else "w") as f:
        f.write(text)


def commit(repo, msg):
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", msg)


def fresh_repo():
    d = tempfile.mkdtemp()
    git(d, "init", "-q")
    git(d, "config", "user.email", "s@x")
    git(d, "config", "user.name", "s")
    write(d, ".okf/index.md", "# index\n")
    write(d, ".okf/log.md", "# log\n")
    write(d, ".okf/manifesto.md", "---\ntype: manifesto\n---\nm\n")
    write(d, ".okf/decisions/index.md", "# d\n")
    write(d, ".okf/decisions/0001-a.md", "---\ntype: decision\n---\na\n")
    write(d, SUMMARY, "---\ntype: summary\n---\ns\n")
    commit(d, "init")
    return d


D1 = ".okf/decisions/0002-b.md"

# a) summary committed, then a decision added and committed
r = fresh_repo()
write(r, D1, "---\ntype: decision\n---\nb\n")
write(r, ".okf/log.md", "- Added b\n", append=True)
commit(r, "add decision")
check("a decision after summary", stale(r), [D1])

# b) decision and summary in the same commit
r = fresh_repo()
write(r, D1, "---\ntype: decision\n---\nb\n")
write(r, SUMMARY, "more\n", append=True)
commit(r, "decision + summary")
check("b same commit", stale(r), [])

# b2) summary updated in a later commit of the same session
r = fresh_repo()
write(r, D1, "---\ntype: decision\n---\nb\n")
commit(r, "decision")
write(r, SUMMARY, "more\n", append=True)
commit(r, "summary")
check("b2 summary in later commit", stale(r), [])

# c) uncommitted decision edit, then uncommitted summary edit
r = fresh_repo()
write(r, ".okf/decisions/0001-a.md", "edit\n", append=True)
write(r, D1, "untracked new\n")
check("c1 uncommitted decision", stale(r), [".okf/decisions/0001-a.md", D1])
write(r, SUMMARY, "more\n", append=True)
check("c2 uncommitted summary too", stale(r), [])

# d) kmctl verify-style edit: front matter verified line + log.md
r = fresh_repo()
write(r, ".okf/decisions/0001-a.md",
      "---\ntype: decision\nverified:\n  - by: human:x\n    at: 2026-10-18\n---\na\n")
write(r, ".okf/log.md", "- Verified `decisions/0001-a` (human:x).\n", append=True)
commit(r, "verify")
check("d verify stamp after summary (expected nudge)", stale(r), [".okf/decisions/0001-a.md"])
# d2) verify stamp written earlier, then summary updated after: covered
write(r, SUMMARY, "more\n", append=True)
commit(r, "summary")
check("d2 verify then summary", stale(r), [])
# d3) verify stamp uncommitted
write(r, ".okf/manifesto.md", "verified: []\n", append=True)
write(r, ".okf/log.md", "- Verified manifesto\n", append=True)
check("d3 uncommitted verify", stale(r), [".okf/manifesto.md"])

# e) only log.md, an index.md, a handoff
r = fresh_repo()
write(r, ".okf/log.md", "x\n", append=True)
write(r, ".okf/decisions/index.md", "x\n", append=True)
write(r, ".okf/handoffs/2026-10-18-h.md", "h\n")
commit(r, "non-concepts")
write(r, ".okf/index.md", "y\n", append=True)
check("e non-concepts only", stale(r), [])

# f) summary ack (checked: DATE) committed after the decision
r = fresh_repo()
write(r, D1, "---\ntype: decision\n---\nb\n")
commit(r, "decision")
write(r, SUMMARY, "---\ntype: summary\nchecked: 2026-10-18\n---\ns\n")
commit(r, "ack")
check("f ack after decision", stale(r), [])

# g) speed on the real repository (read-only)
times = []
for _ in range(5):
    t = time.perf_counter()
    res = stale(REAL)
    times.append((time.perf_counter() - t) * 1000)
base = git(REAL, "log", "-1", "--format=%H", "--", SUMMARY).strip()
print(f"g real repo: baseline={'none' if not base else base}; "
      f"concepts flagged={len(res)}; ms min={min(times):.1f} max={max(times):.1f}")
# with a baseline: time the diff against the first commit (worst case)
first = git(REAL, "rev-list", "--max-parents=0", "HEAD").split()[0]
t = time.perf_counter()
n = len(git(REAL, "diff", "--name-only", f"{first}..HEAD", "--", ".okf").split())
print(f"g diff root..HEAD -- .okf: {n} files in {(time.perf_counter() - t) * 1000:.1f} ms")
if max(times) > 1000:
    failures.append("g too slow")

# h) real history: commits that change concepts
log = git(REAL, "log", "--format=@%H %s", "--name-only", "--", ".okf")
commits = []
for block in log.split("@")[1:]:
    head, *files = block.strip().splitlines()
    sha, _, subj = head.partition(" ")
    commits.append((sha, subj, [f for f in files if f]))
cc = [(s, m, [f for f in fs if is_concept(f)]) for s, m, fs in commits]
cc = [c for c in cc if c[2] and not c[1].startswith("loop:")]
multi = [c for c in cc if len(c[2]) > 1]
fm_only = []
for sha, subj, files in cc:
    for f in files:
        try:
            diff = git(REAL, "show", "--format=", "-U0", sha, "--", f)
        except subprocess.CalledProcessError:
            continue
        if "new file mode" in diff:
            continue
        old = git(REAL, "show", f"{sha}^:{f}") if sha else ""
        try:
            new = git(REAL, "show", f"{sha}:{f}")
        except subprocess.CalledProcessError:
            continue  # deleted
        body = lambda t: t.split("\n---\n", 1)[1] if t.startswith("---\n") and "\n---\n" in t else t
        if body(old) == body(new) and old != new:
            fm_only.append((sha[:8], subj, f))
print(f"h real history: {len(cc)} concept-changing non-loop commits, "
      f"{len(multi)} change >1 concept, {len(fm_only)} front-matter-only concept edits")
for x in fm_only:
    print("  fm-only:", *x)

sys.exit(1 if failures else 0)
