"""Which package a repository path belongs to, for its release notes (ADR 0012).

Usage::

    git diff --name-only A B | python3 scripts/release_paths.py kmctl|kmaudit

kmaudit owns ``packages/kmaudit/`` and its pages in ``docs/``, whose file
names start with ``kmaudit-``. kmctl owns ``packages/kmctl/`` and every
other path outside ``packages/``, except the repository's bookkeeping, which ships
in no package: the loop's state (``.loop/``), the knowledge bundle
(``.okf/``), the repository's own agent rules (``.claude/``) and the shared
``uv.lock``. ``release_notes.py`` lists a commit in a package's notes when the
package owns one of the paths it touches, and release-tag names a late
commit the same way, through the command: it reads paths on stdin and exits
0 when the package owns any of them, 1 when it owns none, 2 for an unknown
package. Standard library only, so release-tag runs it with no install.
"""

from __future__ import annotations

import sys

PACKAGES = ("kmctl", "kmaudit")
#: Folders that ship in no package.
BOOKKEEPING = (".loop/", ".okf/", ".claude/")
#: Files that ship in no package.
BOOKKEEPING_FILES = ("uv.lock",)
#: The start of a kmaudit page's file name in ``docs/``.
KMAUDIT_DOCS_PREFIX = "kmaudit-"


def owns(package: str, path: str) -> bool:
    """Whether ``path`` belongs to ``package``; bookkeeping belongs to neither."""
    if path.startswith(BOOKKEEPING) or path in BOOKKEEPING_FILES:
        return False
    kmaudit_doc = path.startswith("docs/") and path.rsplit("/", 1)[-1].startswith(
        KMAUDIT_DOCS_PREFIX
    )
    if package == "kmaudit":
        return path.startswith("packages/kmaudit/") or kmaudit_doc
    if kmaudit_doc:
        return False
    return path.startswith("packages/kmctl/") or not path.startswith("packages/")


def main(argv: list[str] | None = None) -> int:
    """Exit 0 when the package in ``argv`` owns a path on stdin, 1 when none, 2 on misuse."""
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1 or args[0] not in PACKAGES:
        print(
            f"release_paths: name one package, {' or '.join(PACKAGES)}; paths come on stdin",
            file=sys.stderr,
        )
        return 2
    # Read every path before deciding: the caller pipes git diff in under
    # pipefail, and stopping early would kill the writer with SIGPIPE.
    paths = [p.strip() for p in sys.stdin.read().splitlines() if p.strip()]
    return 0 if any(owns(args[0], p) for p in paths) else 1


if __name__ == "__main__":
    sys.exit(main())
