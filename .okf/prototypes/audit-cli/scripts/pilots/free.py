"""The pilots that cost nothing or next to nothing, each measured on all stored claims.

Run from the audit-cli folder, with the shell's keys loaded:

    uv run python scripts/pilots/free.py dedup [MODEL]|skip|changed|survival|batch

- dedup: claims in different sections that state the same fact. Candidate pairs by text and shared named things,
  then a decision model (Clef by default, or jev-latest) is asked whether checking one settles the other.
- skip: claims no code can settle, by the extractor's kind; what leaving them out at extraction would save.
- changed: over the last commits that touched code, how many claims a commit would send back for a check, if only
  claims whose located files changed are checked again.
- survival: the saved checks run at older commits; which flip, to see whether a kept check tracks real change.
- batch: whether Bifrost offers a batch endpoint (half-price answers that can wait).

Each writes results/pilots/<name>.json and prints a summary.
"""

import asyncio
import difflib
import json
import subprocess
import sys
from collections import Counter
from itertools import combinations
from typing import Any

import httpx
from pydantic import TypeAdapter

from audit_cli.checks.steps import Repository, Step, run_check

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from pilots import common  # the scripts folder is not a package on the path

STEPS = TypeAdapter(list[Step])
SAME_FACT = {
    "same_fact": {
        "type": "noul",
        "instructions": "Do claim A and claim B state the same fact about the repository, so that checking one "
        "settles the other? Two claims about the same file or command that say different things about it are not "
        "the same fact.",
    }
}


def save(name: str, data: dict[str, Any]) -> None:
    """Write one pilot's results and print them."""
    common.OUT.mkdir(parents=True, exist_ok=True)
    (common.OUT / f"{name}.json").write_text(json.dumps(data, indent=1, default=str))
    print(
        json.dumps(
            {k: v for k, v in data.items() if k not in {"pairs", "per_commit", "flips_detail"}}, indent=1, default=str
        )
    )


def git(*args: str, root: Any = common.REPO) -> str:
    """Return a git command's output."""
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True).stdout


async def dedup(model: str) -> None:
    """Find claims in different sections that state one fact, and how many checks sharing a verdict would save."""
    claims = common.claims()
    names = {c.claim_id: {a["text"] for a in c.anchors} for c in claims}
    candidates = []
    for a, b in combinations(claims, 2):
        if a.chunk_id == b.chunk_id:
            continue
        ratio = difflib.SequenceMatcher(a=a.text.lower(), b=b.text.lower()).ratio()
        shared = names[a.claim_id] & names[b.claim_id]
        if ratio >= 0.6 or (shared and ratio >= 0.4):
            candidates.append((a, b, round(ratio, 2)))
    pairs = []
    async with httpx.AsyncClient(timeout=120) as client:
        limit = asyncio.Semaphore(4)

        async def ask(a: common.StoredClaim, b: common.StoredClaim, ratio: float) -> None:
            """Ask the decision model whether one pair states the same fact."""
            async with limit:
                answer = await common.decide(client, model, {"claim A": a.text, "claim B": b.text}, SAME_FACT)
            pairs.append({"a": a.text, "b": b.text, "ratio": ratio, "same": answer["same_fact"]})

        if model == common.JEV:
            ledger = common.Ledger()
            ledger.check(jev_calls=len(candidates))
        await asyncio.gather(*(ask(*c) for c in candidates))
        if model == common.JEV:
            ledger.add("dedup", jev_calls=len(candidates))
    same = [p for p in pairs if p["same"] > 0.5]
    groups: dict[str, set[str]] = {}
    for p in same:  # join pairs into groups of one fact
        group = groups.get(p["a"], set()) | groups.get(p["b"], set()) | {p["a"], p["b"]}
        for text in group:
            groups[text] = group
    unique_groups = {frozenset(g) for g in groups.values()}
    saved = sum(len(g) - 1 for g in unique_groups)
    save(
        f"dedup-{common.slug(model)}",
        {
            "model": model,
            "claims": len(claims),
            "candidate_pairs": len(candidates),
            "same_fact_pairs": len(same),
            "checks_saved": saved,
            "share_saved": round(saved / len(claims), 3),
            "pairs": sorted(pairs, key=lambda p: -p["same"]),
        },
    )


def skip() -> None:
    """Count the claims whose kind says no code settles them: what leaving them out at extraction saves."""
    claims = common.claims()
    kinds = Counter(c.kind for c in claims)
    not_code = {k: n for k, n in kinds.items() if k in {"external", "subjective", "broad"}}
    save(
        "skip",
        {
            "claims": len(claims),
            "by_kind": dict(kinds),
            "not_code_by_kind": not_code,
            "share_skipped": round(sum(not_code.values()) / len(claims), 3),
            "note": "history and intent are not a kind yet; the router pilot asks for them",
        },
    )


def command_files(command: str) -> list[str]:
    """Return the source files that name a command's last word in quotes: where a CLI verb is registered."""
    words = command.split()
    if words[0].endswith(".py"):
        return [words[0]]
    verb = words[-1]
    hits = git("grep", "-l", "-F", f'"{verb}"', "--", "src/*.py").split()
    return hits or []


def claim_files(claim: common.StoredClaim) -> set[str]:
    """Return the files whose change sends a claim back: located files, and the files of the commands it names."""
    files = set(common.located_files(claim))
    for anchor in claim.anchors:
        if anchor["kind"] in {"command", "flag"}:
            for where in anchor["where"]:
                files |= set(command_files(where))
    return {f for f in files if not f.endswith(".md") and not f.startswith(common.LEFT_OUT)}


def changed(commits: int = 60) -> None:
    """Over recent commits that touched code, count the claims each would send back for a check."""
    claims = common.claims()
    tied = {c.claim_id: claim_files(c) for c in claims}
    untied = [c for c in claims if not tied[c.claim_id]]
    log = git("log", "--no-merges", f"-n{commits}", "--format=%H", "--", ".", ":!.okf", ":!.loop", ":!*.md").split()
    per_commit: list[dict[str, Any]] = []
    ever: set[str] = set()
    for sha in log:
        files = set(git("show", "--name-only", "--format=", sha).split())
        hit = [cid for cid, fs in tied.items() if fs & files]
        ever |= set(hit)
        per_commit.append({"commit": sha[:10], "files": len(files), "claims": len(hit)})
    counts: list[int] = sorted(int(p["claims"]) for p in per_commit)
    tied_n = len(claims) - len(untied)
    save(
        "changed",
        {
            "claims": len(claims),
            "tied_to_files": tied_n,
            "untied": len(untied),
            "commits": len(log),
            "claims_per_commit_median": counts[len(counts) // 2],
            "claims_per_commit_mean": round(sum(counts) / len(counts), 1),
            "claims_per_commit_max": counts[-1],
            "commits_touching_no_claim": sum(c == 0 for c in counts),
            "share_of_tied_rechecked_per_commit_mean": round(sum(counts) / len(counts) / tied_n, 3),
            "claims_rechecked_over_window": len(ever),
            "per_commit": per_commit,
        },
    )


def survival(offsets: tuple[int, ...] = (5, 150, 600, 1000, 1500)) -> None:
    """Run the saved checks at older commits and list which flip from what they give now."""
    saved = json.loads((common.HERE / "results" / "checks" / "checks.json").read_text())
    checks = {cid: STEPS.validate_python(e["check"]["steps"]) for cid, e in saved.items() if "check" in e}
    now = {cid: run_check(Repository(common.REPO), steps)[0] for cid, steps in checks.items()}
    shas = git("log", "--format=%H", "-n", str(max(offsets) + 1)).split()
    scratch = common.HERE / "results" / "pilots" / "worktrees"
    rows, details = [], []
    for offset in offsets:
        sha = shas[offset]
        tree = scratch / sha[:10]
        if not tree.exists():
            git("worktree", "add", "--detach", str(tree), sha)
        try:
            then = {cid: run_check(Repository(tree), steps)[0] for cid, steps in checks.items()}
        finally:
            git("worktree", "remove", "--force", str(tree))
        flips = [cid for cid in checks if then[cid] != now[cid]]
        date = git("show", "-s", "--format=%cs", sha).strip()
        rows.append({"commits_back": offset, "date": date, "flipped": len(flips), "of": len(checks)})
        details += [
            {"commits_back": offset, "claim": saved[cid]["claim"], "now": now[cid], "then": then[cid]} for cid in flips
        ]
    save("survival", {"checks": len(checks), "by_offset": rows, "flips_detail": details})


async def batch() -> None:
    """Ask Bifrost whether it serves the OpenAI batch and files endpoints."""
    key = __import__("os").environ["BIFROST_CC_VIRTUAL_KEY"]
    found = {}
    async with httpx.AsyncClient(timeout=30) as client:
        for path in ("batches", "files"):
            response = await client.get(f"{common.BIFROST}/{path}", headers={"Authorization": f"Bearer {key}"})
            found[path] = {"status": response.status_code, "body": response.text[:300]}
    save("batch", found)


def main() -> None:
    """Run the named pilot."""
    common.settings()
    name = sys.argv[1]
    if name == "dedup":
        asyncio.run(dedup(sys.argv[2] if len(sys.argv) > 2 else common.CLEF))
    elif name == "skip":
        skip()
    elif name == "changed":
        changed()
    elif name == "survival":
        survival()
    elif name == "batch":
        asyncio.run(batch())
    else:
        raise SystemExit(f"unknown pilot {name!r}")


if __name__ == "__main__":
    main()
