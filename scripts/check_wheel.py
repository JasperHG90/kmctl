# /// script
# requires-python = ">=3.12"
# ///
"""Check that a built wheel carries the package data kmctl's pyproject adds: the skills, agents and rules.

Usage::

    uv run scripts/check_wheel.py dist/kmctl-*.whl [--pyproject packages/kmctl/pyproject.toml]

The expected entries come from the pyproject's ``apm-include`` table, which
``packages/kmctl/hatch_build.py`` copies into the wheel (ADR 0044), so the
release build and the packaging config cannot disagree about what a wheel
holds (ADR 0001, ADR 0012).
"""

from __future__ import annotations

import argparse
import sys
import tomllib
import zipfile
from pathlib import Path


def expected_entries(pyproject: Path) -> list[str]:
    """Return the wheel paths the pyproject's build hook adds.

    A directory source maps to a ``<target>/`` prefix; a file maps to its path.
    Sources are relative to the repository's ``apm/``, two folders above the
    package.
    """
    data = tomllib.loads(pyproject.read_text())
    wheel = data["tool"]["hatch"]["build"]["targets"]["wheel"]
    table = wheel["hooks"]["custom"]["apm-include"]
    root = pyproject.parent / ".." / ".." / "apm"
    return [
        f"{target}/" if (root / source).is_dir() else str(target)
        for source, target in table.items()
    ]


def missing_entries(wheel: Path, expected: list[str]) -> list[str]:
    """Return the expected entries the wheel does not hold."""
    with zipfile.ZipFile(wheel) as zf:
        names = zf.namelist()
    missing: list[str] = []
    for entry in expected:
        present = (
            any(n.startswith(entry) for n in names)
            if entry.endswith("/")
            else entry in names
        )
        if not present:
            missing.append(entry)
    return missing


def main(argv: list[str] | None = None) -> int:
    """Exit 0 when every wheel given is complete, else name what is missing and exit 1."""
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0] if __doc__ else None
    )
    parser.add_argument("wheels", nargs="+", type=Path, help="the built wheel(s)")
    parser.add_argument(
        "--pyproject",
        type=Path,
        default=Path("packages/kmctl/pyproject.toml"),
        help="the pyproject.toml whose apm-include table lists the entries",
    )
    args = parser.parse_args(argv)
    expected = expected_entries(args.pyproject.resolve())
    failed = False
    for wheel in args.wheels:
        missing = missing_entries(wheel, expected)
        if missing:
            failed = True
            print(
                f"check_wheel: {wheel.name} lacks {', '.join(missing)}", file=sys.stderr
            )
        else:
            print(f"check_wheel: {wheel.name} holds {', '.join(expected)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
