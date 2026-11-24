#!/usr/bin/env python3
"""Git merge driver for .okf/summary.md.

`kmctl summary ack` rewrites the `checked` block in the summary's front matter, so two
branches that both ran it change the same lines and git reports a conflict. This driver
merges that block itself and leaves every other line to git:

- `checked.at` becomes the later of the two times;
- `checked.against` becomes the ids of both sides, sorted.

A change to any other line that git cannot merge stays a conflict, with the usual markers.

Git calls it as `merge_summary.py %O %A %B`: the common ancestor, our version and their
version. It writes the result over our version and exits 0 when the merge is clean.

    git config merge.okf-summary.driver "python3 .okf/prototypes/bookkeeping-merge-conflicts/scripts/merge_summary.py %O %A %B"
    echo ".okf/summary.md merge=okf-summary" >> .gitattributes
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys
import tempfile

PLACEHOLDER = "checked: MERGED-BY-DRIVER\n"
# The `checked:` key and its indented lines, inside the front matter.
BLOCK = re.compile(r"^checked:[^\n]*\n(?:[ \t]+[^\n]*\n)*", re.MULTILINE)


def split(text: str) -> tuple[str, str | None, list[str]]:
    """Return the text with the checked block replaced, its `at` and its `against` ids."""
    end = text.find("\n---\n", 4) if text.startswith("---\n") else -1
    head = text[: end + 1] if end != -1 else ""
    match = BLOCK.search(head)
    if not match:
        return text, None, []
    block = match.group(0)
    at = re.search(r"^[ \t]+at:[ \t]*(\S+)", block, re.MULTILINE)
    against = re.findall(r"^[ \t]+-[ \t]*(\S+)", block, re.MULTILINE)
    return (
        text[: match.start()] + PLACEHOLDER + text[match.end() :],
        at.group(1) if at else None,
        against,
    )


def main() -> int:
    base_path, ours_path, theirs_path = (pathlib.Path(p) for p in sys.argv[1:4])
    base, _, _ = split(base_path.read_text(encoding="utf-8"))
    ours, ours_at, ours_against = split(ours_path.read_text(encoding="utf-8"))
    theirs, theirs_at, theirs_against = split(theirs_path.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory() as tmp:
        names = []
        for name, text in (("ours", ours), ("base", base), ("theirs", theirs)):
            path = pathlib.Path(tmp) / name
            path.write_text(text, encoding="utf-8")
            names.append(str(path))
        done = subprocess.run(
            [
                "git",
                "merge-file",
                "-p",
                "-L",
                "ours",
                "-L",
                "base",
                "-L",
                "theirs",
                *names,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    if done.returncode < 0 or done.returncode > 127:
        return 1  # git merge-file itself failed; leave our version as it is
    merged = done.stdout

    times = [t for t in (ours_at, theirs_at) if t]
    ids = sorted(set(ours_against) | set(theirs_against))
    if times:
        block = (
            f"checked:\n  at: {max(times)}\n  against:"
            + ("".join(f"\n    - {i}" for i in ids) if ids else " []")
            + "\n"
        )
        merged = merged.replace(PLACEHOLDER, block)
    else:
        merged = merged.replace(PLACEHOLDER, "")

    ours_path.write_text(merged, encoding="utf-8")
    return 1 if done.returncode else 0


if __name__ == "__main__":
    sys.exit(main())
