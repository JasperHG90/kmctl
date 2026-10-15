"""Run one hermes -z call against fake_llm.py in a fresh HOME and work dir.

Usage: drive.py OUTDIR [--config] [--plugin] [--safe-root] -- HERMES_ARGS...
Prints a JSON summary of what happened. Library for the spike checks.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
HERMES = HERE / "bin" / "hermes"
PROMPT = "Audit this repo. Reply with a fenced json findings block."


def run(hermes_args, *, config=None, plugin=False, extra_env=None, timeout=120,
        prompt=PROMPT):
    root = Path(tempfile.mkdtemp(prefix="hrun-", dir=HERE))
    home, work = root / "home", root / "work"
    home.mkdir()
    work.mkdir()
    (work / "fixture.txt").write_text("hello from fixture\n")
    (work / "AGENTS.md").write_text("MARKER_AGENTS_MD: always say banana\n")
    (work / "CLAUDE.md").write_text("MARKER_CLAUDE_MD\n")
    (work / ".cursorrules").write_text("MARKER_CURSORRULES\n")
    target = work / "target.txt"
    target.write_text("original\n")
    log, portf = root / "requests.jsonl", root / "port"
    srv = subprocess.Popen([sys.executable, "-I", str(HERE / "fake_llm.py"),
                            str(portf), str(log), str(target)])
    for _ in range(100):
        if portf.exists() and portf.read_text():
            break
        time.sleep(0.05)
    port = portf.read_text()
    base = f"http://127.0.0.1:{port}/v1"
    if config is not None:
        hh = home / ".hermes"
        hh.mkdir()
        (hh / "config.yaml").write_text(config.replace("@BASE@", base))
    if plugin:
        pd = home / ".hermes" / "plugins" / "kmctl-read"
        pd.mkdir(parents=True)
        shutil.copy(HERE / "plugin" / "plugin.yaml", pd / "plugin.yaml")
        shutil.copy(HERE / "plugin" / "__init__.py", pd / "__init__.py")
    # Child env built from scratch: no inherited keys, no real HOME.
    env = {
        "PATH": f"{HERE / 'bin'}:/usr/local/bin:/usr/bin:/bin",
        "HOME": str(home),
        "LANG": "C.UTF-8",
        "TERM": "dumb",
        "FAKE_API_KEY": "sk-fake-123",
    }
    for k, v in (extra_env or {}).items():
        env[k] = v.replace("@BASE@", base).replace("@WORK@", str(work)).replace(
            "@ROOT@", str(root))
    args = [a.replace("@BASE@", base) for a in hermes_args]
    t0 = time.time()
    try:
        p = subprocess.run([str(HERMES), *args, "-z", prompt], cwd=work, env=env,
                           stdin=subprocess.DEVNULL, capture_output=True,
                           text=True, timeout=timeout)
        rc, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        rc, out, err = "timeout", e.stdout or "", e.stderr or ""
        out = out if isinstance(out, str) else out.decode()
        err = err if isinstance(err, str) else err.decode()
    secs = round(time.time() - t0, 1)
    srv.terminate()
    reqs = [json.loads(l) for l in log.read_text().splitlines()] if log.exists() else []
    chats = [r for r in reqs if r["method"] == "POST" and r.get("body", {}).get("tools")]
    offered = sorted({t["function"]["name"] for r in chats for t in r["body"]["tools"]})
    tool_results = []
    sys_prompt = ""
    if chats:
        msgs = chats[-1]["body"].get("messages", [])
        tool_results = [m.get("content") for m in msgs if m.get("role") == "tool"]
        sys_prompt = "\n".join(str(m.get("content")) for m in msgs
                               if m.get("role") == "system")
    created = sorted(str(p.relative_to(work)) for p in work.rglob("*")
                     if p.name not in {"fixture.txt", "AGENTS.md", "CLAUDE.md",
                                        ".cursorrules", "target.txt"})
    return {
        "root": str(root),
        "rc": rc,
        "secs": secs,
        "stdout": out,
        "stderr_tail": err[-2000:],
        "requests": [(r["method"], r["path"]) for r in reqs],
        "auth": sorted({str(r.get("auth")) for r in reqs if r["method"] == "POST"}),
        "models": sorted({r["body"].get("model") for r in chats}),
        "stream": sorted({bool(r["body"].get("stream")) for r in chats}),
        "offered_tools": offered,
        "tool_results": [str(t)[:400] for t in tool_results],
        "target_after": target.read_text(),
        "new_files_in_work": created,
        "sys_has_agents_md": "MARKER_AGENTS_MD" in sys_prompt,
        "sys_has_claude_md": "MARKER_CLAUDE_MD" in sys_prompt,
        "sys_has_cursorrules": "MARKER_CURSORRULES" in sys_prompt,
        "sys_prompt_len": len(sys_prompt),
    }


if __name__ == "__main__":
    spec = json.loads(sys.argv[1])
    print(json.dumps(run(**spec), indent=1))
