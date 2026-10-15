"""Risk 1: can Hermes get file read + search without write, patch or terminal.

Exits 0 only when a read-only setup exists and holds: the model is offered
read/search tools only, its write/patch/terminal/execute_code calls are
refused, the target file is unchanged, and a read still works.
Also prints what the built-in `file` toolset offers, for the record.
"""

import json
import re
import sys

sys.path.insert(0, "/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-hermes")
from drive import run  # noqa: E402

BASE = ["--provider", "custom", "-m", "fake-model"]
ENV = {"CUSTOM_BASE_URL": "@BASE@"}
WRITERS = {"write_file", "patch", "terminal", "process", "execute_code",
           "delegate_task", "skill_manage", "memory", "cronjob"}


def show(name, r):
    keep = {k: r[k] for k in ("rc", "secs", "offered_tools", "tool_results",
                              "target_after", "new_files_in_work", "stdout",
                              "stderr_tail", "requests")}
    print(f"== {name}\n{json.dumps(keep, indent=1)}\n")


ok = True

# A. Built-in `file` toolset, for the record.
a = run(BASE + ["-t", "file"], extra_env=ENV)
show("A: -t file (built-in)", a)
print("A built-in file toolset offers writers:",
      sorted(set(a["offered_tools"]) & WRITERS), "target_after:", repr(a["target_after"]))

# B. Built-in `file` toolset fenced by HERMES_WRITE_SAFE_ROOT.
b = run(BASE + ["-t", "file"], extra_env={**ENV, "HERMES_WRITE_SAFE_ROOT": "@ROOT@/sink"})
show("B: -t file + HERMES_WRITE_SAFE_ROOT", b)
print("B target unchanged:", b["target_after"] == "original\n")

# C. Spike plugin `kmctl-read` registering a `kmctl_read` toolset.
c = run(BASE + ["-t", "kmctl_read"], extra_env=ENV, plugin=True,
        config="plugins:\n  enabled: [kmctl-read]\n")
show("C: -t kmctl_read (plugin)", c)
c_ok = (
    c["rc"] == 0
    and c["offered_tools"] == ["kmctl_read_file", "kmctl_search_files"]
    and c["target_after"] == "original\n"
    and not c["new_files_in_work"]
    and all(f"Tool '{t}' does not exist" in " ".join(c["tool_results"])
            for t in ("write_file", "patch", "terminal", "execute_code"))
    and any("hello from fixture" in t for t in c["tool_results"])
)
print("C read-only plugin holds:", c_ok)
ok &= c_ok

# D. Fail closed: the same -t when the plugin is not enabled.
d = run(BASE + ["-t", "kmctl_read"], extra_env=ENV, plugin=True)
show("D: -t kmctl_read, plugin not enabled", d)
d_ok = d["rc"] != 0 and not any(m == "POST" for m, _ in d["requests"])
print("D fails closed (non-zero, no model call):", d_ok)
ok &= d_ok

# E. No -t at all: what a forgotten flag offers.
e = run(BASE, extra_env=ENV)
print("E: no -t offers", len(e["offered_tools"]), "tools; writers:",
      sorted(set(e["offered_tools"]) & WRITERS), "target_after:", repr(e["target_after"]))

print("RESULT:", "read-only setup holds" if ok else "risk holds")
sys.exit(0 if ok else 1)
