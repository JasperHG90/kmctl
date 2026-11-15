"""Risk 3: does a package = false workspace root give the plan's dev loop?

Usage (from a checkout of the repo): python workspace_tests.py

1. Baseline: clone HEAD, uv sync, uv run pytest --collect-only -q; note the
   selected count.
2. Clone again and apply the layout with the plan's O2 test split
   (restructure.py --tests): root pyproject [tool.uv] package = false,
   members = ["packages/*"], kmctl and kmaudit in the dev group.
3. uv sync; check both kmctl and kmaudit are installed editable
   (direct_url.json); KMCTL_PINNED=1 uv run kmctl --version prints apm.yml's
   version.
4. uv run pytest --collect-only -q -p conftest_probe: no collection errors,
   the same selected count as the baseline, and every function a test module
   imports from conftest / fixtures / test_* comes from its own tree.
Exits 0 only if all of that holds for the layout as the plan writes it.
5. Then, as candidate fixes, each on a clean copy of the moved tree:
   addopts: drop pytest_plugins from packages/kmctl/tests/conftest.py and add
     "-p", "pytester" to the root pytest addopts;
   root-conftest: move that pytest_plugins line into the root tests/conftest.py;
   testpaths: keep it, set testpaths to the three trees.
   Each is collected and probed the same way and reported. After the addopts
   fix, the whole default suite also runs once, for information only: its
   failure count, and how many failures say a fixture or import was missing.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sh(args, cwd, env=None):
    r = subprocess.run([str(a) for a in args], cwd=cwd, env=env, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def collect(repo: Path, env) -> tuple[int, str]:
    code, text = sh(["uv", "run", "pytest", "--collect-only", "-q", "-p", "conftest_probe"], repo, env)
    return code, text


def summary(text: str) -> str:
    return [line for line in text.splitlines() if "collected" in line or "error" in line.lower()][-1:][0] if text else ""


def selected(text: str) -> int | None:
    m = re.search(r"(\d+)/(\d+) tests collected", text) or re.search(r"(\d+) tests collected", text)
    return int(m.group(1)) if m else None


def editable(repo: Path, name: str) -> str:
    hits = list(repo.glob(f".venv/lib/python*/site-packages/{name}-*.dist-info/direct_url.json"))
    if not hits:
        return "not installed"
    data = json.loads(hits[0].read_text())
    return f"editable={data.get('dir_info', {}).get('editable', False)} url={data.get('url')}"


def main() -> int:
    src = Path.cwd()
    _, head = sh(["git", "rev-parse", "--short", "HEAD"], src)
    print(f"source at {head}")
    ok = True
    with tempfile.TemporaryDirectory(prefix="k2p-ws-", dir=HERE) as t:
        tmp = Path(t)
        env = {**os.environ, "PYTHONPATH": str(HERE), "KMCTL_PINNED": "1",
               "UV_CACHE_DIR": str(tmp / "uv-cache")}
        env.pop("VIRTUAL_ENV", None)
        base = tmp / "base"
        sh(["git", "clone", "-q", src, base], tmp)
        c, text = sh(["uv", "sync", "-q"], base, env)
        assert c == 0, text
        c, text = collect(base, env)
        before = selected(text)
        print(f"baseline: exit {c}; {summary(text)}")
        print("\n".join(line for line in text.splitlines() if line.startswith("probe:")))

        repo = tmp / "moved"
        c, text = sh([sys.executable, HERE / "restructure.py", src, repo, "--tests"], tmp, env)
        print(f"restructure: exit {c}; {text.splitlines()[-1] if text else ''}")
        if c:
            print(text)
            return 1
        c, text = sh(["uv", "sync"], repo, env)
        print(f"uv sync: exit {c}; {' | '.join(l for l in text.splitlines() if 'kmctl' in l or 'kmaudit' in l or 'error' in l)}")
        ok &= c == 0
        for name in ("kmctl", "kmaudit"):
            state = editable(repo, name)
            print(f"{name}: {state}")
            ok &= "editable=True" in state
        version = re.search(r"(?m)^version: (\S+)", (repo / "apm/apm.yml").read_text()).group(1)
        c, text = sh(["uv", "run", "kmctl", "--version"], repo, env)
        print(f"uv run kmctl --version: exit {c}; {text!r} (apm.yml says {version})")
        ok &= c == 0 and version in text.split()
        c, text = collect(repo, env)
        after = selected(text)
        print(f"moved: exit {c}; {summary(text)}")
        probe = [line for line in text.splitlines() if line.startswith("probe:")]
        print("\n".join(probe))
        errors = [line for line in text.splitlines() if line.startswith("ERROR")]
        print("\n".join(errors[:20]))
        ok &= c == 0 and not errors and after == before and after is not None
        ok &= any("from the wrong tree 0" in line for line in probe)
        print(f"\nplan as written: selected before {before}, after {after}; result {'OK' if ok else 'FAIL'}")
        conftest = repo / "packages/kmctl/tests/conftest.py"
        pyproject = repo / "pyproject.toml"
        line = 'pytest_plugins = ("pytester",)\n'
        for fix in ("addopts", "root-conftest", "testpaths"):
            sh(["git", "checkout", "-q", "--", "."], repo)
            if fix == "addopts":
                conftest.write_text(conftest.read_text().replace(line, ""))
                pyproject.write_text(pyproject.read_text().replace(
                    'addopts = ["--strict-markers", "-m", "not integration"]',
                    'addopts = ["--strict-markers", "-m", "not integration", "-p", "pytester"]'))
            elif fix == "root-conftest":
                conftest.write_text(conftest.read_text().replace(line, ""))
                root_conftest = repo / "tests/conftest.py"
                root_conftest.write_text(line + root_conftest.read_text())
            else:
                pyproject.write_text(pyproject.read_text().replace(
                    'addopts = ["--strict-markers", "-m", "not integration"]',
                    'addopts = ["--strict-markers", "-m", "not integration"]\n'
                    'testpaths = ["tests", "packages/kmctl/tests", "packages/kmaudit/tests"]'))
            sh(["git", "diff", "--stat"], repo)
            c, text = collect(repo, env)
            probe = [l for l in text.splitlines() if l.startswith("probe:")]
            errors = [l for l in text.splitlines() if l.startswith("ERROR")]
            fine = c == 0 and not errors and selected(text) == before and any("from the wrong tree 0" in l for l in probe)
            print(f"\nfix {fix}: exit {c}; {summary(text)}; {'OK' if fine else 'FAIL'}")
            print("\n".join(probe + errors[:10]))
            if fix == "addopts":
                c, text = sh(["uv", "run", "pytest", "-q", "-p", "no:cacheprovider", "-rf"], repo, env)
                lines = text.splitlines()
                failed = [l for l in lines if l.startswith("FAILED ")]
                missing = [l for l in lines if re.search(r"fixture '.*' not found|ImportError|ModuleNotFoundError", l)]
                print(f"full run after addopts: exit {c}; {lines[-1] if lines else ''}")
                print(f"  failures naming a missing fixture/import: {len(missing)}")
                for l in failed:
                    print("  " + l[:160])
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
