"""Count the pages a pull request reread would check, decisions only against every page.

Usage: python scope.py REF [N]

For each of the last N pull request merges reachable from REF (subject
"Merge pull request #" or "Merge loop/"), list the files the pull request
changed (git diff FIRST_PARENT...HEAD) and, at its head, every markdown page
under .okf/ and docs/ whose front matter names one of them in `sources` (a
file by its path, a folder as a prefix). Print, per merge, the pages a
decisions-only scope (stable decisions) finds and the pages the wide scope
(every page with sources, any status but deprecated or superseded) finds, by
kind, then the totals. Exit 0 when the wide scope finds more pages, 1 when it adds none.
"""

import subprocess
import sys
from collections import Counter

import yaml

REF = sys.argv[1]
N = int(sys.argv[2]) if len(sys.argv) > 2 else 15


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True)


def front(sha: str, path: str) -> dict:
    text = git("show", f"{sha}:{path}")
    if not text.startswith("---"):
        return {}
    try:
        meta = yaml.safe_load(text.split("---", 2)[1])
    except yaml.YAMLError:
        return {}
    return meta if isinstance(meta, dict) else {}


def matches(source: str, changed: set[str]) -> bool:
    s = source.lstrip("/")
    if s.endswith("/"):
        return any(p.startswith(s) for p in changed)
    return any(p == s or p.startswith(s + "/") for p in changed)


def kind(path: str) -> str:
    if path.startswith("docs/"):
        return "docs"
    return path.split("/")[1] if path.count("/") > 1 else path.split("/")[1].removesuffix(".md")


merges = [
    line
    for line in git("log", "--merges", REF, "--format=%H %P %s").splitlines()
    if line.split(" ", 3)[3].startswith(("Merge pull request #", "Merge loop/"))
][:N]
narrow_total = 0
wide_total: Counter = Counter()
for line in merges:
    sha, fp, sp, *subj = line.split(" ")
    changed = set(git("diff", "--name-only", f"{fp}...{sp}").split())
    pages = [
        p
        for p in git("ls-tree", "-r", "--name-only", sp, ".okf", "docs").split()
        if p.endswith(".md") and not p.startswith(".okf/handoffs/")
    ]
    narrow, wide = [], Counter()
    for p in pages:
        meta = front(sp, p)
        sources = [
            str(s.get("resource", "")) for s in meta.get("sources") or [] if isinstance(s, dict)
        ]
        if not any(r and "://" not in r and matches(r, changed) for r in sources):
            continue
        status = meta.get("status")
        if status in {"deprecated", "superseded"}:
            continue
        wide[kind(p)] += 1
        if p.startswith(".okf/decisions/") and status == "stable":
            narrow.append(p)
    narrow_total += len(narrow)
    wide_total += wide
    print(f"{sha[:8]} {' '.join(subj)[:60]!r}: decisions-only {len(narrow)}, wide {sum(wide.values())} {dict(wide)}")
print(f"\ntotal over {len(merges)} merges: decisions-only {narrow_total}, wide {sum(wide_total.values())} {dict(wide_total)}")
sys.exit(0 if sum(wide_total.values()) > narrow_total else 1)
