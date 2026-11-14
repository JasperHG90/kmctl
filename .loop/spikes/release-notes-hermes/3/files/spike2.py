"""Spike 2: does the response_file written by toiminnot actions/hermes (551e8a6) pass the
release-notes checks, with default tools (A) and with tools off (B)? And does any rewrite
reverse a bullet's meaning?

Runs the action's own runner (python -m hermes_runner) with the env vars action.yaml sets,
pointed at Bifrost: base_url=$BIFROST_URL, api_key=$BIFROST_VIRTUAL_KEY (sent as Bearer),
model=ollama/deepseek-v4.1-flash. Each run gets a fresh local clone of the repo as its cwd
(the job's checkout), a fresh HERMES_HOME and RUNNER_TEMP, and reads RUNNER_TEMP/hermes-response.txt.

Usage: spike2.py REPO TOIMINNOT_RUNNER_DIR
Exits 0 when B keeps >= 70% of rewrites and no B rewrite is flagged as a reversal.
Never prints the key: all child output is redacted before printing.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from checks import bullets, check  # noqa: E402  (spike 1's checker, unchanged)

PROMPT_FILE = HERE / "release-notes-system.md"
MODEL = "ollama/deepseek-v4.1-flash"
TAGS = ["v0.12.1", "v0.12.0", "v0.11.0", "v0.10.0", "v0.9.0"]
RUNS = 3
DISABLED = "browser,clarify,code_execution,delegation,file,memory,project,session_search,skills,terminal,todo,tts,web,vision"
CONFIGS = {
    "A": {"max_iterations": "40", "enabled_toolsets": "", "disabled_toolsets": ""},
    "B": {"max_iterations": "3", "enabled_toolsets": "", "disabled_toolsets": DISABLED},
}
REVERSAL = re.compile(r"\b(postpon\w*|defer\w*|later|planned|plan to|will|future|upcoming|not yet|pending)\b", re.I)
KEY = os.environ["BIFROST_VIRTUAL_KEY"]
URL = os.environ["BIFROST_URL"]


def redact(s: str) -> str:
    return s.replace(KEY, "[REDACTED]") if KEY else s


def run_one(repo: Path, runner: Path, cfg: str, tag: str, n: int, draft: str) -> dict:
    tmp = Path(tempfile.mkdtemp(prefix=f"hermes-{cfg}-{tag}-{n}-"))
    work, home, rt = tmp / "work", tmp / "home", tmp / "rt"
    home.mkdir()
    rt.mkdir()
    subprocess.run(["git", "clone", "-q", "--shared", str(repo), str(work)], check=True)
    (rt / "draft.md").write_text(draft)
    c = CONFIGS[cfg]
    env = {k: v for k, v in os.environ.items() if k not in ("BIFROST_VIRTUAL_KEY", "VIRTUAL_ENV")}
    env.update(
        HERMES_HOME=str(home),
        RUNNER_TEMP=str(rt),
        HERMES_RUNNER_MODEL=MODEL,
        HERMES_RUNNER_PROVIDER="ollama-cloud",
        HERMES_RUNNER_BASE_URL=URL,
        HERMES_RUNNER_API_KEY=KEY,
        HERMES_RUNNER_SYSTEM_PROMPT_FILE=str(PROMPT_FILE),
        HERMES_RUNNER_USER_MESSAGE=f"@{rt / 'draft.md'}",
        HERMES_RUNNER_MAX_ITERATIONS=c["max_iterations"],
        HERMES_RUNNER_ENABLED_TOOLSETS=c["enabled_toolsets"],
        HERMES_RUNNER_DISABLED_TOOLSETS=c["disabled_toolsets"],
        HERMES_RUNNER_OUTPUT_FILE="",
        HERMES_RUNNER_QUIET_MODE="true",
        HERMES_INFERENCE_PROVIDER="ollama-cloud",
        HERMES_MODEL=MODEL,
        OPENAI_BASE_URL=URL,
        OPENAI_API_KEY=KEY,
    )
    try:
        p = subprocess.run(
            ["uv", "run", "-q", "--project", str(runner), "python", "-m", "hermes_runner"],
            cwd=work, env=env, capture_output=True, text=True, timeout=420,
        )
        code, err = p.returncode, p.stderr
    except subprocess.TimeoutExpired:
        code, err = "timeout", ""
    resp_path = rt / "hermes-response.txt"
    # The action sets response_file only when the runner exits 0.
    resp = resp_path.read_text() if code == 0 and resp_path.exists() else ""
    tools: list[str] = []
    traj = rt / "hermes-trajectory.json"
    if traj.exists():
        for m in json.loads(traj.read_text()):
            for tc in (m.get("tool_calls") or []) if isinstance(m, dict) else []:
                f = tc.get("function", {}) if isinstance(tc, dict) else {}
                tools.append(f"{f.get('name')}({str(f.get('arguments', ''))[:80]})")
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=work, capture_output=True, text=True).stdout
    fail = check(draft, resp) if code == 0 else f"runner-exit-{code}"
    flags = []
    db, rb = bullets(draft), bullets(resp)
    for i, b in enumerate(rb):
        d = db[i] if i < len(db) else ""
        if b.rstrip() != d.rstrip() and REVERSAL.search(b):
            hits = {h.lower() for h in REVERSAL.findall(b)} - {h.lower() for h in REVERSAL.findall(d)}
            if hits:
                flags.append((d, b, sorted(hits)))
    return {
        "cfg": cfg, "tag": tag, "n": n, "code": code, "fail": fail, "resp": redact(resp),
        "err_tail": redact(err[-600:]) if code != 0 else "", "tools": [redact(t) for t in tools],
        "dirty": redact(dirty), "flags": [(redact(a), redact(b), h) for a, b, h in flags],
        "pairs": [(redact(db[i] if i < len(db) else ""), redact(b)) for i, b in enumerate(rb)],
    }


def main() -> int:
    repo, runner = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    drafts = {
        t: subprocess.run([sys.executable, str(repo / "scripts/release_notes.py"), "--repo", str(repo), t],
                          capture_output=True, text=True, check=True).stdout
        for t in TAGS
    }
    jobs = [(cfg, t, n) for cfg in CONFIGS for t in TAGS for n in range(1, RUNS + 1)]
    with ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(lambda j: run_one(repo, runner, j[0], j[1], j[2], drafts[j[1]]), jobs))
    # loopctl keeps only the last 20000 bytes of each stream, so config A goes to
    # stdout and config B to stderr, drafts once per tag, unchanged bullets as "=".
    for cfg, out in (("A", sys.stdout), ("B", sys.stderr)):
        print(f"##### CONFIG {cfg} {CONFIGS[cfg]}", file=out)
        for t in TAGS:
            print(f"=== draft {t} What changed:", file=out)
            for i, b in enumerate(bullets(drafts[t])):
                print(f"  D{i}: {b}", file=out)
            for r in (r for r in results if r["cfg"] == cfg and r["tag"] == t):
                names = [x.split("(")[0] for x in r["tools"]]
                print(f"--- {cfg} {t} run {r['n']}: exit {r['code']}, "
                      f"{'KEPT' if r['fail'] is None else 'FALLBACK ' + r['fail']}; "
                      f"tools {len(names)} {names}; checkout changed: {bool(r['dirty'])}", file=out)
                if r["err_tail"]:
                    print(f"  stderr tail: {r['err_tail']}", file=out)
                for i, (d, b) in enumerate(r["pairs"]):
                    print(f"  R{i}: " + ("=" if d.rstrip() == b.rstrip() else b), file=out)
                for d, b, h in r["flags"]:
                    print(f"  REVERSAL? {h}: {b}", file=out)
        out.flush()
    print("===== SUMMARY")
    ok = True
    for cfg, c in CONFIGS.items():
        rs = [r for r in results if r["cfg"] == cfg]
        kept = sum(r["fail"] is None for r in rs)
        flagged = sum(len(r["flags"]) for r in rs)
        tooled = sum(bool(r["tools"]) for r in rs)
        dirty = sum(bool(r["dirty"]) for r in rs)
        fails = {}
        for r in rs:
            if r["fail"]:
                fails[r["fail"]] = fails.get(r["fail"], 0) + 1
        print(f"{cfg} {c}: kept {kept}/{len(rs)}; failures {fails}; runs using tools {tooled}; "
              f"runs changing checkout {dirty}; flagged reversal bullets {flagged}")
        if cfg == "B":
            ok = kept / len(rs) >= 0.7 and flagged == 0
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
