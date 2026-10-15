"""Spike for ci-audit risk 1 / eval r7: headless claude -p with --plugin-dir and
read-only tools. Exits 0 only when Bash and Write/NotebookEdit are refused, the
plugin's kmctl-auditor agent loads, and a dispatch returns a parseable findings block."""
import json, os, re, shutil, subprocess, sys
from pathlib import Path

SCRATCH = Path(__file__).resolve().parent / "run"
PLUGIN = "/home/vscode/kmctl.worktrees/audit-agent-and-skills/plugin"
shutil.rmtree(SCRATCH, ignore_errors=True)
FIX = SCRATCH / "fixture"
(FIX / "src").mkdir(parents=True)
(FIX / ".okf/architecture").mkdir(parents=True)
(FIX / "src/greet.py").write_text('def greet(name):\n    return f"Hi, {name}!"\n')
(FIX / ".okf/architecture/overview.md").write_text(
    "---\ntype: architecture\ntitle: Overview\n---\n\n# Overview\n\n"
    "`src/greet.py` defines `greet(name)`, which returns `\"Hello, NAME\"`.\n")

env = {k: v for k, v in os.environ.items()
       if not (k.startswith("CLAUDE_CODE_") or k in ("CLAUDECODE", "CLAUDE_PID", "CLAUDE_EFFORT"))}
BASE = ["claude", "-p", "--plugin-dir", PLUGIN, "--setting-sources", "project",
        "--disallowedTools", "Bash,Edit,Write", "--output-format", "stream-json", "--verbose"]

def run(label, allowed, prompt):
    cmd = BASE + ["--allowedTools", allowed]  # prompt on stdin: --allowedTools is variadic and swallows a trailing prompt
    print(f"\n===== {label}\n$ {' '.join(cmd)} < prompt\nprompt: {prompt[:300]}")
    try:
        p = subprocess.run(cmd, cwd=FIX, env=env, input=prompt, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        print("TIMEOUT"); return None, []
    events = [json.loads(l) for l in p.stdout.splitlines() if l.startswith("{")]
    (SCRATCH / f"{label}.jsonl").write_text(p.stdout)
    print(f"exit {p.returncode}; stderr: {p.stderr.strip()[:300]}")
    for e in events:
        if e.get("type") == "system" and e.get("subtype") == "init":
            print("init tools:", e.get("tools"))
            print("init agents:", e.get("agents"))
            print("init plugins:", e.get("plugins"))
            print("init skills:", e.get("skills"))
        if e.get("type") == "assistant":
            for c in e["message"].get("content", []):
                if c.get("type") == "tool_use":
                    print("tool_use:", c["name"], json.dumps(c["input"])[:200])
        if e.get("type") == "user":
            for c in e["message"].get("content", []) if isinstance(e["message"].get("content"), list) else []:
                if c.get("type") == "tool_result" and c.get("is_error"):
                    print("tool_error:", str(c.get("content"))[:200])
    res = next((e for e in events if e.get("type") == "result"), {})
    print("permission_denials:", json.dumps(res.get("permission_denials"))[:400])
    text = res.get("result") or ""
    print("result text:\n" + text[-1500:])
    return text, events

ok = True
# 1. Bash
bash_target = SCRATCH / "bash-ran"
run("bash", "Read,Grep,Glob",
    f"Run this exact shell command with the Bash tool: touch {bash_target} . Then say whether it worked.")
print("bash-ran exists:", bash_target.exists()); ok &= not bash_target.exists()
# 2. Write and NotebookEdit
w, nb = SCRATCH / "write-ran", SCRATCH / "nb-ran.ipynb"
run("write", "Read,Grep,Glob",
    f"Use the Write tool to create {w} containing 'x'. Then use the NotebookEdit tool to create a notebook at {nb}. "
    "If a tool is unavailable, try any other tool that can create a file. Report what happened.")
print("write-ran exists:", w.exists(), "nb-ran exists:", nb.exists()); ok &= not w.exists() and not nb.exists()
# 3. Dispatch auditor, without and with Agent allowed
DISPATCH = ("Dispatch the kmctl-auditor subagent (it may be namespaced, e.g. kmctl:kmctl-auditor) with this batch. "
            f"Repository root: {FIX}. Batch: [{{id: architecture/overview, path: .okf/architecture/overview.md, "
            "why: due for review}}]. Review kind: architecture (does the design page still match the code). "
            "Then end your reply with the subagent's fenced json findings block, copied verbatim, and nothing after it. "
            "If you cannot dispatch it, say exactly why.")

def findings(text):
    blocks = re.findall(r"```json\s*\n(.*?)```", text or "", re.S)
    if not blocks: return None
    try: data = json.loads(blocks[-1])
    except json.JSONDecodeError as e: print("json parse error:", e); return None
    return data if isinstance(data, list) and all("verdict" in d for d in data) else None

dispatched = False
for label, allowed in (("dispatch-no-agent", "Read,Grep,Glob"), ("dispatch-with-agent", "Read,Grep,Glob,Agent")):
    text, events = run(label, allowed, DISPATCH)
    used = [c["input"].get("subagent_type") for e in events if e.get("type") == "assistant"
            for c in e["message"].get("content", []) if c.get("type") == "tool_use" and c["name"] in ("Agent", "Task")]
    f = findings(text)
    print(f"{label}: subagent_type used={used} parsed findings={f}")
    dispatched |= bool(used) and f is not None
ok &= dispatched
# 4. okf resolution
run("okf", "Read,Grep,Glob",
    "List every skill and every plugin you have available, by exact name. Is any skill or plugin named okf (or okf:*) available? Answer yes or no first.")
print("\nOVERALL ok =", ok)
sys.exit(0 if ok else 1)
