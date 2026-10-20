# /// script
# requires-python = ">=3.12"
# dependencies = ["packaging"]
# ///
"""Print a release's notes from main's first-parent history (ADR 0012).

Usage::

    uv run scripts/release_notes.py TAG

Most work lands on main as ``Merge loop/SLUG: SUMMARY`` commits, not pull
requests, so GitHub's generated notes list only the release pull request.
This script reads main's first-parent history between the ``v*`` tag before
``TAG`` and ``TAG``. Pull requests merged on GitHub reach that line through a
sync merge such as ``Merge remote-tracking branch 'origin/main'``, so the
script also reads the first-parent history each sync brought in. Each ticket
merge becomes a bullet under What changed, and so does each pull request
merge, with the title GitHub wrote in its body. Each other commit becomes a
bullet under Other changes, unless a listed pull request has the same title.
Loop state commits, release commits, release pull request merges, the syncs
themselves and manual placeholder commits are left out. The bullets fill
``.github/release-notes.md``, whose ``$changes``, ``$other``, ``$tag`` and
``$compare`` are replaced. ``release-tag.yml`` publishes the output as the
GitHub Release's body.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from string import Template

from packaging.version import InvalidVersion, Version

#: The notes' layout, filled by ``render``; read from this checkout, so notes
#: written for an old tag use today's layout.
TEMPLATE = Path(__file__).resolve().parents[1] / ".github" / "release-notes.md"
REPO_URL = "https://github.com/JasperHG90/kmctl"
_TICKET = re.compile(r"^Merge loop/(?P<slug>[a-z0-9-]+): (?P<summary>.+)$")
_PULL = re.compile(r"^Merge pull request #(?P<number>\d+) from \S+$")
_SYNC = re.compile(r"^Merge remote-tracking branch ")
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


def _first_parent(
    repo: Path, tip: str, exclude: list[str]
) -> Iterator[tuple[str, str]]:
    """Yield the subject and body of each commit on ``tip``'s first-parent line, newest first.

    The walk stops at commits that any of ``exclude`` reaches. Each sync merge
    is followed by the commits it brought in, read the same way, so a pull
    request merged on GitHub sits where main took it in and is listed once.
    """
    log = _git(
        repo,
        "log",
        "--first-parent",
        "--format=%P%x1f%s%x1f%b%x1e",
        tip,
        *(f"^{ref}" for ref in exclude),
    )
    for record in log.split("\x1e")[:-1]:
        parents, subject, body = record.lstrip("\n").split("\x1f")
        yield subject, body
        if _SYNC.match(subject) and len(parents.split()) == 2:
            first, second = parents.split()
            yield from _first_parent(repo, second, [*exclude, first])


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
    changes: list[str] = []
    other: list[str] = []
    titles: set[str] = set()
    for subject, body in _first_parent(repo, tag, [previous] if previous else []):
        if _SKIP.match(subject):
            continue
        if ticket := _TICKET.match(subject):
            changes.append(f"- {ticket['summary']} (`{ticket['slug']}`)")
        elif pull := _PULL.match(subject):
            title = next(
                (ln.strip() for ln in body.splitlines() if ln.strip()), subject
            )
            titles.add(title)
            changes.append(f"- {title} (#{pull['number']})")
        else:
            other.append(subject)
    other = [f"- {subject}" for subject in other if subject not in titles]
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
