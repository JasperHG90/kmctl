"""Risk 1: does kmctl build from packages/kmctl with apm/ two levels up?

Usage (from a checkout of the repo): python builds.py

For each config variant (plain = the plan's, then sdist, hook, symlink; see
restructure.py) it clones the checkout, applies the layout with apm/apm.yml
bumped to 0.99.0, and tries the four builds:
  a. uv build --package kmctl (sdist, then wheel from it)
  b. uv build --wheel --package kmctl
  c. uv tool install git+file://BARE@v0.99.0#subdirectory=packages/kmctl
  d. uv tool install ARCHIVE/packages/kmctl (git archive, no .git: action.yml's path)
A wheel passes when scripts/check_wheel.py (--pyproject packages/kmctl/pyproject.toml)
and scripts/smoke_wheel.py --version 0.99.0 both exit 0. An install passes when
its kmctl --version prints 0.99.0 and the installed package holds _skills/audit/SKILL.md,
_agents/ and _rules/. Prints a matrix; exits 0 only if the plain variant passes all four.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERSION = "0.99.0"
VARIANTS = ["plain", "sdist", "hook", "symlink"]


def sh(args, cwd, env=None):
    r = subprocess.run(
        [str(a) for a in args], cwd=cwd, env=env, capture_output=True, text=True
    )
    return r.returncode, (r.stdout + r.stderr).strip()


def tail(text: str, n: int = 3) -> str:
    errors = [line.strip() for line in text.splitlines() if "Error:" in line]
    return " | ".join(errors[-1:] or text.splitlines()[-n:])


def payload(wheel: Path) -> str:
    names = zipfile.ZipFile(wheel).namelist()
    found = [d for d in ("kmctl/_skills/", "kmctl/_agents/", "kmctl/_rules/") if any(n.startswith(d) for n in names)]
    return f"wheel holds {len(found)}/3 of _skills,_agents,_rules"


def sdist_apm(out: Path) -> str:
    sdists = sorted(out.glob("*.tar.gz"))
    if not sdists:
        return ""
    names = tarfile.open(sdists[0]).getnames()
    return f"; sdist has {sum('/apm/' in n for n in names)} apm/ files"


def wheel_case(repo: Path, out: Path, build_args: list[str]) -> str:
    code, text = sh(["uv", "build", *build_args, "--package", "kmctl", "-o", out], repo)
    if code:
        return f"FAIL build: {tail(text)}"
    wheels = sorted(out.glob("*.whl"))
    names = ",".join(p.name for p in sorted(out.iterdir()))
    if not wheels:
        return f"FAIL no wheel ({names})"
    pyproject = repo / "packages/kmctl/pyproject.toml"
    c1, t1 = sh(["uv", "run", "scripts/check_wheel.py", wheels[0], "--pyproject", pyproject], repo)
    c2, t2 = sh(["uv", "run", "scripts/smoke_wheel.py", wheels[0], "--version", VERSION], repo)
    verdict = "PASS" if c1 == 0 and c2 == 0 else "FAIL"
    return f"{verdict} built {names}{sdist_apm(out)}; {payload(wheels[0])}; check_wheel={c1} ({tail(t1, 1)}); smoke_wheel={c2} ({tail(t2, 1)})"


INSPECT = (
    "import kmctl, pathlib; p = pathlib.Path(kmctl.__file__).parent; "
    "ok = (p/'_skills/audit/SKILL.md').is_file() and (p/'_agents').is_dir() and (p/'_rules').is_dir(); "
    "print(p, ok); raise SystemExit(0 if ok else 1)"
)


def install_case(source: str, tools: Path, cwd: Path) -> str:
    env = {
        **os.environ,
        "UV_TOOL_DIR": str(tools / "tools"),
        "UV_TOOL_BIN_DIR": str(tools / "bin"),
        "KMCTL_PINNED": "1",
    }
    code, text = sh(["uv", "tool", "install", source], cwd, env)
    if code:
        return f"FAIL install: {tail(text)}"
    c1, t1 = sh([tools / "bin/kmctl", "--version"], cwd, env)
    c2, t2 = sh([tools / "tools/kmctl/bin/python", "-c", INSPECT], cwd, env)
    ok = c1 == 0 and VERSION in t1.split() and c2 == 0
    return f"{'PASS' if ok else 'FAIL'} version={t1!r}; payload={c2} ({tail(t2, 1)})"


def variant(name: str, src: Path, tmp: Path) -> dict[str, str]:
    repo = tmp / name / "repo"
    code, text = sh(
        [sys.executable, HERE / "restructure.py", src, repo, "--variant", name, "--bump", VERSION],
        tmp,
    )
    if code:
        return {"setup": f"FAIL {tail(text)}"}
    sh(["git", "tag", f"v{VERSION}"], repo)
    bare = tmp / name / "bare.git"
    sh(["git", "clone", "-q", "--bare", repo, bare], tmp)
    archive = tmp / name / "archive"
    archive.mkdir()
    subprocess.run(
        f"git -C '{repo}' archive HEAD | tar -x -C '{archive}'", shell=True, check=True
    )
    elsewhere = tmp / name / "cwd"
    elsewhere.mkdir()
    return {
        "a sdist->wheel": wheel_case(repo, tmp / name / "dist-a", []),
        "b wheel": wheel_case(repo, tmp / name / "dist-b", ["--wheel"]),
        "c git subdir": install_case(
            f"git+file://{bare}@v{VERSION}#subdirectory=packages/kmctl",
            tmp / name / "tools-c",
            elsewhere,
        ),
        "d archive dir": install_case(
            str(archive / "packages/kmctl"), tmp / name / "tools-d", elsewhere
        ),
    }


def main() -> int:
    src = Path.cwd()
    _, head = sh(["git", "rev-parse", "--short", "HEAD"], src)
    _, uv = sh(["uv", "--version"], src)
    print(f"source {src} at {head}; {uv}")
    results = {}
    with tempfile.TemporaryDirectory(prefix="k2p-builds-", dir=HERE) as t:
        tmp = Path(t)
        os.environ["UV_CACHE_DIR"] = str(tmp / "uv-cache")
        for name in VARIANTS:
            results[name] = variant(name, src, tmp)
            print(f"\n== {name}")
            for case, verdict in results[name].items():
                print(f"  {case}: {verdict}")
            sys.stdout.flush()
    print("\n== summary")
    for name, cases in results.items():
        passed = sum(v.startswith("PASS") for v in cases.values())
        print(f"  {name}: {passed}/{len(cases)} pass")
    plain = results["plain"]
    return 0 if len(plain) == 4 and all(v.startswith("PASS") for v in plain.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
