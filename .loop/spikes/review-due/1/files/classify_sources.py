"""Classify every sources[].resource in an OKF bundle.

Usage: classify_sources.py REPO_ROOT [BUNDLE_DIR]

Rule, first match wins, but every rule is tested so overlaps show up:
  url        - has a URI scheme (scheme://)
  concept    - resolves to a .md file in the bundle: '/x' against the bundle
               root (spec 6.2), or a relative path against the concept's dir
  repo-path  - listed by `git ls-files` from the repo root
  historic   - not tracked now, but present somewhere in git history
  other      - none of the above (scope descriptor, wrong prefix, missing)

Exits 0 only when every entry matches exactly one class and none is 'other'.
"""

import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import yaml

repo = Path(sys.argv[1]).resolve()
bundle = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else repo / ".okf"


def git(*args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout


tracked = set(git("ls-files").splitlines())
historic = set(git("log", "--all", "--name-only", "--pretty=format:").splitlines()) - {""}

counts = Counter()
problems = []
total_concepts = 0
for md in sorted(bundle.rglob("*.md")):
    text = md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        continue
    try:
        fm = yaml.safe_load(text.split("---", 2)[1]) or {}
    except yaml.YAMLError as exc:
        problems.append(f"{md.relative_to(repo)}: bad frontmatter: {exc}")
        continue
    srcs = fm.get("sources") if isinstance(fm, dict) else None
    if not srcs:
        continue
    total_concepts += 1
    for entry in srcs:
        res = entry.get("resource") if isinstance(entry, dict) else entry
        res = str(res)
        hits = []
        if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", res):
            hits.append("url")
        else:
            cand = bundle / res.lstrip("/") if res.startswith("/") else md.parent / res
            if cand.resolve().is_file() and bundle in cand.resolve().parents:
                hits.append("concept")
            if res in tracked:
                hits.append("repo-path")
            elif res in historic:
                hits.append("historic")
        cls = hits[0] if len(hits) == 1 else ("other" if not hits else "ambiguous:" + "+".join(hits))
        counts[cls] += 1
        print(f"{cls:12} {md.relative_to(repo)} -> {res}")
        if cls == "other" or cls.startswith("ambiguous"):
            problems.append(f"{cls}: {md.relative_to(repo)} -> {res}")

print(f"\nconcepts with sources: {total_concepts} of {len(list(bundle.rglob('*.md')))} .md files")
print("counts:", dict(counts), "total:", sum(counts.values()))
for p in problems:
    print("UNCLASSIFIED", p)
sys.exit(1 if problems else 0)
