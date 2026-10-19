# /// script
# requires-python = ">=3.12"
# dependencies = ["packaging"]
# ///
"""Print a release's notes from main's first-parent history (ADR 0012).

Usage::

    uv run scripts/release_notes.py TAG

Work lands on main as ``Merge loop/SLUG: SUMMARY`` commits, not pull
requests, so GitHub's generated notes list only the release pull request.
This script reads main's first-parent history between the ``v*`` tag before
``TAG`` and ``TAG``: each ticket merge becomes a bullet under What changed,
each other commit a bullet under Other changes. Loop state commits, release
commits, release pull request merges, branch syncs and manual placeholder
commits are left out. The bullets fill ``.github/release-notes.md``, whose
``$changes``, ``$other``, ``$tag`` and ``$compare`` are replaced.
``release-tag.yml`` publishes the output as the GitHub Release's body.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from string import Template

from packaging.version import InvalidVersion, Version

#: The notes' layout, filled by ``render``; read from this checkout, so notes
#: written for an old tag use today's layout.
TEMPLATE = Path(__file__).resolve().parents[1] / ".github" / "release-notes.md"
REPO_URL = "https://github.com/JasperHG90/kmctl"
_TICKET = re.compile(r"^Merge loop/(?P<slug>[a-z0-9-]+): (?P<summary>.+)$")
_SKIP = re.compile(
    r"^(loop: |release: "
    r"|Merge pull request #\d+ from \S+/release/v"
    r"|Merge remote-tracking branch "
    r"|Merge (branch '?main'? |main )into "
    r"|operator: manual commits?$"
    r"|chore; manual commits?$)"
)
_RELEASE_TAG = re.compile(r"^v\d+\.\d+\.\d+((a|b|rc)\d+)?$")


class NotesRefused(Exception):
    """The notes cannot be written; the message names the fix."""


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout


def previous_tag(repo: Path, tag: str) -> str | None:
    """Return the highest release tag below ``tag``, or None for the first release."""
    try:
        version = Version(tag)
    except InvalidVersion as exc:
        raise NotesRefused(f"{tag!r} is not a release tag; use e.g. v0.2.0") from exc
    older = [
        Version(t)
        for t in _git(repo, "tag", "--list", "v*").split()
        if _RELEASE_TAG.match(t) and Version(t) < version
    ]
    return f"v{max(older)}" if older else None


def render(repo: Path, tag: str) -> str:
    """Return the notes for ``tag``: the template filled from the history since the tag before.

    Raises
    ------
    NotesRefused
        When ``tag`` is not a tag in ``repo``.
    """
    if subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "-q", "--verify", f"refs/tags/{tag}"],
        capture_output=True,
        check=False,
    ).returncode:
        raise NotesRefused(f"no tag {tag}; push it first, or check the name")
    previous = previous_tag(repo, tag)
    span = f"{previous}..{tag}" if previous else tag
    changes: list[str] = []
    other: list[str] = []
    for subject in _git(
        repo, "log", "--first-parent", "--format=%s", span
    ).splitlines():
        if ticket := _TICKET.match(subject):
            changes.append(f"- {ticket['summary']} (`{ticket['slug']}`)")
        elif not _SKIP.match(subject):
            other.append(f"- {subject}")
    compare = (
        f"**Full diff**: {REPO_URL}/compare/{previous}...{tag}"
        if previous
        else "First release."
    )
    return Template(TEMPLATE.read_text()).substitute(
        changes="\n".join(reversed(changes)) or "None.",
        other="\n".join(reversed(other)) or "None.",
        tag=tag,
        compare=compare,
    )


def main(argv: list[str] | None = None) -> int:
    """Print the notes and map a refusal to exit 1."""
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0] if __doc__ else None
    )
    parser.add_argument(
        "--repo", type=Path, default=Path.cwd(), help="the repository root"
    )
    parser.add_argument("tag", help="the release tag, e.g. v0.2.0")
    args = parser.parse_args(argv)
    try:
        notes = render(args.repo.resolve(), args.tag)
    except NotesRefused as exc:
        print(f"release_notes: refused: {exc}", file=sys.stderr)
        return 1
    print(notes, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
