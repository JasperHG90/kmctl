"""Spike ci-audit/4: the real action/knowledge-audit.sh with real claude 2.1.300 on a
fixture with one due architecture page that has drifted (page says Hello, code says Hi).
gh is a stub that records its calls. Exits 0 only when the summary holds a drifted
finding, gh is asked to create the issue, and the fixture repository is unchanged.

The child gets a fresh-session environment (no Claude Code session variables), the
same way spike ci-audit/3 ran claude; this process's own environment is unchanged."""

import os
import subprocess
import sys
from pathlib import Path

S = Path("/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/ci-audit-real")
W = Path("/home/vscode/kmctl.worktrees/ci-audit")
for name in ("summary.md", "gh-calls"):
    (S / name).unlink(missing_ok=True)

child = {k: v for k, v in os.environ.items()
         if not (k.startswith("CLAUDE_CODE_") or k in ("CLAUDECODE", "CLAUDE_PID", "CLAUDE_EFFORT"))}
child |= {
    "PATH": f"{S / 'bin'}:{os.environ['PATH']}",
    "GITHUB_EVENT_NAME": "workflow_dispatch",
    "GITHUB_STEP_SUMMARY": str(S / "summary.md"),
    "KMCTL_PLUGIN_DIR": str(W / "plugin"),
}
p = subprocess.run(["bash", str(W / "action" / "knowledge-audit.sh")], cwd=S / "repo",
                   env=child, capture_output=True, text=True, timeout=540)
summary = (S / "summary.md").read_text() if (S / "summary.md").exists() else ""
calls = (S / "gh-calls").read_text() if (S / "gh-calls").exists() else ""
status = subprocess.run(["git", "status", "--short"], cwd=S / "repo",
                        capture_output=True, text=True).stdout
print(f"script exit {p.returncode}\nstderr tail: {p.stderr[-600:]}")
print("--- summary\n" + summary + "--- gh calls\n" + calls + "--- fixture git status\n" + status)
ok = ("| `architecture/overview` | drifted |" in summary
      and "issue create --title Knowledge audit" in calls and not status.strip())
print("OVERALL ok =", ok)
sys.exit(0 if ok else 1)
