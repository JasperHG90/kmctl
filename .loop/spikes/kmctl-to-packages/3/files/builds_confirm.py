"""Risk 1, confirming run: does the plan's revised config pass all four builds?

Usage (from a checkout of the repo): python builds_confirm.py

Applies restructure.py --variant hook --bump 0.99.0 (packages/kmctl/hatch_build.py
force-includes from ../../apm when it exists, else the sdist's apm/; the wheel
force-include table is replaced by the hook's apm-include table), then:
- trims the sdist force-include to the three folders the plan names
  (skills, agents, instructions; no apm.yml);
- patches scripts/check_wheel.py to read the hook's apm-include table when
  the wheel has no force-include table;
- commits, tags v0.99.0, and runs builds.py's four cases (a sdist->wheel,
  b --wheel, c git+file subdirectory install, d git-archive folder install).
Exits 0 only if all four pass.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import builds  # noqa: E402

VERSION = builds.VERSION

OLD = '''    data = tomllib.loads(pyproject.read_text())
    table = data["tool"]["hatch"]["build"]["targets"]["wheel"]["force-include"]
    root = pyproject.parent
'''
NEW = '''    data = tomllib.loads(pyproject.read_text())
    wheel = data["tool"]["hatch"]["build"]["targets"]["wheel"]
    root = pyproject.parent
    if "force-include" not in wheel:
        hook = wheel["hooks"]["custom"]["apm-include"]
        base = root / "../../apm"
        if not base.is_dir():
            base = root / "apm"
        return [
            f"{target}/" if (base / source).is_dir() else str(target)
            for source, target in hook.items()
        ]
    table = wheel["force-include"]
'''


def main() -> int:
    src = Path.cwd()
    _, head = builds.sh(["git", "rev-parse", "--short", "HEAD"], src)
    _, uv = builds.sh(["uv", "--version"], src)
    print(f"source {src} at {head}; {uv}")
    with tempfile.TemporaryDirectory(prefix="k2p-confirm-", dir=HERE) as t:
        tmp = Path(t)
        os.environ["UV_CACHE_DIR"] = str(tmp / "uv-cache")
        repo = tmp / "repo"
        code, text = builds.sh(
            [sys.executable, HERE / "restructure.py", src, repo, "--variant", "hook", "--bump", VERSION], tmp
        )
        if code:
            print(f"setup FAIL: {text}")
            return 1
        pp = repo / "packages/kmctl/pyproject.toml"
        body = pp.read_text()
        line = '"../../apm/apm.yml" = "apm/apm.yml"\n'
        assert line in body
        pp.write_text(body.replace(line, ""))
        cw = repo / "scripts/check_wheel.py"
        assert OLD in cw.read_text()
        cw.write_text(cw.read_text().replace(OLD, NEW))
        env = {**os.environ, **{"GIT_AUTHOR_NAME": "spike", "GIT_AUTHOR_EMAIL": "s@x.invalid",
                                 "GIT_COMMITTER_NAME": "spike", "GIT_COMMITTER_EMAIL": "s@x.invalid"}}
        for args in (["git", "add", "-A"], ["git", "commit", "-q", "-m", "spike: plan config"], ["git", "tag", f"v{VERSION}"]):
            c, out = builds.sh(args, repo, env)
            assert c == 0, out
        print("packages/kmctl/pyproject.toml hatch tables:")
        print("\n".join("  " + l for l in pp.read_text().splitlines() if "apm" in l or l.startswith("[tool.hatch")))
        bare = tmp / "bare.git"
        builds.sh(["git", "clone", "-q", "--bare", repo, bare], tmp)
        archive = tmp / "archive"
        archive.mkdir()
        subprocess.run(f"git -C '{repo}' archive HEAD | tar -x -C '{archive}'", shell=True, check=True)
        elsewhere = tmp / "cwd"
        elsewhere.mkdir()
        results = {
            "a sdist->wheel": builds.wheel_case(repo, tmp / "dist-a", []),
            "b wheel": builds.wheel_case(repo, tmp / "dist-b", ["--wheel"]),
            "c git subdir": builds.install_case(
                f"git+file://{bare}@v{VERSION}#subdirectory=packages/kmctl", tmp / "tools-c", elsewhere
            ),
            "d archive dir": builds.install_case(str(archive / "packages/kmctl"), tmp / "tools-d", elsewhere),
        }
    for case, verdict in results.items():
        print(f"  {case}: {verdict}")
    passed = sum(v.startswith("PASS") for v in results.values())
    print(f"summary: {passed}/4 pass")
    return 0 if passed == 4 else 1


if __name__ == "__main__":
    raise SystemExit(main())
