# /// script
# requires-python = ">=3.12"
# dependencies = ["packaging"]
# ///
"""The release workflows' helper: read, set and compare the release version (ADR 0012).

Usage::

    uv run scripts/release.py current
    uv run scripts/release.py manifest
    uv run scripts/release.py set VERSION
    uv run scripts/release.py compare OLD NEW
    uv run scripts/release.py is-prerelease VERSION

``apm/apm.yml``, kmctl's APM package, carries the one version, and
``pyproject.toml`` reads it from there (ADR 0014). APM needs a ``version:`` in
each apm.yml, so ``set`` writes it into every file in ``APM_FILES``;
``current`` refuses when one differs. ``manifest`` prints ``apm/apm.yml``'s
version alone, for ``release-tag.yml``'s read of the commit before a push,
where an older commit's copies may disagree. ``set`` also points the six install lines in the docs, and the
APM how-to's CLI install line, at the tag ``vVERSION``, and moves the starter
template's ``kmctl_ref`` default in ``copier.yml`` to that tag, so the template
a release tag carries pins that release (ADR 0025). It points the two install
hints in the Claude Code hook's ``hooks.json`` at the tag too, so the hook a
release tag carries installs that release. This script never
commits or tags: ``.github/workflows/release.yml`` opens the version pull
request and ``release-tag.yml`` tags the merge, so there is one release path.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from packaging.version import InvalidVersion, Version

#: The one version source, which pyproject.toml's [tool.hatch.version] reads.
MANIFEST = Path("apm/apm.yml")
#: The docs whose install lines ``set`` points at the release tag.
DOC_FILES = (
    Path("README.md"),
    Path("docs/tutorials/get-started-with-kmctl.md"),
    Path("docs/how-to/install-the-plugin-and-the-ci-action.md"),
)
#: How many install lines ``DOC_FILES`` hold between them.
DOC_LINES = 6
#: The apm.yml files ``set`` writes the version into: the root copy, the
#: package and its two per-harness sub-packages (ADR 0020).
APM_FILES = (
    Path("apm.yml"),
    MANIFEST,
    Path("apm/claude/apm.yml"),
    Path("apm/antigravity/apm.yml"),
)
#: The APM how-to, whose install line ``set`` pins with the others.
APM_DOC = Path("docs/how-to/install-kmctl-with-apm.md")
#: The starter template's questions, whose ``kmctl_ref`` default ``set`` moves.
COPIER = Path("copier.yml")
#: The Claude Code hook, whose two install hints ``set`` points at the release tag.
HOOKS = Path("apm/claude/.apm/hooks/hooks.json")
#: How many install hints ``HOOKS`` holds.
HOOK_HINTS = 2
_INSTALL = re.compile(
    r"^(\s*uv tool install git\+https://github\.com/JasperHG90/kmctl)(@\S+)?$",
    re.MULTILINE,
)
# An install hint in the hook's command, with or without a release tag; the
# tag stops before the full stop that ends the second hint.
_HOOK_INSTALL = re.compile(
    r"(git\+https://github\.com/JasperHG90/kmctl)(@v\d+\.\d+\.\d+(?:(?:a|b|rc)\d+)?)?"
)
_USES = re.compile(r"^(\s*- uses: JasperHG90/kmctl)@\S+$", re.MULTILINE)
# One top-level ``version:`` line, rewritten as text so comments and layout stay;
# pyproject.toml's [tool.hatch.version] reads the same line.
_APM_VERSION = re.compile(r"^(version: )(.*)$", re.MULTILINE)
# The ``default:`` line of the top-level ``kmctl_ref:`` question, past its
# indented help lines.
_COPIER_DEFAULT = re.compile(
    r"^(kmctl_ref:\n(?:(?!\S).*\n)*?  default: )\S+$", re.MULTILINE
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


def manifest_version(repo: Path) -> str:
    """Return the version ``apm/apm.yml`` declares, whatever the other apm.yml files hold.

    Raises
    ------
    ReleaseRefused
        When ``apm/apm.yml`` is missing or has no version.
    """
    version = _apm_version(repo / MANIFEST)
    if version is None:
        raise ReleaseRefused(f"{MANIFEST} has no top-level version: line; restore it")
    return version


def current(repo: Path) -> str:
    """Return the version ``apm/apm.yml`` declares, once every copy agrees.

    Raises
    ------
    ReleaseRefused
        When ``apm/apm.yml`` has no version, or another file in ``APM_FILES``
        is missing or holds another version.
    """
    version = manifest_version(repo)
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


def set_version(repo: Path, version_text: str) -> list[Path]:
    """Write the version into the four apm.yml files, pin the docs, the hook's hints and copier.yml's default.

    Nothing is written unless the version is valid, all six install lines are
    found, each apm.yml has a ``version:`` line, ``copier.yml`` has a
    ``kmctl_ref`` default and ``HOOKS`` has its two install hints. ``APM_DOC``'s install line
    is pinned too; its "Older installs" example keeps the version it shows.

    Returns
    -------
    list[Path]
        The repo-relative paths written.

    Raises
    ------
    ReleaseRefused
        When the version is malformed, the docs hold fewer than six install
        lines, an apm.yml has no ``version:``, copier.yml has no
        ``kmctl_ref`` default, or ``HOOKS`` lacks an install hint.
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
    docs[APM_DOC], _ = pin_docs((repo / APM_DOC).read_text(), version)
    apm: dict[Path, str] = {}
    for rel in APM_FILES:
        apm[rel], count = _APM_VERSION.subn(
            rf"\g<1>{version}", (repo / rel).read_text(), count=1
        )
        if count != 1:
            raise ReleaseRefused(f"{rel} has no top-level version: line; restore it")
    copier, count = _COPIER_DEFAULT.subn(
        rf"\g<1>v{version}", (repo / COPIER).read_text(), count=1
    )
    if count != 1:
        raise ReleaseRefused(
            f"{COPIER} has no kmctl_ref question with a default: line; restore it"
        )
    hooks, count = _HOOK_INSTALL.subn(rf"\g<1>@v{version}", (repo / HOOKS).read_text())
    if count != HOOK_HINTS:
        raise ReleaseRefused(
            f"found {count} of the {HOOK_HINTS} install hints in {HOOKS}; restore the missing one"
        )
    for rel, text in {**apm, **docs, COPIER: copier, HOOKS: hooks}.items():
        (repo / rel).write_text(text)
    return [*APM_FILES, *DOC_FILES, APM_DOC, COPIER, HOOKS]


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
        help="print apm/apm.yml's version; refuse when another apm.yml differs",
    )
    p_man = sub.add_parser(
        "manifest",
        help="print apm/apm.yml's version alone; refuse only when it has none",
    )
    p_set = sub.add_parser(
        "set",
        help="write the version into the four apm.yml files, pin the docs, the hook's install hints and copier.yml's kmctl_ref",
    )
    p_set.add_argument("version", help="the release version, e.g. 0.2.0 or 0.2.0rc1")
    p_cmp = sub.add_parser("compare", help="print raised, same, lowered or skip")
    p_cmp.add_argument("old", help="the version before, or an empty string for none")
    p_cmp.add_argument("new", help="the version after")
    p_pre = sub.add_parser(
        "is-prerelease", help="exit 0 for an a, b or rc version, else 1"
    )
    p_pre.add_argument("version", help="the version to test, e.g. 0.2.0rc1")
    for p in (p_cur, p_man, p_set, p_cmp, p_pre):
        p.add_argument("--repo", type=Path, default=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    repo: Path = args.repo.resolve()
    try:
        if args.cmd == "current":
            print(current(repo))
        elif args.cmd == "manifest":
            print(manifest_version(repo))
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
