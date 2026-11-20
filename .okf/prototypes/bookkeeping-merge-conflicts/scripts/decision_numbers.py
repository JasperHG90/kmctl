#!/usr/bin/env python3
"""Count how often two pull requests that both add a decision record are open at the same time.

`kmctl new decision` takes the next free number in the checkout. Two branches that both add
a decision therefore take the same number, and git reports no conflict, because the two
files have different names.

Run from the repository root; it needs the GitHub CLI:

    python3 .okf/prototypes/bookkeeping-merge-conflicts/scripts/decision_numbers.py

It prints the counts in the README. A closed pull request that was never merged is left out.
"""

from __future__ import annotations

import itertools
import json
import re
import subprocess
import sys

RECORD = re.compile(r"^\.okf/decisions/(\d{4})-[^/]+\.md$")


def gh(*args: str) -> str:
    done = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)
    if done.returncode != 0:
        sys.exit(f"gh {' '.join(args)} failed: {done.stderr.strip()}")
    return done.stdout


def main() -> int:
    pulls = [
        p
        for p in json.loads(
            gh(
                "pr",
                "list",
                "--state",
                "all",
                "--limit",
                "500",
                "--json",
                "number,state,createdAt,mergedAt,files",
            )
        )
        if p["state"] != "CLOSED"
    ]
    rows = []
    for pull in pulls:
        if not any(RECORD.match(f["path"]) for f in pull["files"]):
            continue
        # `gh pr list` does not say whether a file is new, so ask the API for its status.
        files = gh(
            "api",
            f"repos/{{owner}}/{{repo}}/pulls/{pull['number']}/files?per_page=100",
            "--paginate",
            "-q",
            '.[] | select(.status == "added") | .filename',
        )
        numbers = sorted(
            m.group(1) for name in files.splitlines() if (m := RECORD.match(name))
        )
        if numbers:
            rows.append(
                {
                    "number": pull["number"],
                    "state": pull["state"],
                    "from": pull["createdAt"],
                    "to": pull["mergedAt"] or "9999",
                    "records": numbers,
                }
            )

    together = {
        r["number"]
        for a, b in itertools.combinations(rows, 2)
        if a["from"] < b["to"] and b["from"] < a["to"]
        for r in (a, b)
    }
    print(f"Merged or open pull requests: {len(pulls)}")
    print(f"... that add a decision record: {len(rows)}")
    print(
        f"... and were open at the same time as another one that adds a decision record: {len(together)}"
    )
    print(
        "Open now, with the numbers they took: "
        + ", ".join(
            f"#{r['number']} ({', '.join(r['records'])})"
            for r in sorted(rows, key=lambda r: r["number"])
            if r["state"] == "OPEN"
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
