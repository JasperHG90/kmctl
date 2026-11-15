# /// script
# requires-python = ">=3.12"
# dependencies = ["packaging"]
# ///
"""The release workflows' helper: read, set and compare the release version (ADR 0012).

Usage::

    uv run scripts/release.py [--package kmctl|kmaudit] current
    uv run scripts/release.py [--package kmctl|kmaudit] manifest
    uv run scripts/release.py [--package kmctl|kmaudit] set VERSION
    uv run scripts/release.py [--package kmctl|kmaudit] tag VERSION
    uv run scripts/release.py compare OLD NEW
    uv run scripts/release.py is-prerelease VERSION

``--package`` picks the package, kmctl by default. Each has its own version
source and tag family, each in its own APM package's apm.yml (ADR 0045):
kmctl's is described below and tags ``vX.Y.Z``; kmaudit's is
``packages/kmaudit/apm/apm.yml``, which its pyproject reads, and tags
``kmaudit-vX.Y.Z``. For kmaudit, ``current`` and ``manifest`` print that
file's version and ``set`` writes it there and into its Claude Code
sub-package's apm.yml, pins the MCP server that apm.yml declares, the
install lines in ``packages/kmaudit/README.md`` and the ``kmaudit[tracing]``
line in ``packages/kmaudit/docs/commands.md`` to the tag. ``tag`` prints a version's tag.

``packages/kmctl/apm/apm.yml``, kmctl's APM package, carries the one version,
and ``packages/kmctl/pyproject.toml`` reads it from there (ADR 0014). APM needs a ``version:`` in
each apm.yml, so ``set`` writes it into every file in ``APM_FILES``;
``current`` refuses when one differs. ``manifest`` prints that apm.yml's
version alone, for ``release-tag.yml``'s read of the commit before a push,
where an older commit's copies may disagree; on a commit from before the
move it reads ``apm/apm.yml`` instead (``OLD_MANIFEST``). ``set`` also points the six install lines in the docs, and the
APM how-to's CLI install line, at the tag ``vVERSION``, each kmctl install
line building from ``packages/kmctl`` (ADR 0044), and moves the starter
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

#: The one version source, which packages/kmctl/pyproject.toml's [tool.hatch.version] reads.
MANIFEST = Path("packages/kmctl/apm/apm.yml")
#: Where ``MANIFEST`` was before ADR 0045, which ``manifest`` reads on an older commit.
OLD_MANIFEST = Path("apm/apm.yml")
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
    Path("packages/kmctl/apm/claude/apm.yml"),
    Path("packages/kmctl/apm/antigravity/apm.yml"),
)
#: The APM how-to, whose install line ``set`` pins with the others.
APM_DOC = Path("docs/how-to/install-kmctl-with-apm.md")
#: The starter template's questions, whose ``kmctl_ref`` default ``set`` moves.
COPIER = Path("copier.yml")
#: The Claude Code hook, whose two install hints ``set`` points at the release tag.
HOOKS = Path("packages/kmctl/apm/claude/.apm/hooks/hooks.json")
#: How many install hints ``HOOKS`` holds.
HOOK_HINTS = 2
#: The folder releases after ``LAST_ROOT_RELEASE`` build kmctl from (ADR 0044);
#: ``set`` writes it after the tag on every install line and hint, for those
#: releases only.
SUBDIRECTORY = "#subdirectory=packages/kmctl"
#: The last release built from the repository root, as ``kmctl.plugin`` names it.
LAST_ROOT_RELEASE = "v0.12.2"
_INSTALL = re.compile(
    r"^(\s*uv tool install git\+https://github\.com/JasperHG90/kmctl)(@[^\s#]+)?"
    r"(#subdirectory=packages/kmctl)?$",
    re.MULTILINE,
)
# An install hint in the hook's command, with or without a release tag and
# the subdirectory; the tag stops before the full stop that ends the second hint.
_HOOK_INSTALL = re.compile(
    r"(git\+https://github\.com/JasperHG90/kmctl)(@v\d+\.\d+\.\d+(?:(?:a|b|rc)\d+)?)?"
    r"(#subdirectory=packages/kmctl)?"
)
_USES = re.compile(r"^(\s*- uses: JasperHG90/kmctl)@\S+$", re.MULTILINE)
# One top-level ``version:`` line, rewritten as text so comments and layout stay;
# packages/kmctl/pyproject.toml's [tool.hatch.version] reads the same line.
_APM_VERSION = re.compile(r"^(version: )(.*)$", re.MULTILINE)
# The ``default:`` line of the top-level ``kmctl_ref:`` question, past its
# indented help lines.
_COPIER_DEFAULT = re.compile(
    r"^(kmctl_ref:\n(?:(?!\S).*\n)*?  default: )\S+$", re.MULTILINE
)


#: The packages a release can name, and each one's tag prefix.
TAG_PREFIX = {"kmctl": "v", "kmaudit": "kmaudit-v"}
#: kmaudit's one version source, its APM package, which packages/kmaudit/pyproject.toml reads.
KMAUDIT_MANIFEST = Path("packages/kmaudit/apm/apm.yml")
#: kmaudit's Claude Code sub-package, whose version ``set --package kmaudit`` writes too.
KMAUDIT_CLAUDE = Path("packages/kmaudit/apm/claude/apm.yml")
#: kmaudit's README, whose install line ``set --package kmaudit`` pins.
KMAUDIT_README = Path("packages/kmaudit/README.md")
#: kmaudit's commands reference, whose ``kmaudit[tracing]`` install line
#: ``set --package kmaudit`` pins too.
KMAUDIT_DOCS = Path("packages/kmaudit/docs/commands.md")
# kmaudit's install line, with or without a tag before its subdirectory.
_KMAUDIT_INSTALL = re.compile(
    r"(git\+https://github\.com/JasperHG90/kmctl)(@[^\s#']+)?(#subdirectory=packages/kmaudit)"
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
    """Return the version ``MANIFEST`` declares, whatever the other apm.yml files hold.

    A commit from before ADR 0045 has no ``MANIFEST``, so its ``OLD_MANIFEST``
    is read instead.

    Raises
    ------
    ReleaseRefused
        When the apm.yml it reads is missing or has no version.
    """
    path = MANIFEST if (repo / MANIFEST).is_file() else OLD_MANIFEST
    version = _apm_version(repo / path)
    if version is None:
        raise ReleaseRefused(f"{path} has no top-level version: line; restore it")
    return version


def kmaudit_version(repo: Path) -> str:
    """Return the version ``packages/kmaudit/apm/apm.yml`` declares.

    Raises
    ------
    ReleaseRefused
        When the file is missing or has no top-level ``version:`` line.
    """
    version = _apm_version(repo / KMAUDIT_MANIFEST)
    if version is None:
        raise ReleaseRefused(
            f"{KMAUDIT_MANIFEST} is missing or has no top-level version: line; restore it"
        )
    return version


def set_kmaudit_version(repo: Path, version_text: str) -> list[Path]:
    """Write the version into kmaudit's two apm.yml files and pin its MCP server and install lines to the tag.

    Nothing is written unless the version is valid, both apm.yml files have
    a ``version:`` line, the package's apm.yml declares the MCP server from
    kmaudit's git URL, the README holds an install line and the commands
    reference holds its ``kmaudit[tracing]`` install line.

    Returns
    -------
    list[Path]
        The repo-relative paths written.

    Raises
    ------
    ReleaseRefused
        When the version is malformed, an apm.yml is missing or has no
        ``version:`` line, the package's apm.yml has no MCP server install line, the README has
        no install line or the commands reference has no ``kmaudit[tracing]``
        install line.
    """
    version = str(parse_release(version_text))
    manifest, count = _APM_VERSION.subn(
        rf"\g<1>{version}", (repo / KMAUDIT_MANIFEST).read_text(), count=1
    )
    if count != 1:
        raise ReleaseRefused(
            f"{KMAUDIT_MANIFEST} has no top-level version: line; restore it"
        )
    manifest, count = _KMAUDIT_INSTALL.subn(rf"\g<1>@kmaudit-v{version}\g<3>", manifest)
    if count == 0:
        raise ReleaseRefused(
            f"{KMAUDIT_MANIFEST} declares no kmaudit MCP server from "
            "git+https://github.com/JasperHG90/kmctl; restore its uvx --from args"
        )
    claude_path = repo / KMAUDIT_CLAUDE
    claude, count = _APM_VERSION.subn(
        rf"\g<1>{version}",
        claude_path.read_text() if claude_path.is_file() else "",
        count=1,
    )
    if count != 1:
        raise ReleaseRefused(
            f"{KMAUDIT_CLAUDE} is missing or has no top-level version: line; restore it"
        )
    readme, count = _KMAUDIT_INSTALL.subn(
        rf"\g<1>@kmaudit-v{version}\g<3>", (repo / KMAUDIT_README).read_text()
    )
    if count == 0:
        raise ReleaseRefused(
            f"{KMAUDIT_README} has no kmaudit install line; restore the uv tool install line"
        )
    docs, count = _KMAUDIT_INSTALL.subn(
        rf"\g<1>@kmaudit-v{version}\g<3>", (repo / KMAUDIT_DOCS).read_text()
    )
    if "kmaudit[tracing] @" not in docs or count == 0:
        raise ReleaseRefused(
            f"{KMAUDIT_DOCS} has no kmaudit[tracing] install line; restore the "
            "uv tool install line in its tracing section"
        )
    (repo / KMAUDIT_MANIFEST).write_text(manifest)
    (repo / KMAUDIT_CLAUDE).write_text(claude)
    (repo / KMAUDIT_README).write_text(readme)
    (repo / KMAUDIT_DOCS).write_text(docs)
    return [KMAUDIT_MANIFEST, KMAUDIT_CLAUDE, KMAUDIT_README, KMAUDIT_DOCS]


def tag(package: str, version_text: str) -> str:
    """Return the tag that releases ``version_text`` of ``package``, e.g. ``kmaudit-v0.2.0``."""
    return f"{TAG_PREFIX[package]}{parse_release(version_text)}"


def current(repo: Path) -> str:
    """Return the version ``MANIFEST`` declares, once every copy agrees.

    Raises
    ------
    ReleaseRefused
        When ``MANIFEST`` has no version, or another file in ``APM_FILES``
        is missing or holds another version.
    """
    version = _apm_version(repo / MANIFEST)
    if version is None:
        raise ReleaseRefused(f"{MANIFEST} has no top-level version: line; restore it")
    for rel in APM_FILES:
        found = _apm_version(repo / rel)
        if found != version:
            raise ReleaseRefused(
                f"{rel} has version {found or 'none'} but {MANIFEST} has {version}; "
                f"run scripts/release.py set {version}"
            )
    return version


def subdirectory(version: str) -> str:
    """``SUBDIRECTORY`` for a release after ``LAST_ROOT_RELEASE``, else empty."""
    if Version(version) <= Version(LAST_ROOT_RELEASE.removeprefix("v")):
        return ""
    return SUBDIRECTORY


def pin_docs(text: str, version: str) -> tuple[str, int]:
    """Point each install line in ``text`` at the tag ``v<version>``.

    The line builds from packages/kmctl only for a release after
    ``LAST_ROOT_RELEASE`` (``subdirectory``).

    Returns
    -------
    tuple[str, int]
        The new text and how many lines it pinned.
    """
    text, installs = _INSTALL.subn(rf"\g<1>@v{version}{subdirectory(version)}", text)
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
    hooks, count = _HOOK_INSTALL.subn(
        rf"\g<1>@v{version}{subdirectory(version)}", (repo / HOOKS).read_text()
    )
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
    parser.add_argument(
        "--package",
        choices=tuple(TAG_PREFIX),
        default="kmctl",
        help="the package to release (default kmctl); each reads packages/<package>/apm/apm.yml",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_cur = sub.add_parser(
        "current",
        help="print the version in packages/<package>/apm/apm.yml (kmctl: refusing when another apm.yml differs)",
    )
    p_man = sub.add_parser(
        "manifest",
        help="print the version source's version alone (kmctl: packages/kmctl/apm/apm.yml, or apm/apm.yml on a commit from before it moved); refuse only when it has none",
    )
    p_set = sub.add_parser(
        "set",
        help="kmctl: write the version into the four apm.yml files, pin the docs, the hook's install hints and copier.yml's kmctl_ref; kmaudit: write packages/kmaudit/apm/apm.yml and apm/claude/apm.yml and pin its MCP server and the install lines in its README and docs/commands.md",
    )
    p_set.add_argument("version", help="the release version, e.g. 0.2.0 or 0.2.0rc1")
    p_tag = sub.add_parser(
        "tag", help="print the package's tag for a version: vX.Y.Z or kmaudit-vX.Y.Z"
    )
    p_tag.add_argument("version", help="the release version, e.g. 0.2.0")
    p_cmp = sub.add_parser("compare", help="print raised, same, lowered or skip")
    p_cmp.add_argument("old", help="the version before, or an empty string for none")
    p_cmp.add_argument("new", help="the version after")
    p_pre = sub.add_parser(
        "is-prerelease", help="exit 0 for an a, b or rc version, else 1"
    )
    p_pre.add_argument("version", help="the version to test, e.g. 0.2.0rc1")
    for p in (p_cur, p_man, p_set, p_tag, p_cmp, p_pre):
        p.add_argument("--repo", type=Path, default=argparse.SUPPRESS)
        p.add_argument(
            "--package", choices=tuple(TAG_PREFIX), default=argparse.SUPPRESS
        )
    args = parser.parse_args(argv)
    repo: Path = args.repo.resolve()
    try:
        kmaudit = args.package == "kmaudit"
        if args.cmd == "current":
            print(kmaudit_version(repo) if kmaudit else current(repo))
        elif args.cmd == "manifest":
            print(kmaudit_version(repo) if kmaudit else manifest_version(repo))
        elif args.cmd == "set":
            written = (
                set_kmaudit_version(repo, args.version)
                if kmaudit
                else set_version(repo, args.version)
            )
            for path in written:
                print(f"wrote {path}")
        elif args.cmd == "tag":
            print(tag(args.package, args.version))
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
