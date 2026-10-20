"""Copy the workspace Hermes files into this worktree, stage them, and run every prek hook."""
import shutil, subprocess, sys
from pathlib import Path

SRC = Path("/home/vscode/workspace/.github")
dst = Path.cwd() / ".github"
shutil.copytree(SRC / "skills" / "okf", dst / "skills" / "okf")
shutil.copytree(SRC / "prompts", dst / "prompts")
for wf in (SRC / "workflows").glob("hermes-*.yaml"):
    shutil.copy(wf, dst / "workflows" / wf.name)
subprocess.run(["git", "add", "-A"], check=True)
sys.exit(subprocess.run(["uvx", "prek", "run", "--all-files"]).returncode)
