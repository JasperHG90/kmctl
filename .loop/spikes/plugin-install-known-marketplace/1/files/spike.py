"""Spike plugin-install-known-marketplace/1. User settings declare the scaccogatto
marketplace from a git URL. Shows: (a) kmctl's add of scaccogatto/okf-skills fails
with the operator's message; (b) adding from the entry's own URL, then installing
kmctl@kmctl at project scope, succeeds with okf as a dependency.
Exits 0 only when (a) fails and (b) succeeds. Runs claude with an isolated HOME,
CLAUDE_CONFIG_DIR and XDG_DATA_HOME, given to the child only."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

S = Path("/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/mkt-repro/run")
shutil.rmtree(S, ignore_errors=True)
home, repo = S / "home", S / "repo"
(home / ".claude").mkdir(parents=True)
repo.mkdir()
subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
url = "https://github.com/scaccogatto/okf-skills.git"
(home / ".claude" / "settings.json").write_text(json.dumps(
    {"extraKnownMarketplaces": {"scaccogatto": {"source": {"source": "git", "url": url}}}}))

env = {k: v for k, v in os.environ.items()
       if not (k.startswith("CLAUDE_CODE_") or k in ("CLAUDECODE", "CLAUDE_PID", "CLAUDE_EFFORT"))}
env |= {"HOME": str(home), "CLAUDE_CONFIG_DIR": str(home / ".claude"), "XDG_DATA_HOME": str(home / "data")}


def claude(*args: str) -> int:
    p = subprocess.run(["claude", *args], cwd=repo, env=env, capture_output=True, text=True, timeout=240)
    print(f"$ claude {' '.join(args)}\n  exit {p.returncode}: {(p.stdout + p.stderr).strip()[-400:]}\n")
    return p.returncode


old_add = claude("plugin", "marketplace", "add", "scaccogatto/okf-skills", "--scope", "project")
staged = subprocess.run(["/home/vscode/kmctl/.venv/bin/python", "-c", "from kmctl.plugin import stage; print(stage())"],
                        env=env, capture_output=True, text=True, check=True).stdout.strip()
new_add = claude("plugin", "marketplace", "add", url, "--scope", "project")
claude("plugin", "marketplace", "add", staged, "--scope", "project")
put = claude("plugin", "install", "kmctl@kmctl", "--scope", "project")
ok = old_add != 0 and new_add == 0 and put == 0
print("OVERALL ok =", ok)
sys.exit(0 if ok else 1)
