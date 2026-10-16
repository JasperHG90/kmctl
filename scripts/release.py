# /// script
# requires-python = ">=3.12"
# dependencies = ["packaging"]
# ///
"""The release workflows' helper: read, set and compare the release version (ADR 0012).

Usage::

    uv run scripts/release.py current
    uv run scripts/release.py set VERSION
    uv run scripts/release.py compare OLD NEW
    uv run scripts/release.py is-prerelease VERSION

``plugin/.claude-plugin/plugin.json`` carries the one version, and
``pyproject.toml`` reads it from there. APM needs a ``version:`` in each
apm.yml, so ``set`` writes the manifest and copies the version into the root
``apm.yml`` and ``apm/apm.yml``; ``current`` refuses when a copy differs
(ADR 0013). ``set`` also points the five install lines in the docs, and the
APM how-to's package pins and CLI install line, at the tag ``vVERSION``. This script never
commits or tags: ``.github/workflows/release.yml`` opens the version pull
request and ``release-tag.yml`` tags the merge, so there is one release path.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from packaging.version import InvalidVersion, Version

MANIFEST = Path("plugin/.claude-plugin/plugin.json")
#: The docs whose install lines ``set`` points at the release tag.
DOC_FILES = (
    Path("README.md"),
    Path("docs/tutorials/get-started-with-kmctl.md"),
    Path("docs/how-to/install-the-plugin-and-the-ci-action.md"),
)
#: How many install lines ``DOC_FILES`` hold between them.
DOC_LINES = 5
#: The apm.yml files that copy the manifest's version, because APM requires one.
APM_FILES = (Path("apm.yml"), Path("apm/apm.yml"))
#: The how-to whose ``JasperHG90/Knowledge-management/apm`` pins ``set`` moves.
APM_DOC = Path("docs/how-to/install-kmctl-with-apm.md")
_INSTALL = re.compile(
    r"^(\s*uv tool install git\+https://github\.com/JasperHG90/Knowledge-management)(@\S+)?$",
    re.MULTILINE,
)
# The same pattern pyproject.toml's [tool.hatch.version] reads, so only the
# version string changes and the rest of the manifest keeps its layout.
_VERSION = re.compile(r'("version": ")[^"]+(")')
_USES = re.compile(r"^(\s*- uses: JasperHG90/Knowledge-management)@\S+$", re.MULTILINE)
# One top-level ``version:`` line, rewritten as text so comments and layout stay.
_APM_VERSION = re.compile(r"^(version: )(.*)$", re.MULTILINE)
# The APM package with an optional #ref; not apm.yml or a longer path.
_APM_PIN = re.compile(
    r"(JasperHG90/Knowledge-management/apm)(?:#[\w.+-]+)?(?![\w/]|\.\w)"
)


class ReleaseRefused(Exception):
    """A release precondition failed; the message names the fix."""


def parse_version(text: str) -> Version:
    """Parse a version written the canonical way as X.Y.Z, refusing anything else."""
    try:
        version = Version(text)
    except InvalidVersion as exc:
        raise ReleaseRefused(
            f"{text!r} is not a version; use e.g. 0.2.0 or 0.2.0a1"
        ) from exc
    if str(version) != text:
        raise ReleaseRefused(
            f"{text!r} is not written the canonical way; use {version}"
        )
    if len(version.release) != 3:
        raise ReleaseRefused(f"{text!r} must name X.Y.Z, e.g. 0.2.0 or 0.2.0a1")
    return version


def parse_release(text: str) -> Version:
    """Parse a version that may be released: no ``.devN`` and no ``+local`` part."""
    version = parse_version(text)
    if version.is_devrelease or version.local is not None:
        raise ReleaseRefused(
            f"{text!r} is not a release: a .dev or +local version is never tagged; "
            "use e.g. 0.2.0 or 0.2.0a1"
        )
    return version


def _apm_version(path: Path) -> str | None:
    """Return the top-level ``version:`` of the apm.yml at ``path``, or None."""
    match = _APM_VERSION.search(path.read_text()) if path.is_file() else None
    return match.group(2).strip().strip("'\"") if match else None


def current(repo: Path) -> str:
    """Return the version the plugin manifest declares.

    Raises
    ------
    ReleaseRefused
        When an apm.yml in ``APM_FILES`` is missing or holds another version.
    """
    version = str(json.loads((repo / MANIFEST).read_text())["version"])
    for rel in APM_FILES:
        found = _apm_version(repo / rel)
        if found != version:
            raise ReleaseRefused(
                f"{rel} has version {found or 'none'} but {MANIFEST} has {version}; "
                f"run scripts/release.py set {version}"
            )
    return version


def pin_docs(text: str, version: str) -> tuple[str, int]:
    """Point each install line in ``text`` at the tag ``v<version>``.

    Returns
    -------
    tuple[str, int]
        The new text and how many lines it pinned.
    """
    text, installs = _INSTALL.subn(rf"\g<1>@v{version}", text)
    text, uses = _USES.subn(rf"\g<1>@v{version}", text)
    return text, installs + uses


def pin_apm_doc(text: str, version: str) -> tuple[str, int]:
    """Point each ``JasperHG90/Knowledge-management/apm`` in ``text`` at ``#v<version>``.

    Returns
    -------
    tuple[str, int]
        The new text and how many pins it moved.
    """
    return _APM_PIN.subn(rf"\g<1>#v{version}", text)


def set_version(repo: Path, version_text: str) -> list[Path]:
    """Write the version into the plugin manifest and both apm.yml files, and pin the docs.

    Nothing is written unless the version is valid, all five install lines and
    an APM pin in ``APM_DOC`` are found, and each apm.yml has a ``version:`` line.

    Returns
    -------
    list[Path]
        The repo-relative paths written.

    Raises
    ------
    ReleaseRefused
        When the version is malformed, the docs hold fewer than five install
        lines, ``APM_DOC`` has no APM pin, or an apm.yml has no ``version:``.
    """
    version = str(parse_release(version_text))
    docs: dict[Path, str] = {}
    found = 0
    for rel in DOC_FILES:
        docs[rel], count = pin_docs((repo / rel).read_text(), version)
        found += count
    if found < DOC_LINES:
        raise ReleaseRefused(
            f"found {found} of the {DOC_LINES} install lines in {', '.join(map(str, DOC_FILES))}; "
            "restore the missing uv tool install or uses: line"
        )
    apm_doc, _ = pin_docs((repo / APM_DOC).read_text(), version)
    docs[APM_DOC], count = pin_apm_doc(apm_doc, version)
    if count == 0:
        raise ReleaseRefused(
            f"{APM_DOC} has no JasperHG90/Knowledge-management/apm pin; restore it"
        )
    manifest = repo / MANIFEST
    text, count = _VERSION.subn(rf"\g<1>{version}\g<2>", manifest.read_text(), count=1)
    if count != 1:
        raise ReleaseRefused(f'{MANIFEST} has no "version": "..." line; restore it')
    apm: dict[Path, str] = {}
    for rel in APM_FILES:
        apm[rel], count = _APM_VERSION.subn(
            rf"\g<1>{version}", (repo / rel).read_text(), count=1
        )
        if count != 1:
            raise ReleaseRefused(f"{rel} has no top-level version: line; restore it")
    manifest.write_text(text)
    for rel, text in {**apm, **docs}.items():
        (repo / rel).write_text(text)
    return [MANIFEST, *APM_FILES, *DOC_FILES, APM_DOC]


def compare(old_text: str, new_text: str) -> str:
    """Return ``raised``, ``same``, ``lowered`` or ``skip`` for a version change.

    ``skip`` means the new version can never be released (a ``.dev`` or
    ``+local`` version), so nothing is tagged. With no old version, a releasable
    new version counts as raised.
    """
    new = parse_version(new_text)
    if new.is_devrelease or new.local is not None:
        return "skip"
    if not old_text:
        return "raised"
    old = parse_version(old_text)
    return "raised" if new > old else "same" if new == old else "lowered"


def main(argv: list[str] | None = None) -> int:
    """Run one subcommand and map a refusal to exit 1."""
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0] if __doc__ else None
    )
    parser.add_argument(
        "--repo", type=Path, default=Path.cwd(), help="the repository root"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_cur = sub.add_parser(
        "current",
        help="print the plugin manifest's version; refuse when an apm.yml differs",
    )
    p_set = sub.add_parser(
        "set",
        help="write the version into the manifest and both apm.yml files, and pin the docs",
    )
    p_set.add_argument("version", help="the release version, e.g. 0.2.0 or 0.2.0rc1")
    p_cmp = sub.add_parser("compare", help="print raised, same, lowered or skip")
    p_cmp.add_argument("old", help="the version before, or an empty string for none")
    p_cmp.add_argument("new", help="the version after")
    p_pre = sub.add_parser(
        "is-prerelease", help="exit 0 for an a, b or rc version, else 1"
    )
    p_pre.add_argument("version", help="the version to test, e.g. 0.2.0rc1")
    for p in (p_cur, p_set, p_cmp, p_pre):
        p.add_argument("--repo", type=Path, default=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    repo: Path = args.repo.resolve()
    try:
        if args.cmd == "current":
            print(current(repo))
        elif args.cmd == "set":
            for path in set_version(repo, args.version):
                print(f"wrote {path}")
        elif args.cmd == "compare":
            print(compare(args.old, args.new))
        else:
            return 0 if parse_version(args.version).is_prerelease else 1
    except ReleaseRefused as exc:
        print(f"release: refused: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
