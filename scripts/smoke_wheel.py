# /// script
# requires-python = ">=3.12"
# ///
"""Install a built wheel into a fresh environment and check it works as shipped.

Usage::

    uv run scripts/smoke_wheel.py dist/kmctl-*.whl [--package kmctl|kmaudit] [--version VERSION]

It creates a throwaway virtual environment, installs the wheel with its
dependencies, and checks that ``<package> --version`` prints the wheel's
version (or ``--version`` when given). For kmctl, the default, it also checks
that the installed package holds the skills ``kmctl briefing`` lists, such as
``kmctl/_skills/audit/SKILL.md``; kmaudit ships no skills. Exit 0 when the
checks hold (ADR 0012).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

#: One skill the package ships, under the folder ``kmctl briefing`` reads.
SKILL = "_skills/audit/SKILL.md"


def wheel_version(wheel: Path) -> str:
    """Return the version in a wheel's file name (``name-version-...whl``)."""
    return wheel.name.split("-")[1]


def version_matches(printed: str, expect: str) -> bool:
    """Whether ``kmctl --version`` output names exactly ``expect`` as a token."""
    return expect in printed.split()


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a command, capturing its output."""
    return subprocess.run(args, capture_output=True, text=True, check=False)


def smoke(wheel: Path, expect: str, package: str = "kmctl") -> list[str]:
    """Install ``wheel`` in a fresh venv and return the problems found (empty when fine)."""
    with tempfile.TemporaryDirectory(prefix=f"{package}-smoke-") as tmp:
        venv = Path(tmp) / "venv"
        made = _run(["uv", "venv", "-q", "--python", "3.12", str(venv)])
        if made.returncode != 0:
            return [f"could not create a venv: {made.stderr.strip()}"]
        python = venv / "bin" / "python"
        inst = _run(["uv", "pip", "install", "-q", "--python", str(python), str(wheel)])
        if inst.returncode != 0:
            return [f"could not install the wheel: {inst.stderr.strip()}"]
        problems: list[str] = []
        command = venv / "bin" / package
        version = (
            _run([str(command), "--version"])
            if command.is_file()
            else subprocess.CompletedProcess([], 1, "", "")
        )
        if version.returncode != 0 or not version_matches(version.stdout, expect):
            problems.append(
                f"{package} --version printed {version.stdout.strip()!r}, not {expect}"
            )
        if package != "kmctl":
            return problems
        found = _run(
            [
                str(python),
                "-c",
                (
                    "import kmctl, pathlib; "
                    f"p = pathlib.Path(kmctl.__file__).parent / {SKILL!r}; "
                    "print(p); raise SystemExit(0 if p.is_file() else 1)"
                ),
            ]
        )
        if found.returncode != 0:
            problems.append(
                f"the installed package holds no skills at {found.stdout.strip()}"
                f"{found.stderr.strip()}"
            )
        return problems


def main(argv: list[str] | None = None) -> int:
    """Smoke-test the wheel and exit 1 naming each problem."""
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0] if __doc__ else None
    )
    parser.add_argument("wheel", type=Path, help="the built wheel")
    parser.add_argument(
        "--package",
        choices=("kmctl", "kmaudit"),
        default="kmctl",
        help="the package the wheel builds (default kmctl); kmaudit skips the skills check",
    )
    parser.add_argument(
        "--version",
        help="the version the package must report; default: the wheel file name's",
    )
    args = parser.parse_args(argv)
    expect = args.version or wheel_version(args.wheel)
    problems = smoke(args.wheel.resolve(), expect, args.package)
    for problem in problems:
        print(f"smoke_wheel: {problem}", file=sys.stderr)
    if not problems:
        held = ", holds its skills" if args.package == "kmctl" else ""
        print(f"smoke_wheel: {args.wheel.name} installs, reports {expect}{held}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
