"""Split main's history over a fixed range into units and label the ones that added a decision.

A unit is one ticket merge, one pull request with no ticket merges, or one
plain commit, as ``scripts/release_notes.py`` walks main's first-parent line
(syncs and ticket-carrying pull requests expanded). Loop state, release and
placeholder commits are left out. A unit is positive when it adds a decision
record, ``.okf/decisions/NNNN-*.md``, whose number its first parent lacks.

Usage::

    python3 scripts/units.py REPO > results/units.jsonl
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

#: The range measured: after ADRs 0007 to 0009, up to the badges merge.
START = "14799749"
TIP = "ee87e883"
DECISION = re.compile(r"^\.okf/decisions/(\d{4})-[^/]+\.md$")


def git(repo: Path, *args: str) -> str:
    """Run git in ``repo`` and return its stdout."""
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout


def changes(repo: Path, sha: str, parent: str | None) -> list[tuple[str, str]]:
    """The (status, path) pairs ``sha`` changes against ``parent``, renames as their new path."""
    if parent is None:
        out = git(repo, "diff-tree", "--root", "-r", "--name-status", "--no-commit-id", sha)
    else:
        out = git(repo, "diff", "--name-status", "-M", parent, sha)
    pairs = []
    for line in out.splitlines():
        parts = line.split("\t")
        pairs.append((parts[0][0], parts[-1]))
    return pairs


def numbers(repo: Path, ref: str) -> set[str]:
    """The decision numbers in ``ref``'s tree."""
    names = git(repo, "ls-tree", "--name-only", f"{ref}:.okf/decisions").split()
    return {n[:4] for n in names if re.match(r"\d{4}-", n)}


def main() -> int:
    """Print one JSON line per unit in the range, oldest first."""
    repo = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(repo / "scripts"))
    from release_notes import _SKIP, _TICKET, _first_parent

    units = []
    for sha, parents, subject, body in _first_parent(repo, TIP, [START]):
        if _SKIP.match(subject):
            continue
        parent = parents[0] if parents else None
        pairs = changes(repo, sha, parent)
        before = numbers(repo, parent) if parent else set()
        added = sorted(
            {
                m.group(1)
                for status, path in pairs
                if status in "AR" and (m := DECISION.match(path))
            }
            - before
        )
        ticket = _TICKET.match(subject)
        units.append(
            {
                "sha": sha,
                "parent": parent,
                "subject": subject,
                "body": body.strip(),
                "slug": ticket["slug"] if ticket else None,
                "files": [[s, p] for s, p in pairs],
                "adds_decisions": added,
            }
        )
    for unit in reversed(units):
        print(json.dumps(unit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
