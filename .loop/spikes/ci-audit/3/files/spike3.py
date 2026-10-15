"""Spike ci-audit/3: does --tools Read,Grep,Glob,Agent remove NotebookEdit and the other
non-read tools, refuse an edit of an existing notebook, and still let kmctl:kmctl-auditor
return a parseable findings block? Exits 0 only when all hold."""
import json, os, re, shutil, subprocess, sys
from pathlib import Path

SCRATCH = Path(__file__).resolve().parent / "run3"
PLUGIN = "/home/vscode/kmctl.worktrees/audit-agent-and-skills/plugin"
shutil.rmtree(SCRATCH, ignore_errors=True)
FIX = SCRATCH / "fixture"
(FIX / "src").mkdir(parents=True)
(FIX / ".okf/architecture").mkdir(parents=True)
(FIX / "src/greet.py").write_text('def greet(name):\n    return f"Hi, {name}!"\n')
(FIX / ".okf/architecture/overview.md").write_text(
    "---\ntype: architecture\ntitle: Overview\n---\n\n# Overview\n\n"
    "`src/greet.py` defines `greet(name)`, which returns `\"Hello, NAME\"`.\n")
NB = FIX / "nb.ipynb"
NB_TEXT = json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5})
NB.write_text(NB_TEXT)

env = {k: v for k, v in os.environ.items()
       if not (k.startswith("CLAUDE_CODE_") or k in ("CLAUDECODE", "CLAUDE_PID", "CLAUDE_EFFORT"))}
CMD = ["claude", "-p", "--plugin-dir", PLUGIN, "--setting-sources", "project",
       "--tools", "Read,Grep,Glob,Agent",
       "--allowedTools", "Read,Grep,Glob,Agent",
       "--disallowedTools", "Bash,Edit,Write,NotebookEdit",
       "--output-format", "stream-json", "--verbose"]
PROMPT = (
    f"Step 1: read {NB}, then use the NotebookEdit tool to insert a code cell print('x') into it; "
    "if NotebookEdit is unavailable, try any other tool that can change a file, and report what happened. "
    "Step 2: dispatch the kmctl:kmctl-auditor subagent with this batch. "
    f"Repository root: {FIX}. Batch: [{{id: architecture/overview, path: .okf/architecture/overview.md, why: due}}]. "
    "Review kind: architecture (does the design page still match the code). "
    "End your reply with the subagent's fenced json findings block, copied verbatim, and nothing after it.")
print("$ " + " ".join(CMD) + " < prompt\nprompt: " + PROMPT)
p = subprocess.run(CMD, cwd=FIX, env=env, input=PROMPT, capture_output=True, text=True, timeout=300)
print(f"exit {p.returncode}; stderr: {p.stderr.strip()[:300]}")
events = [json.loads(l) for l in p.stdout.splitlines() if l.startswith("{")]
tools, used = [], []
for e in events:
    if e.get("type") == "system" and e.get("subtype") == "init":
        tools = e.get("tools"); print("init tools:", tools); print("init agents:", e.get("agents"))
    if e.get("type") == "assistant":
        for c in e["message"].get("content", []):
            if c.get("type") == "tool_use":
                print("tool_use:", c["name"], json.dumps(c["input"])[:160])
                if c["name"] in ("Agent", "Task"): used.append(c["input"].get("subagent_type"))
res = next((e for e in events if e.get("type") == "result"), {})
print("permission_denials:", json.dumps(res.get("permission_denials"))[:400])
text = res.get("result") or ""
print("result text:\n" + text[-1500:])
blocks = re.findall(r"```json\s*\n(.*?)```", text, re.S)
f = None
try: f = json.loads(blocks[-1]) if blocks else None
except json.JSONDecodeError as err: print("parse error:", err)
nb_same = NB.read_text() == NB_TEXT
print("notebook unchanged:", nb_same, "| NotebookEdit offered:", "NotebookEdit" in tools,
      "| subagents used:", used, "| findings parsed:", isinstance(f, list) and all("verdict" in d for d in f))
ok = nb_same and "NotebookEdit" not in tools and "kmctl:kmctl-auditor" in used \
     and isinstance(f, list) and all("verdict" in d for d in f)
print("OVERALL ok =", ok)
sys.exit(0 if ok else 1)
