"""Compare `kmctl review due --base` with a plain sources matcher over real merged PRs.

For each of the last N first-parent merges on main: check out the second
parent (the PR head) in a throwaway worktree, run the current kmctl's
`review due --base FIRST_PARENT --json --path WT`, and separately list the
stable decisions at the PR head whose `sources` (a file, or a folder as a
prefix) match a file in `git diff FP...HEAD --name-only`. Report what the
matcher finds that review due --base leaves out, and why.

Exit 0 only when review due --base lists every matcher hit (the risk does
not hold); exit 1 otherwise.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

N = int(sys.argv[1]) if len(sys.argv) > 1 else 15
REPO = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
KMCTL = [str(Path(sys.executable).with_name("kmctl"))]


def git(*args, cwd=REPO):
    return subprocess.check_output(["git", "-C", str(cwd), *args], text=True)


def front(path: Path):
    text = path.read_text()
    if not text.startswith("---"):
        return {}
    return yaml.safe_load(text.split("---", 2)[1]) or {}


def matches(source: str, changed: set[str]) -> list[str]:
    s = source.lstrip("/")
    if s.endswith("/"):
        return sorted(p for p in changed if p.startswith(s))
    return sorted(p for p in changed if p == s or p.startswith(s + "/"))


merges = git("log", "--merges", "--first-parent", "main", f"-{N}", "--format=%H %P %s").splitlines()
tmp = Path(tempfile.mkdtemp(prefix="pr-scope-"))
tot_hits = tot_cov = tot_src = 0
folder_seen = unverified_seen = False
misses_all = []
for i, line in enumerate(merges):
    sha, fp, sp, *subj = line.split(" ")
    subj = " ".join(subj)
    wt = tmp / f"wt{i}"
    git("worktree", "add", "--detach", "-q", str(wt), sp)
    try:
        changed = set(git("diff", "--name-only", f"{fp}...{sp}").split())
        out = subprocess.run(
            [*KMCTL, "review", "due", "--path", str(wt), "--base", fp, "--json"],
            capture_output=True, text=True,
        )
        if out.returncode != 0:
            print(f"{sha[:8]} review due exit {out.returncode}: {out.stderr.strip()[:300]}")
            continue
        due = {d["id"]: d["reasons"] for d in json.loads(out.stdout)["due"]}
        hits = {}
        for p in sorted((wt / ".okf/decisions").glob("*.md")):
            if p.name in {"index.md", "log.md"}:
                continue
            meta = front(p)
            if meta.get("status") != "stable":
                continue
            cid = "decisions/" + p.stem
            for s in meta.get("sources") or []:
                r = (s or {}).get("resource", "")
                if "://" in r:
                    continue
                m = matches(r, changed)
                if m:
                    hits.setdefault(cid, []).append((r, m, bool(meta.get("verified")), f".okf/decisions/{p.name}" in changed))
        print(f"\n== {sha[:8]} {subj[:70]}  ({len(changed)} files changed)")
        print(f"   review due --base decisions: {sorted(k for k in due if k.startswith('decisions/'))}")
        print(f"   matcher decisions:           {sorted(hits)}")
        for cid, srcs in hits.items():
            tot_hits += 1
            verified = srcs[0][2]
            edited = srcs[0][3]
            folder = any(r.endswith("/") for r, *_ in srcs)
            if cid in due:
                tot_cov += 1
                by_src = any(r.startswith("source changed: ") for r in due[cid])
                tot_src += by_src
                if by_src:
                    folder_seen |= folder
                    unverified_seen |= not verified
                else:
                    print(f"   LISTED, but not for its sources: {cid} reasons={due[cid]}")
                continue
            if not verified:
                why = "no verified entry (sources never compared; 'unverified' kept only when the record itself changed)"
            elif edited:
                why = "record edited/verified in this PR (verified after the change)"
            else:
                why = "verified, source changed, but not due: verification commit at or after the change"
            kind = "folder" if folder else "file"
            misses_all.append((sha[:8], cid, kind, why))
            print(f"   MISS {cid} [{kind} source: {', '.join(r for r, *_ in srcs)}] -> {why}")
    finally:
        git("worktree", "remove", "--force", str(wt))

print("\n== totals")
print(f"PRs: {len(merges)}; matcher hits: {tot_hits}; listed by review due --base: {tot_cov}; missed: {tot_hits - tot_cov}; listed with a 'source changed' reason: {tot_src}")
reasons = {}
for _, cid, kind, why in misses_all:
    reasons.setdefault((kind, why), set()).add(cid)
for (kind, why), ids in reasons.items():
    print(f"  {kind} | {why}: {len([m for m in misses_all if (m[2], m[3]) == (kind, why)])} hits, {sorted(ids)}")
print(f"folder-source decision ever listed by --base for a source change: {folder_seen}")
print(f"decision with no verified entry ever listed by --base for a source change: {unverified_seen}")
sys.exit(0 if tot_hits == tot_cov else 1)
