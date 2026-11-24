#!/usr/bin/env python3
"""Count how many merged pull requests would still write to .okf/log.md if it held lifecycle events only.

For each merge on the first-parent history of main, the script reads the lines the merge added
to .okf/log.md and sorts each line by its first word. A line is a lifecycle event when it
records a concept created, renamed, superseded, deprecated, removed, regenerated, accepted or verified
(ADR 0049); any other line is about an edit.

Run from the root of the repository to measure:

    python3 path/to/log_lines.py

It prints counts only, no file names or pull request numbers.
"""

from __future__ import annotations

import re
import subprocess
from collections import Counter

LIFECYCLE = re.compile(
    r"^- (Added|Wrote|Created|Verified|Moved|Renamed|Superseded|Deprecated|Retired|Removed|Deleted|Regenerated)\b"
)
ACCEPTED = re.compile(r"\bto (status )?`?stable`?", re.IGNORECASE)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def is_lifecycle(line: str) -> bool:
    return bool(LIFECYCLE.match(line) or ACCEPTED.search(line))


def main() -> None:
    merges = git("log", "--merges", "--first-parent", "main", "--format=%H").split()
    counts: Counter[str] = Counter()
    for merge in merges:
        diff = git("diff", f"{merge}^1", merge, "--", ".okf/log.md")
        added = [line[1:] for line in diff.splitlines() if line.startswith("+- ")]
        if not added:
            continue
        lifecycle = [line for line in added if is_lifecycle(line)]
        counts["pull requests that wrote to the log"] += 1
        counts["... and still would, with lifecycle events only"] += bool(lifecycle)
        counts["lines added"] += len(added)
        counts["... that are lifecycle events"] += len(lifecycle)
    print(f"merges on main: {len(merges)}")
    for name, value in counts.items():
        print(f"{name}: {value}")


if __name__ == "__main__":
    main()
