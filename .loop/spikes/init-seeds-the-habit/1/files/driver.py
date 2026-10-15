#!/usr/bin/env python3
"""Spike for init-seeds-the-habit risk 1: does seeding get an agent to record its choices?

Two arms, N runs each, each in a fresh git repo outside the kmctl checkout:
  A (today):  kmctl init, prompt prefixed with `kmctl briefing` as session-start context.
  B (seeded): A plus four rule files, a CLAUDE.md kmctl block, decision 0001 and
              init's planned next-steps text in the prompt.
Exit 0 only when arm B's mean decisions written AND mean architecture pages both
beat arm A's (the risk does not hold).
"""

from __future__ import annotations

import concurrent.futures as cf
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

N = int(os.environ.get("SPIKE_N", "3"))
RUN_TIMEOUT = int(os.environ.get("SPIKE_RUN_TIMEOUT", "900"))
WORKERS = int(os.environ.get("SPIKE_WORKERS", "3"))
KMCTL_REPO = Path("/home/vscode/kmctl")
KMCTL = KMCTL_REPO / ".venv/bin/kmctl"
RULES = ["okf-bundle", "docs-layout", "diagrams-stay-current", "manifesto-invariants"]
BASE = Path(os.environ.get("SPIKE_BASE") or tempfile.mkdtemp(prefix="seed-spike-")).resolve()

TASK = (
    "Build a small Python service for a school: a FastAPI app where a teacher creates a quiz, "
    "students submit answers, and the app scores them. Pick the storage, the scoring rules and "
    "the project layout yourself. Include tests. Work until it runs."
)

CLAUDE_MD_BLOCK = """<!-- kmctl:start -->
## Project knowledge (kmctl)

| What you need | Where it lives |
|---|---|
| How to use the project | `docs/`, one folder per Diataxis type, each page listed in `docs/README.md` |
| What the project is for, its invariants and values | `.okf/manifesto.md` |
| Why a choice was made | `.okf/decisions/`, one record per choice with the alternative it rejected |
| The design as diagrams | `.okf/architecture/`, each page with a Depicts section naming the files it covers |
| Lessons, designs not built, spikes, handoffs | `.okf/practices/`, `.okf/proposals/`, `.okf/prototypes/`, `.okf/handoffs/` |

Start at `.okf/index.md`. The rules for writing knowledge are in `.claude/rules/`.

Your duties while you work:

1. Record each choice as a decision when you make it: `kmctl new decision 'Title' --description 'One sentence.'`, then write its Context, Decision (with the alternative you rejected) and Consequences.
2. Keep `.okf/architecture/` matching the code: add or update a page when the design changes.
3. Run `kmctl check` before you finish.
<!-- kmctl:end -->
"""

DECISION_0001_BODY = """
## Context

This repository needs a place for knowledge that people and agents working on it
can find and trust: what the project is for, why each choice was made, and how
the design fits together. Knowledge kept in someone's head or in chat is lost
when they move on, and an agent starting a session cannot read it.

## Decision

Keep project knowledge in an OKF bundle in `.okf/`, set up and checked by
kmctl, next to the code it describes. Each choice gets a decision record when it
is made, the design gets diagrams in `.okf/architecture/`, and `docs/` holds
pages for people who use the project.

## Rejected alternatives

- A wiki: it lives apart from the code, so it drifts and agents cannot read it in a session.
- README-only notes: one file mixes users' and maintainers' needs and loses the why of each choice.
- Nothing: every new session and every new person rediscovers the same reasons.

## Consequences

Each change that makes a choice also writes a decision record, and a change to
the design updates its architecture page. `kmctl check` keeps indexes and links
in step. The bundle costs a few minutes per choice and saves rereading code to
find out why.
"""

NEXT_STEPS = """kmctl init finished. Next, in order:
1. Fill .okf/manifesto.md: what this project is for and its invariants (the values are the operator's to write).
2. Once there is code, add a page to .okf/architecture/ that shows the design as a diagram, with a Depicts section naming the files it covers.
3. Record each choice as you make it with kmctl new decision 'Title' --description 'One sentence.', then write its Context, Decision (with the alternative you rejected) and Consequences.
Run kmctl check before you finish."""

REJECT_RE = re.compile(r"reject|alternative|considered|instead of|rather than", re.I)


def child_env(bindir: Path) -> dict[str, str]:
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith("CLAUDE_CODE_") and k not in {"CLAUDECODE", "CLAUDE_PID", "CLAUDE_EFFORT", "VIRTUAL_ENV"}
    }
    path = [p for p in env.get("PATH", "").split(":") if "/workspace/.venv" not in p and "/kmctl/.venv" not in p]
    env["PATH"] = ":".join([str(bindir), *path])
    for k in ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"):
        env[k] = "spike"
    for k in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"):
        env[k] = "spike@example.invalid"
    return env


def sh(args, cwd, env, timeout=120, check=True):
    p = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    if check and p.returncode != 0:
        raise RuntimeError(f"{args} failed: {p.stdout}{p.stderr}")
    return p


def snapshot(repo: Path) -> dict:
    okf = repo / ".okf"
    files = {str(p.relative_to(repo)) for p in okf.rglob("*") if p.is_file()} if okf.exists() else set()
    log = (okf / "log.md").read_text() if (okf / "log.md").exists() else ""
    return {"files": files, "log_lines": sum(1 for line in log.splitlines() if line.startswith("- "))}


def setup(arm: str, i: int, env: dict) -> tuple[Path, str]:
    repo = BASE / f"{arm}{i}"
    repo.mkdir(parents=True)
    sh(["git", "init", "-q", "."], repo, env)
    sh([str(KMCTL), "init"], repo, env)
    preamble = ""
    if arm == "B":
        rules = repo / ".claude/rules"
        rules.mkdir(parents=True)
        for r in RULES:
            shutil.copy(KMCTL_REPO / ".claude/rules" / f"{r}.md", rules / f"{r}.md")
        (repo / "CLAUDE.md").write_text(CLAUDE_MD_BLOCK)
        out = json.loads(
            sh(
                [
                    str(KMCTL), "new", "decision", "Keep project knowledge in an OKF bundle",
                    "--description", "Project knowledge lives in an OKF bundle in .okf/, next to the code, not in a wiki or README.",
                    "--json",
                ],
                repo, env,
            ).stdout
        )
        dec = repo / out["path"]
        text = dec.read_text()
        head = text.split("\n## Context", 1)[0]
        dec.write_text(head.rstrip() + "\n" + DECISION_0001_BODY)
        sh([str(KMCTL), "check"], repo, env)
    briefing = sh([str(KMCTL), "briefing"], repo, env).stdout
    sh(["git", "add", "-A"], repo, env)
    sh(["git", "commit", "-q", "-m", "kmctl init"], repo, env)
    preamble = (
        "Session-start context (printed by the kmctl plugin's SessionStart hook):\n\n" + briefing.strip() + "\n"
    )
    if arm == "B":
        preamble += "\nOutput of kmctl init when this repository was set up:\n\n" + NEXT_STEPS + "\n"
    return repo, preamble + "\n---\n\n" + TASK


def run_claude(repo: Path, prompt: str, env: dict) -> dict:
    t0 = time.time()
    cmd = [
        "claude", "-p", prompt,
        "--permission-mode", "bypassPermissions",
        "--output-format", "json",
    ]
    p = subprocess.Popen(cmd, cwd=repo, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, start_new_session=True)
    timed_out = False
    try:
        out, err = p.communicate(timeout=RUN_TIMEOUT)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(p.pid, signal.SIGKILL)
        out, err = p.communicate()
    (repo.parent / f"{repo.name}.claude.json").write_text(out or "")
    (repo.parent / f"{repo.name}.claude.err").write_text(err or "")
    info = {"exit": p.returncode, "timed_out": timed_out, "secs": round(time.time() - t0)}
    try:
        j = json.loads(out)
        info.update(cost=j.get("total_cost_usd"), turns=j.get("num_turns"), is_error=j.get("is_error"))
    except Exception:
        pass
    return info


def manifesto_purpose_filled(repo: Path) -> bool:
    m = repo / ".okf/manifesto.md"
    if not m.exists():
        return False
    sec = re.search(r"^## What this is for\s*\n(.*?)(?=^## |\Z)", m.read_text(), re.S | re.M)
    return bool(sec and sec.group(1).strip())


def run_tests(repo: Path, env: dict) -> str:
    candidates = []
    if (repo / ".venv/bin/python").exists():
        candidates.append([str(repo / ".venv/bin/python"), "-m", "pytest", "-q"])
    if (repo / "pyproject.toml").exists():
        candidates.append(["uv", "run", "--with", "pytest", "--with", "httpx", "pytest", "-q"])
    candidates.append(["uv", "run", "--no-project", "--with", "fastapi", "--with", "httpx", "--with", "pytest",
                       "--with", "sqlalchemy", "--with", "pydantic", "pytest", "-q"])
    last = "not run"
    for c in candidates:
        try:
            p = sh(c, repo, env, timeout=300, check=False)
        except subprocess.TimeoutExpired:
            continue
        tail = (p.stdout.strip().splitlines() or [""])[-1]
        if p.returncode == 0:
            return "pass: " + tail[:60]
        last = "fail: " + tail[:60]
    return last


def measure(repo: Path, before: dict, env: dict) -> dict:
    after = snapshot(repo)
    new = sorted(after["files"] - before["files"])
    decisions = [f for f in new if f.startswith(".okf/decisions/") and not f.endswith("index.md")]
    rejected = sum(1 for f in decisions if REJECT_RE.search((repo / f).read_text()))
    arch = sorted(
        f for f in after["files"] if f.startswith(".okf/architecture/") and not f.endswith("index.md")
    )
    check = sh([str(KMCTL), "check"], repo, env, check=False)
    return {
        "decisions": len(decisions),
        "decisions_with_rejected": rejected,
        "architecture_pages": len(arch),
        "manifesto_purpose": manifesto_purpose_filled(repo),
        "log_lines_added": after["log_lines"] - before["log_lines"],
        "kmctl_check": check.returncode == 0,
        "tests": run_tests(repo, env),
        "decision_files": decisions,
        "architecture_files": arch,
        "other_okf_new": [f for f in new if f not in decisions and f not in arch],
    }


def one(arm: str, i: int) -> dict:
    bindir = BASE / "bin"
    env = child_env(bindir)
    repo, prompt = setup(arm, i, env)
    before = snapshot(repo)
    info = {"dry": True} if os.environ.get("SPIKE_DRY") else run_claude(repo, prompt, env)
    (repo.parent / f"{repo.name}.prompt.txt").write_text(prompt)
    res = {"arm": arm, "run": i, **info, **measure(repo, before, env)}
    print(json.dumps(res), flush=True)
    return res


def main() -> int:
    bindir = BASE / "bin"
    bindir.mkdir(parents=True, exist_ok=True)
    if not (bindir / "kmctl").exists():
        (bindir / "kmctl").symlink_to(KMCTL)
    print(f"base: {BASE}  N={N} per arm  timeout={RUN_TIMEOUT}s  workers={WORKERS}", flush=True)
    jobs = [(arm, i) for i in range(1, N + 1) for arm in ("A", "B")]
    results = []
    with cf.ThreadPoolExecutor(WORKERS) as ex:
        futs = {ex.submit(one, a, i): (a, i) for a, i in jobs}
        for f in cf.as_completed(futs):
            try:
                results.append(f.result())
            except Exception as e:  # keep the other runs
                print(f"run {futs[f]} failed: {e}", file=sys.stderr, flush=True)
    results.sort(key=lambda r: (r["arm"], r["run"]))
    (BASE / "results.json").write_text(json.dumps(results, indent=2))

    cols = ["arm", "run", "secs", "cost", "decisions", "decisions_with_rejected", "architecture_pages",
            "manifesto_purpose", "log_lines_added", "kmctl_check", "tests"]
    print("\n| " + " | ".join(cols) + " |")
    print("|" + "---|" * len(cols))
    for r in results:
        print("| " + " | ".join(str(r.get(c)) for c in cols) + " |")

    def mean(arm, key):
        xs = [float(r[key]) for r in results if r["arm"] == arm]
        return sum(xs) / len(xs) if xs else float("nan")

    print()
    for arm in ("A", "B"):
        n = sum(1 for r in results if r["arm"] == arm)
        print(f"arm {arm} (n={n}): mean decisions {mean(arm, 'decisions'):.2f}, "
              f"mean architecture pages {mean(arm, 'architecture_pages'):.2f}, "
              f"manifesto purpose filled {sum(r['manifesto_purpose'] for r in results if r['arm'] == arm)}/{n}, "
              f"kmctl check pass {sum(r['kmctl_check'] for r in results if r['arm'] == arm)}/{n}")
    na = sum(1 for r in results if r["arm"] == "A")
    nb = sum(1 for r in results if r["arm"] == "B")
    if na == 0 or nb == 0:
        print("an arm has no completed runs")
        return 2
    holds = not (mean("B", "decisions") > mean("A", "decisions")
                 and mean("B", "architecture_pages") > mean("A", "architecture_pages"))
    print("risk holds (seeding did not raise both counts)" if holds else "risk does not hold: B beats A on both")
    return 1 if holds else 0


if __name__ == "__main__":
    sys.exit(main())
