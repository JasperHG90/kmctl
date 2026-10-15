"""Risk 2: does `hermes -z` run unattended with a fresh HOME, taking the
provider, model and base URL without a hand-made config.

Exits 0 only when, with stdin closed and no TTY:
  F. flags + env only (no config.yaml): --provider custom -m MODEL,
     CUSTOM_BASE_URL=... exits 0 in time, calls the endpoint, and stdout
     holds a parseable fenced json block;
  G. a script-written config.yaml with api_key: ${ENV} also works and sends
     that key.
Also records: the context-window check, the --ignore-* flags under -z, and
which repo context files Hermes injects.
"""

import json
import re
import sys

sys.path.insert(0, "/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-hermes")
from drive import run  # noqa: E402

FENCE = re.compile(r"```json\s*\n(.*?)\n```", re.S)


def parsed(stdout):
    m = FENCE.search(stdout)
    try:
        return json.loads(m.group(1)) if m else None
    except ValueError:
        return None


def show(name, r):
    keep = {k: r[k] for k in ("rc", "secs", "auth", "models", "stream",
                              "offered_tools", "stdout", "stderr_tail",
                              "requests", "sys_has_agents_md",
                              "sys_has_claude_md", "sys_has_cursorrules")}
    print(f"== {name}\n{json.dumps(keep, indent=1)}\n")


ok = True

f = run(["--provider", "custom", "-m", "fake-model", "-t", "file"],
        extra_env={"CUSTOM_BASE_URL": "@BASE@"}, timeout=90)
show("F: flags + CUSTOM_BASE_URL, no config.yaml", f)
f_ok = (f["rc"] == 0 and f["models"] == ["fake-model"]
        and parsed(f["stdout"]) is not None)
print("F flags-only unattended run ok:", f_ok, "| parsed:", parsed(f["stdout"]))
ok &= f_ok

cfg = ("model:\n  provider: custom\n  base_url: @BASE@\n  default: fake-model\n"
       "  api_key: ${FAKE_API_KEY}\n")
g = run(["-t", "file"], config=cfg, timeout=90)
show("G: script-written config.yaml, key from ${FAKE_API_KEY}", g)
g_ok = (g["rc"] == 0 and g["auth"] == ["Bearer sk-fake-123"]
        and parsed(g["stdout"]) is not None)
print("G config route ok:", g_ok)
ok &= g_ok

# Context files and the --ignore-* flags under -z (recorded, not gating).
h = run(["--provider", "custom", "-m", "fake-model", "-t", "file",
         "--ignore-user-config", "--ignore-rules"],
        extra_env={"CUSTOM_BASE_URL": "@BASE@"}, timeout=90)
print("H with --ignore-user-config --ignore-rules: rc", h["rc"],
      "AGENTS.md injected:", h["sys_has_agents_md"],
      "CLAUDE.md:", h["sys_has_claude_md"], ".cursorrules:", h["sys_has_cursorrules"])
print("F (no ignore flags) AGENTS.md injected:", f["sys_has_agents_md"])

# Context window: endpoint reports 16K (recorded, not gating).
import os
os.environ["FAKE_CTX"] = "16384"
i = run(["--provider", "custom", "-m", "fake-model", "-t", "file"],
        extra_env={"CUSTOM_BASE_URL": "@BASE@"}, timeout=90)
del os.environ["FAKE_CTX"]
print("I endpoint reports 16K context: rc", i["rc"], "| stderr:", i["stderr_tail"].strip()[:400])
print("I metadata requests:", i["requests"])

print("RESULT:", "unattended run works" if ok else "risk holds")
sys.exit(0 if ok else 1)
