# /// script
# requires-python = ">=3.12"
# dependencies = ["packaging"]
# ///
"""Print a release's notes from main's first-parent history (ADR 0012).

Usage::

    uv run scripts/release_notes.py TAG
    uv run scripts/release_notes.py --package kmctl|kmaudit TAG [--ref REF] [--out FILE]

``--package`` names the package the tag releases: kmctl's tags are ``vX.Y.Z``
and kmaudit's ``kmaudit-vX.Y.Z``. Its notes start at that family's tag before
``TAG`` and list only commits whose diff against their first parent touches
the package's paths: kmaudit owns ``packages/kmaudit/``, and kmctl owns
``packages/kmctl/`` and every path outside ``packages/``. Without
``--package``, the tag is a kmctl tag and every commit counts, as for the
releases before the split. ``--ref`` drafts the notes for a tag not pushed
yet, reading the history up to ``REF``; ``release.yml`` drafts them so before
the version pull request. ``--out`` writes the notes to ``FILE`` instead of
stdout.

Most work lands on main as ``Merge loop/SLUG: SUMMARY`` commits, not pull
requests, so GitHub's generated notes list only the release pull request.
This script reads main's first-parent history between the previous tag of
``TAG``'s family and ``TAG``, or ``REF`` with ``--ref``. Pull requests merged on GitHub reach that line through a
sync merge such as ``Merge remote-tracking branch 'origin/main'``, so the
script also reads the first-parent history each sync brought in. Each ticket
merge becomes a bullet under What changed, and so does each pull request
merge, with the title GitHub wrote in its body. Each other commit becomes a
bullet under Other changes, unless a listed pull request has the same title.
Loop state commits, release commits, release pull request merges, the syncs
themselves and manual placeholder commits are left out. The bullets fill
``.github/release-notes.md`` (kmaudit's: ``.github/release-notes-kmaudit.md``),
whose ``$changes``, ``$other``, ``$tag`` and ``$compare`` are replaced.
``release.yml`` commits the draft as ``.github/release-notes/TAG.md`` in the
version pull request, and ``release-tag.yml`` publishes that file as the
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
#: kmaudit's layout, with its own install line.
KMAUDIT_TEMPLATE = TEMPLATE.with_name("release-notes-kmaudit.md")
#: Each package's tag prefix and notes layout.
FAMILIES = {"kmctl": ("v", TEMPLATE), "kmaudit": ("kmaudit-v", KMAUDIT_TEMPLATE)}
REPO_URL = "https://github.com/JasperHG90/kmctl"
_TICKET = re.compile(r"^Merge loop/(?P<slug>[a-z0-9-]+): (?P<summary>.+)$")
_PULL = re.compile(r"^Merge pull request #(?P<number>\d+) from \S+$")
_SYNC = re.compile(r"^Merge remote-tracking branch ")
_SKIP = re.compile(
    r"^(loop: |release: "
    r"|Merge pull request #\d+ from \S+/release/(kmaudit-)?v"
    r"|Merge remote-tracking branch "
    r"|Merge (branch '?main'? |main )into "
    r"|operator: manual commits?$"
    r"|chore; manual commits?$)"
)
_RELEASE_VERSION = r"\d+\.\d+\.\d+((a|b|rc)\d+)?$"


class NotesRefused(Exception):
    """The notes cannot be written; the message names the fix."""


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout


def owns(package: str, path: str) -> bool:
    """Whether ``path`` belongs to ``package``: kmaudit owns ``packages/kmaudit/``; kmctl owns ``packages/kmctl/`` and every path outside ``packages/``."""
    if package == "kmaudit":
        return path.startswith("packages/kmaudit/")
    return path.startswith("packages/kmctl/") or not path.startswith("packages/")


def _touched(repo: Path, sha: str, parents: list[str]) -> list[str]:
    """The paths commit ``sha`` changes against its first parent, or all it holds for a root commit."""
    if parents:
        return _git(repo, "diff", "--name-only", parents[0], sha).split("\n")
    return _git(
        repo, "diff-tree", "--root", "-r", "--name-only", "--no-commit-id", sha
    ).split("\n")


def _first_parent(
    repo: Path, tip: str, exclude: list[str]
) -> Iterator[tuple[str, list[str], str, str]]:
    """Yield the hash, parents, subject and body of each commit on ``tip``'s first-parent line, newest first.

    The walk stops at commits that any of ``exclude`` reaches. Each sync merge
    is followed by the commits it brought in, read the same way, so a pull
    request merged on GitHub sits where main took it in and is listed once.
    """
    log = _git(
        repo,
        "log",
        "--first-parent",
        "--format=%H%x1f%P%x1f%s%x1f%b%x1e",
        tip,
        *(f"^{ref}" for ref in exclude),
    )
    for record in log.split("\x1e")[:-1]:
        sha, parents, subject, body = record.lstrip("\n").split("\x1f")
        yield sha, parents.split(), subject, body
        if _SYNC.match(subject) and len(parents.split()) == 2:
            first, second = parents.split()
            yield from _first_parent(repo, second, [*exclude, first])


def previous_tag(repo: Path, tag: str, prefix: str = "v") -> str | None:
    """Return the highest tag of ``prefix``'s family below ``tag``, or None for the first release."""
    pattern = re.compile(rf"^{re.escape(prefix)}{_RELEASE_VERSION}")
    try:
        if not tag.startswith(prefix):
            raise InvalidVersion(tag)
        version = Version(tag.removeprefix(prefix))
    except InvalidVersion as exc:
        raise NotesRefused(
            f"{tag!r} is not a {prefix}X.Y.Z release tag; use e.g. {prefix}0.2.0"
        ) from exc
    older = [
        Version(t.removeprefix(prefix))
        for t in _git(repo, "tag", "--list", f"{prefix}*").split()
        if pattern.match(t) and Version(t.removeprefix(prefix)) < version
    ]
    return f"{prefix}{max(older)}" if older else None


def _resolves(repo: Path, ref: str) -> bool:
    return not subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "-q", "--verify", f"{ref}^{{commit}}"],
        capture_output=True,
        check=False,
    ).returncode


def render(
    repo: Path, tag: str, package: str | None = None, ref: str | None = None
) -> str:
    """Return the notes for ``tag``: the template filled from the history since the tag before.

    Parameters
    ----------
    repo :
        The repository to read.
    tag :
        The release tag, e.g. ``v0.2.0`` or ``kmaudit-v0.2.0``.
    package :
        The package ``tag`` releases; only commits touching its paths count.
        ``None`` reads ``tag`` as a kmctl tag and counts every commit.
    ref :
        Read the history up to ``ref`` instead of ``tag``, which then need
        not exist yet.

    Raises
    ------
    NotesRefused
        When ``tag`` is not a tag of the package's family, or is not a tag in
        ``repo`` and no ``ref`` is given, or ``ref`` names no commit.
    """
    prefix, template = FAMILIES[package or "kmctl"]
    previous = previous_tag(repo, tag, prefix)
    if ref is None:
        if not _resolves(repo, f"refs/tags/{tag}"):
            raise NotesRefused(f"no tag {tag}; push it first, or check the name")
    elif not _resolves(repo, ref):
        raise NotesRefused(f"{ref} names no commit; check the --ref")
    changes: list[str] = []
    other: list[str] = []
    titles: set[str] = set()
    walk = _first_parent(repo, ref or tag, [previous] if previous else [])
    for sha, parents, subject, body in walk:
        if _SKIP.match(subject):
            continue
        if package and not any(
            owns(package, path) for path in _touched(repo, sha, parents) if path
        ):
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
    return Template(template.read_text()).substitute(
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
    parser.add_argument(
        "--package",
        choices=tuple(FAMILIES),
        help="list only commits touching this package's paths, from its family's previous tag",
    )
    parser.add_argument(
        "--ref",
        help="draft the notes up to this commit, for a tag not pushed yet (e.g. HEAD)",
    )
    parser.add_argument(
        "--out", type=Path, help="write the notes to this file instead of stdout"
    )
    parser.add_argument(
        "tag",
        help="the release tag, e.g. v0.2.0 or kmaudit-v0.2.0 with --package kmaudit",
    )
    args = parser.parse_args(argv)
    try:
        notes = render(args.repo.resolve(), args.tag, args.package, args.ref)
    except NotesRefused as exc:
        print(f"release_notes: refused: {exc}", file=sys.stderr)
        return 1
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(notes)
    else:
        print(notes, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
