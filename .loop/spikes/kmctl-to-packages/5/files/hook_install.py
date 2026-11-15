"""Can another repo install and run the kmctl-check hook from the moved tree?

Usage: python hook_install.py   (run from a kmctl checkout at HEAD)

Builds the kmctl-to-packages layout (restructure.py --variant hook), then for
each candidate hook manifest / root pyproject commits a clone and has a
consumer repo run kmctl-check with prek 0.5.5 and with pre-commit:
no args (must fail with a kmctl finding), args [--fix] (must write
docs/how-to/README.md), then again (must pass). Also checks uv sync at the
root for each candidate. Exits 0 when some candidate works in both tools.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESTRUCTURE = HERE.parent / "spike-k2p" / "restructure.py"
GIT_ENV = {
    "GIT_AUTHOR_NAME": "s",
    "GIT_AUTHOR_EMAIL": "s@example.invalid",
    "GIT_COMMITTER_NAME": "s",
    "GIT_COMMITTER_EMAIL": "s@example.invalid",
}

ADDL = '  additional_dependencies: ["./packages/kmctl"]\n'
EMPTY_WHEEL = (
    '\n[build-system]\nrequires = ["hatchling"]\nbuild-backend = "hatchling.build"\n\n'
    "[tool.hatch.build.targets.wheel]\nbypass-selection = true\n"
)
# candidate name -> (manifest edit, root pyproject addition)
CANDIDATES = {
    "a_addl_only": (ADDL, ""),
    "b_empty_wheel_root_plus_addl": (ADDL, EMPTY_WHEEL),
}
TOOLS = {
    "prek-0.5.5": (["uvx", "prek@0.5.5", "run", "kmctl-check", "--all-files"], "PREK_HOME"),
    "pre-commit": (["uvx", "pre-commit", "run", "kmctl-check", "--all-files"], "PRE_COMMIT_HOME"),
}


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, env=os.environ | GIT_ENV, check=True,
        capture_output=True, text=True,
    ).stdout.strip()


def run(cmd: list[str], cwd: Path, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, env=os.environ | (env or {}),
                          capture_output=True, text=True, check=False)


def write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def make_source(base: Path, dest: Path, manifest_add: str, root_add: str) -> str:
    git(base.parent, "clone", "-q", str(base), str(dest))
    m = dest / ".pre-commit-hooks.yaml"
    m.write_text(m.read_text().rstrip("\n") + "\n" + manifest_add)
    if root_add:
        p = dest / "pyproject.toml"
        text = p.read_text()
        i = text.index("[tool.uv]\npackage = false")
        p.write_text(text[:i] + root_add.lstrip("\n") + "\n" + text[i:])
        r = run(["uv", "lock", "-q"], dest)
        assert r.returncode == 0, r.stderr
    git(dest, "add", "-A")
    git(dest, "commit", "-q", "-m", "candidate")
    print(f"--- manifest:\n{m.read_text()}")
    if root_add:
        print(f"--- root pyproject addition:{root_add}")
    return git(dest, "rev-parse", "HEAD")


def uv_sync_check(src: Path) -> str:
    r = run(["uv", "sync", "--locked", "-q"], src, {"UV_PROJECT_ENVIRONMENT": str(src / ".venv")})
    if r.returncode != 0:
        return f"uv sync FAILED: {r.stderr.strip()[-400:]}"
    v = run(["uv", "run", "--no-sync", "kmctl", "--version"], src, {"KMCTL_PINNED": "1"})
    freeze = run(["uv", "pip", "list"], src).stdout
    root_installed = "kmctl-workspace" in freeze
    return (f"uv sync ok; kmctl --version -> {v.stdout.strip() or v.stderr.strip()[-200:]};"
            f" kmctl-workspace installed: {root_installed}")


def try_tool(tool: str, src: Path, rev: str, work: Path) -> tuple[bool, str]:
    cmd, home_var = TOOLS[tool]
    repo = work / f"consumer-{tool}"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    write(repo, "docs/README.md", "# Docs\n\n- [How-to guides](how-to/README.md)\n")
    write(repo, "docs/how-to/install.md", '---\ndescription: "Install it."\n---\n\n# Install it\n')
    write(repo, "docs/how-to/upgrade.md", "# Upgrade it\n")
    env = {home_var: str(work / f"home-{tool}")}

    def config(args: str) -> None:
        write(repo, ".pre-commit-config.yaml",
              f"repos:\n  - repo: {src}\n    rev: {rev}\n    hooks:\n      - id: kmctl-check\n{args}")
        git(repo, "add", "-A")

    config("")
    failed = run(cmd, repo, env)
    log = f"[no args] exit {failed.returncode}\n{(failed.stdout + failed.stderr)[-1500:]}\n"
    config("        args: [--fix]\n")
    fixed = run(cmd, repo, env)
    log += f"[--fix] exit {fixed.returncode}\n{(fixed.stdout + fixed.stderr)[-600:]}\n"
    git(repo, "add", "-A")
    again = run(cmd, repo, env)
    log += f"[again] exit {again.returncode}\n{(again.stdout + again.stderr)[-600:]}\n"
    ok = (failed.returncode != 0 and (repo / "docs/how-to/README.md").is_file()
          and again.returncode == 0)
    return ok, log


def main() -> int:
    checkout = Path.cwd()
    work = Path(tempfile.mkdtemp(prefix="k2p-hook-"))
    base = work / "moved"
    r = run([sys.executable, str(RESTRUCTURE), str(checkout), str(base), "--variant", "hook"], work)
    print(r.stdout, r.stderr[-1000:])
    if r.returncode != 0:
        return 2
    results: dict[tuple[str, str], bool] = {}
    for name, (madd, radd) in CANDIDATES.items():
        print(f"\n===== candidate {name}")
        src = work / name
        rev = make_source(base, src, madd, radd)
        print(uv_sync_check(src))
        for tool in TOOLS:
            ok, log = try_tool(tool, src, rev, work / name)
            results[(name, tool)] = ok
            print(f"\n--- {name} / {tool}: {'WORKS' if ok else 'FAILS'}\n{log}")
    print("\n===== summary")
    for (name, tool), ok in results.items():
        print(f"{name:32} {tool:12} {'WORKS' if ok else 'FAILS'}")
    both = [n for n in CANDIDATES if all(results[(n, t)] for t in TOOLS)]
    print(f"works in both tools: {both or 'none'}")
    return 0 if both else 1


if __name__ == "__main__":
    raise SystemExit(main())
