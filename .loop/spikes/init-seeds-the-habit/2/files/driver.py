#!/usr/bin/env python3
"""Spike r7 for init-seeds-the-habit: rerun spike 1's task with the BUILT kmctl init.

One arm, N runs, each in a fresh git repo outside the kmctl checkout:
  S (built):  the worktree's `kmctl init` (rules, CLAUDE.md block, decision 0001,
              next steps), the briefing delivered by the worktree plugin's real
              SessionStart hook (`claude --plugin-dir <worktree>/plugin`), and
              init's real stdout in the prompt as what the setup printed.
Counts decisions recorded beyond init's own, architecture pages, kmctl check and
tests, and compares with spike 1 (A: 3.0 decisions, 0/3 architecture; B: 4.33, 3/3).
Exit 0 when at least 2 of N runs wrote an architecture page and the mean decisions
is at least spike 1's arm A (3.0).
"""

from __future__ import annotations

import concurrent.futures as cf
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

N = int(os.environ.get("SPIKE_N", "3"))
RUN_TIMEOUT = int(os.environ.get("SPIKE_RUN_TIMEOUT", "900"))
WORKERS = int(os.environ.get("SPIKE_WORKERS", "3"))
WORKTREE = Path("/home/vscode/kmctl.worktrees/init-seeds-the-habit")
KMCTL = WORKTREE / ".venv/bin/kmctl"
PLUGIN_DIR = WORKTREE / "plugin"
BASE = Path(os.environ.get("SPIKE_BASE") or "/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-seed-r7/runs").resolve()
SPIKE1 = {"A": (3.0, 0), "B": (4.33, 3)}

TASK = (
    "Build a small Python service for a school: a FastAPI app where a teacher creates a quiz, "
    "students submit answers, and the app scores them. Pick the storage, the scoring rules and "
    "the project layout yourself. Include tests. Work until it runs."
)

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
    init_out = sh([str(KMCTL), "init"], repo, env).stdout
    sh([str(KMCTL), "check"], repo, env)
    sh(["git", "add", "-A"], repo, env)
    sh(["git", "commit", "-q", "-m", "kmctl init"], repo, env)
    preamble = "Output of kmctl init when this repository was set up:\n\n" + init_out.strip() + "\n"
    return repo, preamble + "\n---\n\n" + TASK


def run_claude(repo: Path, prompt: str, env: dict) -> dict:
    t0 = time.time()
    cmd = [
        "claude", "-p", prompt,
        "--permission-mode", "bypassPermissions",
        "--output-format", "json",
        "--plugin-dir", str(PLUGIN_DIR),
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
    print(f"base: {BASE}  N={N}  timeout={RUN_TIMEOUT}s  workers={WORKERS}  plugin={PLUGIN_DIR}", flush=True)
    results = []
    with cf.ThreadPoolExecutor(WORKERS) as ex:
        futs = {ex.submit(one, "S", i): i for i in range(1, N + 1)}
        for f in cf.as_completed(futs):
            try:
                results.append(f.result())
            except Exception as e:  # keep the other runs
                print(f"run {futs[f]} failed: {e}", file=sys.stderr, flush=True)
    results.sort(key=lambda r: r["run"])
    (BASE / "results.json").write_text(json.dumps(results, indent=2))

    cols = ["arm", "run", "secs", "cost", "decisions", "decisions_with_rejected", "architecture_pages",
            "manifesto_purpose", "log_lines_added", "kmctl_check", "tests"]
    print("\n| " + " | ".join(cols) + " |")
    print("|" + "---|" * len(cols))
    for r in results:
        print("| " + " | ".join(str(r.get(c)) for c in cols) + " |")
    n = len(results)
    if n == 0:
        print("no completed runs")
        return 2
    mean_dec = sum(r["decisions"] for r in results) / n
    with_arch = sum(1 for r in results if r["architecture_pages"] > 0)
    print(f"\narm S, built init + real hook (n={n}): mean decisions {mean_dec:.2f}, "
          f"runs with an architecture page {with_arch}/{n}, "
          f"manifesto purpose filled {sum(r['manifesto_purpose'] for r in results)}/{n}, "
          f"kmctl check pass {sum(r['kmctl_check'] for r in results)}/{n}")
    for arm, (dec, arch) in SPIKE1.items():
        print(f"spike 1 arm {arm} (n=3): mean decisions {dec:.2f}, runs with an architecture page {arch}/3")
    ok = with_arch >= 2 and mean_dec >= SPIKE1["A"][0]
    print("built init holds spike 1's gain" if ok else "built init does not hold spike 1's gain")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
