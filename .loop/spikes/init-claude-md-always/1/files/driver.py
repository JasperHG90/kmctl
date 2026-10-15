"""Spike: which of AGENTS.md / CLAUDE.md does Claude Code load as project memory?

Four fresh git repos with unique codewords; each case run twice with no tools.
Evidence: the model's answer, plus any memory-file lines in a --debug-file log.
Exit 0 when case 4 shows AGENTS.md's codeword exactly once (both runs) and
cases 1 and 3 answer consistently across runs.
"""

import json
import os
import re
import subprocess
import sys
import tempfile

A = "PELICAN-7731"  # AGENTS.md
C = "OTTER-2208"  # CLAUDE.md
PROMPT = (
    "List every codeword in your project instructions, and say how many times "
    "each appears. Answer from your instructions only; do not read any file. "
    "End with one line exactly: COUNTS PELICAN-7731=<n> OTTER-2208=<n>"
)
AGENTS_TXT = f"# Agents\n\nCodeword: {A}\n"
CASES = {
    1: {"AGENTS.md": AGENTS_TXT},
    2: {"CLAUDE.md": f"# Claude\n\nCodeword: {C}\n"},
    3: {"AGENTS.md": AGENTS_TXT, "CLAUDE.md": f"# Claude\n\nCodeword: {C}\n"},
    4: {"AGENTS.md": AGENTS_TXT, "CLAUDE.md": "@AGENTS.md\n"},
}
DROP = {"CLAUDECODE", "CLAUDE_PID", "CLAUDE_EFFORT"}

env = {
    k: v
    for k, v in os.environ.items()
    if not k.startswith("CLAUDE_CODE_") and k not in DROP
}
base = tempfile.mkdtemp(prefix="agentsmd-", dir=os.path.dirname(os.path.abspath(__file__)))
results = {}
for case, files in CASES.items():
    for run in (1, 2):
        repo = os.path.join(base, f"case{case}-run{run}")
        os.makedirs(repo)
        for name, text in files.items():
            with open(os.path.join(repo, name), "w") as fh:
                fh.write(text)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        dbg = os.path.join(base, f"case{case}-run{run}.debug.log")
        p = subprocess.run(
            ["claude", "-p", PROMPT, "--output-format", "json", "--tools", "",
             "--debug-file", dbg],
            cwd=repo, env=env, capture_output=True, text=True, timeout=280,
        )
        try:
            answer = json.loads(p.stdout).get("result", "")
        except json.JSONDecodeError:
            answer = "UNPARSEABLE: " + p.stdout[-500:] + p.stderr[-500:]
        m = re.search(r"COUNTS\s+PELICAN-7731=(\d+)\s+OTTER-2208=(\d+)", answer)
        counts = (int(m.group(1)), int(m.group(2))) if m else None
        mem = []
        if os.path.exists(dbg):
            for line in open(dbg, errors="replace"):
                if (re.search(r"AGENTS\.md|CLAUDE\.md", line) and base in line) or re.search(r"cc-plugin-agents-md@builtin (prompt\.context|session\.start)|plugin\.register: cc-plugin-agents-md", line):
                    mem.append(line.strip()[:300])
        results[(case, run)] = counts
        print(f"=== case {case} run {run} files={sorted(files)} exit={p.returncode}")
        print(f"counts (PELICAN, OTTER) = {counts}")
        print("answer:", answer.strip().replace("\n", " | ")[:800])
        print("debug lines naming repo memory files or the builtin agents-md plugin:")
        for line in mem[:20]:
            print("   ", line)
        print()

ok = True
c4 = [results[(4, r)] for r in (1, 2)]
if any(c is None or c[0] != 1 for c in c4):
    print("FAIL: case 4 did not show PELICAN exactly once in both runs:", c4)
    ok = False
for case in (1, 3):
    pair = [results[(case, r)] for r in (1, 2)]
    if None in pair or pair[0] != pair[1]:
        print(f"FAIL: case {case} unclear across runs:", pair)
        ok = False
summary = {f"case{c}": [results[(c, r)] for r in (1, 2)] for c in CASES}
print("SUMMARY (PELICAN, OTTER) per run:", json.dumps(summary))
print("scratch:", base)
sys.exit(0 if ok else 1)
