# /// script
# requires-python = ">=3.12"
# dependencies = ["packaging"]
# ///
"""Work out the next release version from the newest ``v*`` tag (ADR 0012).

Usage::

    uv run scripts/next_release_version.py INCREMENT [--pre a|b|rc] [--version X] [--repo PATH]

INCREMENT is one of PATCH, MINOR, MAJOR (raise that part of the newest
release, optionally starting a pre-release series with ``--pre``), PRE (the
next pre-release of the same version: the counter, or a later label given
with ``--pre``) or FINAL (promote the newest pre-release to its release).
``--version`` overrides the arithmetic and is required for the first release,
when no tag exists. The version is printed without the ``v``.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

from packaging.version import InvalidVersion, Version

INCREMENTS = ("PATCH", "MINOR", "MAJOR", "PRE", "FINAL")
PRE_LABELS = ("a", "b", "rc")


class Refused(Exception):
    """The version cannot be worked out; the message names the fix."""


def _parse(text: str) -> Version:
    """Parse a release version, refusing anything that is not one."""
    try:
        version = Version(text)
    except InvalidVersion as exc:
        raise Refused(
            f"{text!r} is not a version; type it like 0.2.0 or 0.2.0a1"
        ) from exc
    # One spelling per version, so the tag, the wheel and the manifest all agree.
    if str(version) != text:
        raise Refused(
            f"{text!r} is not written the canonical way; type it as {version}"
        )
    if len(version.release) != 3:
        raise Refused(f"{text!r} must name X.Y.Z, e.g. 0.2.0 or 0.2.0a1")
    return version


def newest_tag(tags: Iterable[str]) -> str | None:
    """Return the highest version among ``v<version>`` tags, without the ``v``."""
    found: list[Version] = []
    for tag in tags:
        if not tag.startswith("v"):
            continue
        try:
            found.append(Version(tag[1:]))
        except InvalidVersion:
            continue
    return str(max(found)) if found else None


def next_version(
    newest: str | None, increment: str, pre: str | None, explicit: str | None = None
) -> str:
    """Return the next version after ``newest``.

    Parameters
    ----------
    newest :
        The newest released version, without ``v``, or ``None`` before the first release.
    increment :
        PATCH, MINOR, MAJOR, PRE or FINAL.
    pre :
        A pre-release label (``a``, ``b``, ``rc``) to start or switch to, or ``None``.
    explicit :
        A version typed by the operator; it wins when given.

    Returns
    -------
    str
        The version to release, without ``v``.

    Raises
    ------
    Refused
        When the increment cannot apply, or no tag exists and no version was given.
    """
    if pre is not None and pre not in PRE_LABELS:
        raise Refused(
            f"pre-release label {pre!r} is not one of {', '.join(PRE_LABELS)}"
        )
    current = _parse(newest) if newest else None
    if explicit:
        wanted = _parse(explicit)
        if current is not None and wanted <= current:
            raise Refused(f"{wanted} is not above the newest release {current}")
        return str(wanted)
    if current is None:
        raise Refused("there is no v* tag yet; give the first version with --version")
    if increment not in INCREMENTS:
        raise Refused(f"increment {increment!r} is not one of {', '.join(INCREMENTS)}")
    major, minor, patch = [*current.release, 0, 0][:3]
    if increment in ("PRE", "FINAL"):
        if current.pre is None:
            raise Refused(f"{current} is not a pre-release; use PATCH, MINOR or MAJOR")
        label, number = current.pre
        core = f"{major}.{minor}.{patch}"
        if increment == "FINAL":
            return core
        target = pre or label
        if PRE_LABELS.index(target) < PRE_LABELS.index(label):
            raise Refused(
                f"{target} after {label} goes backwards; use {label} or later"
            )
        return f"{core}{target}{number + 1 if target == label else 1}"
    if increment == "MAJOR":
        core = f"{major + 1}.0.0"
    elif increment == "MINOR":
        core = f"{major}.{minor + 1}.0"
    else:
        core = f"{major}.{minor}.{patch + 1}"
    return f"{core}{pre}1" if pre else core


def repo_tags(repo: Path) -> list[str]:
    """Return the repository's tag names."""
    out = subprocess.run(
        ["git", "tag", "--list"], cwd=repo, capture_output=True, text=True, check=True
    )
    return out.stdout.split()


def main(argv: list[str] | None = None) -> int:
    """Print the next version, or name the fix on stderr and exit 1."""
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0] if __doc__ else None
    )
    parser.add_argument("increment", help="PATCH, MINOR, MAJOR, PRE or FINAL")
    parser.add_argument(
        "--pre", choices=PRE_LABELS, help="start or switch a pre-release series"
    )
    parser.add_argument("--version", help="the exact version to release, e.g. 0.2.0a1")
    parser.add_argument(
        "--repo", type=Path, default=Path.cwd(), help="the repository root"
    )
    args = parser.parse_args(argv)
    try:
        version = next_version(
            newest_tag(repo_tags(args.repo)),
            args.increment.upper(),
            args.pre,
            args.version,
        )
    except Refused as exc:
        print(f"next_release_version: refused: {exc}", file=sys.stderr)
        return 1
    print(version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
