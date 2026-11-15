"""Clone a kmctl checkout and apply the kmctl-to-packages layout to the clone.

Usage: python restructure.py SRC DEST [--tests] [--variant plain|sdist|hook|symlink] [--bump VERSION]

SRC is a checkout (the spike's worktree); DEST must not exist. The clone gets:
- src/ moved to packages/kmctl/src, README.md and LICENSE copied beside it;
- packages/kmctl/pyproject.toml: kmctl's project, version regex on
  ../../apm/apm.yml, wheel force-includes from ../../apm/...;
- a root pyproject with [tool.uv] package = false, members = ["packages/*"],
  kmctl and kmaudit in the dev group;
- with --tests, the plan's O2 test split, plus the path fixes the move
  forces and the plan lists in O2/O3: kmctl's parents[2] apm/ fallbacks
  become parents[4], moved tests' parents[1] repo root becomes parents[3],
  and the moved conftest's VALIDATOR points at the root tests/vendor/;
- --variant (default plain, the plan's config): sdist adds SDIST_FIX; hook
  swaps the wheel force-include table for HOOK_TABLE plus hatch_build.py
  (beside this file) and SDIST_FIX; symlink commits packages/kmctl/apm ->
  ../../apm and points every apm path at apm/ instead of ../../apm/;
- --bump sets apm/apm.yml's version line, so the build version is traceable.
Then it commits (so git-based installs see the move) and runs uv lock.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

GIT_ENV = {
    "GIT_AUTHOR_NAME": "spike",
    "GIT_AUTHOR_EMAIL": "spike@example.invalid",
    "GIT_COMMITTER_NAME": "spike",
    "GIT_COMMITTER_EMAIL": "spike@example.invalid",
}

STAY_AT_ROOT = {
    "scripts",
    "test_agent.py",
    "test_audit.py",
    "test_ci.py",
    "test_repo_apm.py",
    "test_rules.py",
    "test_skills.py",
    "vendor",
}

KMCTL_PYPROJECT = '''[project]
name = "kmctl"
dynamic = ["version"]
description = "Keep a repository's docs/ and OKF knowledge bundle current, across agent harnesses."
readme = "README.md"
license = "MIT"
license-files = ["LICENSE"]
authors = [
    { name = "Jasper Ginn", email = "jasperginn@gmail.com" }
]
requires-python = ">=3.12"
dependencies = [
    "httpx>=0.28.1",
    "pydantic>=2.14.1",
    "pyyaml>=6.0.3",
    "typer>=0.27.3",
]

[project.scripts]
kmctl = "kmctl:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.version]
source = "regex"
path = "../../apm/apm.yml"
pattern = '(?m)^version: (?P<version>[^\\s#]+)'

[tool.hatch.build.targets.wheel]
packages = ["src/kmctl"]

[tool.hatch.build.targets.wheel.force-include]
"../../apm/.apm/skills" = "kmctl/_skills"
"../../apm/.apm/agents" = "kmctl/_agents"
"../../apm/claude/.apm/instructions" = "kmctl/_rules"

[tool.uv]
cache-keys = [{ file = "pyproject.toml" }, { file = "../../apm/apm.yml" }]
'''

SDIST_FIX = '''
[tool.hatch.build.targets.sdist.force-include]
"../../apm/apm.yml" = "apm/apm.yml"
"../../apm/.apm/skills" = "apm/.apm/skills"
"../../apm/.apm/agents" = "apm/.apm/agents"
"../../apm/claude/.apm/instructions" = "apm/claude/.apm/instructions"
'''

HOOK_TABLE = '''[tool.hatch.build.targets.wheel.hooks.custom]
apm-include = { ".apm/skills" = "kmctl/_skills", ".apm/agents" = "kmctl/_agents", "claude/.apm/instructions" = "kmctl/_rules" }

'''


def kmctl_pyproject(variant: str) -> str:
    p = KMCTL_PYPROJECT
    if variant == "sdist":
        return p + SDIST_FIX
    if variant == "hook":
        start = p.index("[tool.hatch.build.targets.wheel.force-include]")
        end = p.index("[tool.uv]")
        return p[:start] + HOOK_TABLE + p[end:] + SDIST_FIX
    if variant == "symlink":
        return p.replace('"../../apm/', '"apm/')
    assert variant == "plain", variant
    return p


def arg(name: str, default: str | None) -> str | None:
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


ROOT_CONFTEST = '''import os
import shutil
from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True, scope="session")
def _uv_cache(tmp_path_factory: pytest.TempPathFactory) -> Iterator[None]:
    cache = tmp_path_factory.mktemp("uv-cache")
    saved = os.environ.get("UV_CACHE_DIR")
    os.environ["UV_CACHE_DIR"] = str(cache)
    yield
    if saved is None:
        os.environ.pop("UV_CACHE_DIR", None)
    else:
        os.environ["UV_CACHE_DIR"] = saved
    shutil.rmtree(cache, ignore_errors=True)


@pytest.fixture(autouse=True)
def _pinned(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KMCTL_PINNED", "1")
'''


def run(*args: str, cwd: Path) -> None:
    import os

    subprocess.run(args, cwd=cwd, check=True, env={**os.environ, **GIT_ENV})


def root_pyproject(old: str) -> str:
    """The workspace root: no package, dev group names both members."""
    groups = old[old.index("[dependency-groups]") : old.index("# uv rebuilds kmctl")]
    groups = groups.replace(
        '    "kmaudit[tracing]",\n', '    "kmaudit[tracing]",\n    "kmctl",\n'
    )
    rest = old[old.index("[tool.ruff]") :]
    return (
        '[project]\nname = "kmctl-workspace"\nversion = "0.0.0"\n'
        'requires-python = ">=3.12"\ndependencies = []\n\n'
        + groups
        + "[tool.uv]\npackage = false\n\n"
        '[tool.uv.workspace]\nmembers = ["packages/*"]\n\n'
        "[tool.uv.sources]\n"
        "kmctl = { workspace = true }\nkmaudit = { workspace = true }\n\n"
        + rest
    )


def main() -> int:
    src, dest = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    tests = "--tests" in sys.argv
    variant = arg("--variant", "plain")
    bump = arg("--bump", None)
    run("git", "clone", "-q", str(src), str(dest), cwd=src.parent)
    pkg = dest / "packages" / "kmctl"
    pkg.mkdir(parents=True)
    run("git", "mv", "src", "packages/kmctl/src", cwd=dest)
    shutil.copy(dest / "README.md", pkg / "README.md")
    shutil.copy(dest / "LICENSE", pkg / "LICENSE")
    (pkg / "pyproject.toml").write_text(kmctl_pyproject(variant))
    if variant == "hook":
        shutil.copy(Path(__file__).parent / "hatch_build.py", pkg / "hatch_build.py")
    if variant == "symlink":
        (pkg / "apm").symlink_to("../../apm")
    if bump:
        apm = dest / "apm" / "apm.yml"
        apm.write_text(re.sub(r"(?m)^version: \S+", f"version: {bump}", apm.read_text(), count=1))
    old = (dest / "pyproject.toml").read_text()
    new = root_pyproject(old)
    assert re.search(r"(?m)^\[tool\.uv\]\npackage = false", new)
    (dest / "pyproject.toml").write_text(new)
    if tests:
        (pkg / "tests").mkdir()
        for entry in sorted((dest / "tests").iterdir()):
            if entry.name in STAY_AT_ROOT or entry.name == "__pycache__":
                continue
            run("git", "mv", f"tests/{entry.name}", f"packages/kmctl/tests/{entry.name}", cwd=dest)
        (dest / "tests" / "conftest.py").write_text(ROOT_CONFTEST)
        for name in ("plugin.py", "antigravity.py", "opencode.py"):
            f = pkg / "src" / "kmctl" / name
            f.write_text(f.read_text().replace('resolve().parents[2] / "apm"', 'resolve().parents[4] / "apm"'))
        for f in (pkg / "tests").glob("*.py"):
            f.write_text(f.read_text().replace("Path(__file__).resolve().parents[1]", "Path(__file__).resolve().parents[3]").replace("Path(__file__).parents[1]", "Path(__file__).parents[3]"))
        c = pkg / "tests" / "conftest.py"
        c.write_text(c.read_text().replace('VALIDATOR = Path(__file__).parent / "vendor"', 'VALIDATOR = Path(__file__).resolve().parents[3] / "tests" / "vendor"'))
    run("git", "add", "-A", cwd=dest)
    run("git", "commit", "-q", "-m", "spike: kmctl-to-packages layout", cwd=dest)
    run("uv", "lock", "-q", cwd=dest)
    run("git", "add", "-A", cwd=dest)
    run("git", "commit", "-q", "-m", "spike: relock", cwd=dest)
    print(f"restructure: {dest} ready (tests={tests}, variant={variant}, bump={bump})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
