# /// script
# requires-python = ">=3.12"
# ///
"""Check that a built wheel carries its package's data: kmctl's skills, agents and rules, kmaudit's non-Python files.

Usage::

    uv run scripts/check_wheel.py dist/kmctl-*.whl [--package kmctl|kmaudit] [--pyproject PATH]

``--package`` picks the pyproject, ``packages/<package>/pyproject.toml``
(kmctl by default); ``--pyproject`` overrides it. For kmctl the expected
entries come from the pyproject's ``apm-include`` table, which
``packages/kmctl/hatch_build.py`` copies into the wheel (ADR 0044), so the
release build and the packaging config cannot disagree about what a wheel
holds (ADR 0001, ADR 0012). A pyproject with no such table, kmaudit's, expects
each package folder its wheel target names and every non-Python file in it,
such as ``kmaudit/ui.html``.
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
    Sources are relative to the package's own ``apm/`` folder (ADR 0045).
    """
    data = tomllib.loads(pyproject.read_text())
    wheel = data["tool"]["hatch"]["build"]["targets"]["wheel"]
    if "apm-include" not in wheel.get("hooks", {}).get("custom", {}):
        return _package_entries(pyproject.parent, wheel["packages"])
    table = wheel["hooks"]["custom"]["apm-include"]
    root = pyproject.parent / "apm"
    return [
        f"{target}/" if (root / source).is_dir() else str(target)
        for source, target in table.items()
    ]


def _package_entries(project: Path, packages: list[str]) -> list[str]:
    """Return each package folder as ``<name>/`` and the non-Python files under it."""
    entries: list[str] = []
    for package in packages:
        source = project / package
        entries.append(f"{source.name}/")
        entries += sorted(
            f"{source.name}/{path.relative_to(source).as_posix()}"
            for path in source.rglob("*")
            if path.is_file()
            and path.suffix not in (".py", ".pyc")
            and "__pycache__" not in path.parts
        )
    return entries


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
        "--package",
        choices=("kmctl", "kmaudit"),
        default="kmctl",
        help="the package the wheel builds; picks packages/<package>/pyproject.toml (default kmctl)",
    )
    parser.add_argument(
        "--pyproject",
        type=Path,
        help="the pyproject.toml that lists the entries; default packages/<package>/pyproject.toml",
    )
    args = parser.parse_args(argv)
    pyproject = args.pyproject or Path("packages", args.package, "pyproject.toml")
    expected = expected_entries(pyproject.resolve())
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
