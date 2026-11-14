"""Risk 3, confirming run: does one root pytest collect 1407 tests in the revised layout?

Usage (from a checkout of the repo): python collect_confirm.py

Applies restructure.py --tests (root [tool.uv] package = false, members
packages/*, the O2 test split and its path fixes), then the plan's fix:
"-p", "pytester" in the root pytest addopts and the moved conftest's
pytest_plugins line removed. Runs uv sync, then
uv run pytest -m "not integration" --collect-only -q at the root.
Exits 0 only if that exits 0, prints no ERROR line, and selects exactly 1407.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED = 1407
LINE = 'pytest_plugins = ("pytester",)\n'
OLD_ADDOPTS = 'addopts = ["--strict-markers", "-m", "not integration"]'
NEW_ADDOPTS = 'addopts = ["--strict-markers", "-m", "not integration", "-p", "pytester"]'


def sh(args, cwd, env):
    r = subprocess.run([str(a) for a in args], cwd=cwd, env=env, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def main() -> int:
    src = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="k2p-collect-", dir=HERE) as t:
        tmp = Path(t)
        env = {**os.environ, "KMCTL_PINNED": "1", "UV_CACHE_DIR": str(tmp / "uv-cache")}
        env.pop("VIRTUAL_ENV", None)
        repo = tmp / "repo"
        c, text = sh([sys.executable, HERE / "restructure.py", src, repo, "--tests"], tmp, env)
        print(f"restructure: exit {c}; {text.splitlines()[-1] if text else ''}")
        if c:
            print(text)
            return 1
        conftest = repo / "packages/kmctl/tests/conftest.py"
        pyproject = repo / "pyproject.toml"
        assert LINE in conftest.read_text(), "pytest_plugins line not found"
        assert OLD_ADDOPTS in pyproject.read_text(), "addopts line not found"
        conftest.write_text(conftest.read_text().replace(LINE, ""))
        pyproject.write_text(pyproject.read_text().replace(OLD_ADDOPTS, NEW_ADDOPTS))
        root = pyproject.read_text()
        print("root pyproject:", re.search(r"(?m)^package = false$", root) is not None and "package = false",
              re.search(r"(?m)^members = .*$", root).group(0), "|", NEW_ADDOPTS)
        c, text = sh(["uv", "sync", "-q"], repo, env)
        print(f"uv sync: exit {c}")
        if c:
            print(text)
            return 1
        c, text = sh(["uv", "run", "pytest", "-m", "not integration", "--collect-only", "-q"], repo, env)
        lines = text.splitlines()
        errors = [l for l in lines if l.startswith("ERROR")]
        m = re.search(r"(\d+)/(\d+) tests collected", text) or re.search(r"(\d+) tests collected", text)
        n = int(m.group(1)) if m else None
        per_tree = {}
        for l in lines:
            if "::" in l:
                key = "packages/kmctl" if l.startswith("packages/kmctl/") else "packages/kmaudit" if l.startswith("packages/kmaudit/") else l.split("/")[0]
                per_tree[key] = per_tree.get(key, 0) + 1
        print(f"pytest --collect-only: exit {c}; {lines[-1] if lines else ''}")
        print(f"selected {n}; by tree {per_tree}; ERROR lines {len(errors)}")
        print("\n".join(errors[:20]))
    ok = c == 0 and not errors and n == EXPECTED
    print(f"result: {'OK' if ok else 'FAIL'} (expected {EXPECTED})")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
