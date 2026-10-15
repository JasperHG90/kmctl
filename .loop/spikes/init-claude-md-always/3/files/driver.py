#!/usr/bin/env python3
"""Smoke test for init-claude-md-always: do agents record decisions with kmctl on real scaffolds.

Two arms, two scenarios (01-toml-parser, 03-job-queue-simulation), N runs each:
  NEW: kmctl built from the init-claude-md-always worktree (snapshot in scratch/new-src),
       plugin from that worktree. init adds its block to AGENTS.md and writes
       CLAUDE.md as `@AGENTS.md`, plus rules and decision 0001.
  OLD: kmctl built from a3095ed, the first parent of the merge that landed
       init-seeds-the-habit (scratch/old-src worktree), and its plugin.
Each run: fresh git repo, scenario files except OBSERVE.md and loop-gates.toml, AGENTS.md
with the loop-ticket and review-round bullets removed, committed; then `kmctl init`,
committed; then claude -p with init's stdout as the first context and the fixed prompt.
Measures in the checkout the agent worked in (the repo or a git worktree it made).
Exit 0 when NEW's mean decisions and mean architecture pages are both above OLD's.
"""

from __future__ import annotations

import concurrent.futures as cf
import glob
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

S = Path("/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/smoke-scenarios")
SCEN_ROOT = Path("/home/vscode/workspace/evals/scenarios")
SCENARIOS = ["01-toml-parser", "03-job-queue-simulation"]
N = int(os.environ.get("SPIKE_N", "2"))
RUN_TIMEOUT = int(os.environ.get("SPIKE_RUN_TIMEOUT", "1500"))
WORKERS = int(os.environ.get("SPIKE_WORKERS", "4"))
BASE = Path(os.environ.get("SPIKE_BASE") or S / "runs")
ARMS = {
    "NEW": {"bin": S / "bin-new", "plugin": Path("/home/vscode/kmctl.worktrees/init-claude-md-always/plugin")},
    "OLD": {"bin": S / "bin-old", "plugin": S / "old-src/plugin"},
}
PROMPT = "Read MANIFESTO.md and AGENTS.md, then build the first milestone of the roadmap. Work until its tests pass."
REJECT_RE = re.compile(r"reject|alternative|considered|instead of|rather than", re.I)
LOOP_BULLETS = re.compile(r"^- (Every change lands as a \*\*loop ticket\*\*.*\n(?:  .*\n)*|Every ticket passes a review round.*\n)", re.M)


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


def setup(arm: str, scen: str, i: int, env: dict) -> tuple[Path, str]:
    repo = BASE / f"{arm}-{scen[:2]}-{i}"
    repo.mkdir(parents=True)
    src = SCEN_ROOT / scen
    for p in src.rglob("*"):
        rel = p.relative_to(src)
        if rel.parts[0] in {"OBSERVE.md", "loop-gates.toml", ".ruff_cache"} or not p.is_file():
            continue
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, repo / rel)
    agents = repo / "AGENTS.md"
    text, n = LOOP_BULLETS.subn("", agents.read_text())
    if n != 2:
        raise RuntimeError(f"{scen}: expected to remove 2 loop bullets, removed {n}")
    agents.write_text(text)
    sh(["git", "init", "-q", "-b", "main", "."], repo, env)
    sh(["git", "add", "-A"], repo, env)
    sh(["git", "commit", "-q", "-m", "scenario start"], repo, env)
    init_out = sh(["kmctl", "init"], repo, env).stdout
    sh(["kmctl", "check"], repo, env)
    sh(["git", "add", "-A"], repo, env)
    sh(["git", "commit", "-q", "-m", "kmctl init"], repo, env)
    prompt = "Output of kmctl init when this repository was set up:\n\n" + init_out.strip() + "\n\n---\n\n" + PROMPT
    return repo, prompt


def run_claude(repo: Path, prompt: str, env: dict, plugin: Path) -> dict:
    t0 = time.time()
    cmd = ["claude", "-p", prompt, "--permission-mode", "bypassPermissions", "--output-format", "json",
           "--plugin-dir", str(plugin)]
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
        info.update(cost=round(j.get("total_cost_usd") or 0, 2), turns=j.get("num_turns"),
                    is_error=j.get("is_error"), session_id=j.get("session_id"),
                    result_tail=(j.get("result") or "")[-600:])
    except Exception:
        pass
    return info


def transcript_facts(session_id: str | None) -> dict:
    """What the session transcript shows: did the kmctl block reach the model, which kmctl commands ran."""
    if not session_id:
        return {"transcript": None}
    paths = glob.glob(str(Path.home() / ".claude/projects/*" / f"{session_id}.jsonl"))
    if not paths:
        return {"transcript": None}
    text = Path(paths[0]).read_text()
    cmds = []
    for line in text.splitlines():
        try:
            rec = json.loads(line)
        except Exception:
            continue
        msg = rec.get("message") or {}
        content = msg.get("content") if isinstance(msg, dict) else None
        if rec.get("type") == "assistant" and isinstance(content, list):
            for c in content:
                if c.get("type") == "tool_use" and c.get("name") == "Bash":
                    cmd = (c.get("input") or {}).get("command", "")
                    for m in re.finditer(r"\bkmctl\s+([a-z-]+(?:\s+[a-z-]+)?)", cmd):
                        cmds.append(m.group(1))
    return {
        "transcript": paths[0],
        "block_in_context": "Your duties while you work" in text,
        "briefing_in_context": "[kmctl]" in text or "knowledge briefing" in text.lower(),
        "kmctl_cmds": cmds,
    }


def section(text: str, heading: str) -> str:
    m = re.search(rf"^## {heading}\s*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.group(1).strip() if m else ""


def run_tests(repo: Path, env: dict) -> str:
    try:
        p = sh(["uv", "run", "pytest", "-q"], repo, env, timeout=600, check=False)
    except subprocess.TimeoutExpired:
        return "timeout"
    tail = ([ln for ln in p.stdout.strip().splitlines() if ln.strip()] or [""])[-1]
    return ("pass: " if p.returncode == 0 else f"fail({p.returncode}): ") + tail[:70]


def changed(d: Path, env: dict) -> int:
    out = sh(["git", "status", "--porcelain", "--untracked-files=all"], d, env, check=False).stdout
    return sum(1 for ln in out.splitlines() if not re.search(r"\.loop/|uv\.lock|__pycache__|\.claude/worktrees", ln))


def workdir(repo: Path, env: dict) -> Path:
    """The checkout the agent worked in: the repo or one of its git worktrees, whichever changed most (a worktree wins a tie)."""
    out = sh(["git", "worktree", "list", "--porcelain"], repo, env, check=False).stdout
    dirs = [Path(ln[len("worktree "):]) for ln in out.splitlines() if ln.startswith("worktree ")] or [repo]
    return max(dirs, key=lambda d: (changed(d, env) if d.exists() else -1, d != repo))


def measure(repo: Path, before: dict, env: dict) -> dict:
    wts = sh(["git", "worktree", "list", "--porcelain"], repo, env, check=False).stdout.count("worktree ")
    main_repo, repo = repo, workdir(repo, env)
    after = snapshot(repo)
    new = sorted(after["files"] - before["files"])
    decisions = [f for f in new if f.startswith(".okf/decisions/") and not f.endswith("index.md")]
    rejected = sum(1 for f in decisions if REJECT_RE.search((repo / f).read_text()))
    arch = sorted(f for f in after["files"] if f.startswith(".okf/architecture/") and not f.endswith("index.md"))
    m = repo / ".okf/manifesto.md"
    mt = m.read_text() if m.exists() else ""
    root_changed = sh(["git", "diff", "--quiet", "HEAD", "--", "MANIFESTO.md"], repo, env, check=False).returncode != 0
    check = sh(["kmctl", "check"], repo, env, check=False)
    if mt:
        shutil.copy2(m, main_repo.parent / f"{main_repo.name}.okf-manifesto.md")
    return {
        "workdir": "repo" if repo == main_repo else str(repo),
        "decisions": len(decisions),
        "decisions_with_rejected": rejected,
        "architecture_pages": len(arch),
        "okf_purpose": bool(section(mt, "What this is for")),
        "okf_invariants": bool(section(mt, "Invariants")),
        "okf_manifesto_words": len(mt.split()),
        "okf_manifesto_cites_root": "MANIFESTO.md" in mt,
        "root_manifesto_changed": root_changed,
        "log_lines_added": after["log_lines"] - before["log_lines"],
        "kmctl_check": check.returncode == 0,
        "kmctl_check_out": (check.stdout + check.stderr).strip()[-300:],
        "tests": run_tests(repo, env),
        "worktrees": wts,
        "decision_files": decisions,
        "architecture_files": arch,
        "other_okf_new": [f for f in new if f not in decisions and f not in arch],
    }


def one(arm: str, scen: str, i: int) -> dict:
    env = child_env(ARMS[arm]["bin"])
    repo, prompt = setup(arm, scen, i, env)
    (repo.parent / f"{repo.name}.prompt.txt").write_text(prompt)
    before = snapshot(repo)
    info = {"dry": True} if os.environ.get("SPIKE_DRY") else run_claude(repo, prompt, env, ARMS[arm]["plugin"])
    res = {"arm": arm, "scenario": scen, "run": i, **info, **transcript_facts(info.get("session_id")),
           **measure(repo, before, env)}
    print(json.dumps(res), flush=True)
    return res


def main() -> int:
    if BASE.exists():
        print(f"{BASE} exists; remove it or set SPIKE_BASE", file=sys.stderr)
        return 2
    BASE.mkdir(parents=True)
    for arm, a in ARMS.items():
        v = sh(["kmctl", "--version"], S, child_env(a["bin"])).stdout.strip()
        print(f"{arm}: {v} via {a['bin']}, plugin {a['plugin']}", flush=True)
    print(f"base: {BASE}  N={N}  timeout={RUN_TIMEOUT}s  workers={WORKERS}", flush=True)
    jobs = [(arm, scen, i) for i in range(1, N + 1) for scen in SCENARIOS for arm in ARMS]
    results = []
    with cf.ThreadPoolExecutor(WORKERS) as ex:
        futs = {ex.submit(one, *j): j for j in jobs}
        for f in cf.as_completed(futs):
            try:
                results.append(f.result())
            except Exception as e:  # keep the other runs
                print(f"run {futs[f]} failed: {e}", file=sys.stderr, flush=True)
    results.sort(key=lambda r: (r["arm"], r["scenario"], r["run"]))
    (BASE / "results.json").write_text(json.dumps(results, indent=2))

    cols = ["arm", "scenario", "run", "secs", "cost", "timed_out", "decisions", "decisions_with_rejected",
            "architecture_pages", "okf_purpose", "okf_invariants", "okf_manifesto_cites_root",
            "root_manifesto_changed", "log_lines_added", "kmctl_check", "tests", "block_in_context", "workdir"]
    print("\n| " + " | ".join(cols) + " |")
    print("|" + "---|" * len(cols))
    for r in results:
        print("| " + " | ".join(str(r.get(c)) for c in cols) + " |")
    means = {}
    for arm in ARMS:
        rs = [r for r in results if r["arm"] == arm]
        if not rs:
            print(f"{arm}: no completed runs")
            return 2
        means[arm] = (sum(r["decisions"] for r in rs) / len(rs), sum(r["architecture_pages"] for r in rs) / len(rs))
        print(f"{arm} (n={len(rs)}): mean decisions {means[arm][0]:.2f}, mean architecture pages {means[arm][1]:.2f}, "
              f"cost {sum(r.get('cost') or 0 for r in rs):.2f}")
    ok = means["NEW"][0] > means["OLD"][0] and means["NEW"][1] > means["OLD"][1]
    print("NEW above OLD on both" if ok else "NEW not above OLD on both")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
