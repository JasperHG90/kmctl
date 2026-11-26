"""Read file versions out of git history in one call, for kmctl review due and the summary check."""

import subprocess
from pathlib import Path


def show(root: Path, specs: list[str]) -> list[str | None]:
    """The text of each ``REV:./PATH`` in ``specs`` from one ``git cat-file --batch``; None when missing."""
    if not specs:
        return []
    proc = subprocess.run(
        ["git", "-C", str(root), "cat-file", "--batch"],
        input="".join(spec + "\n" for spec in specs).encode(),
        capture_output=True,
        check=False,
    )
    data, out, i = proc.stdout, [], 0
    for _ in specs:
        nl = data.find(b"\n", i)
        header = data[i:nl]
        i = nl + 1
        # "SPEC missing" (or "SPEC ambiguous") echoes the spec, which may hold
        # spaces, so it is told apart by its end, not by counting fields.
        if nl == -1 or header.endswith((b" missing", b" ambiguous")):
            out.append(None)
            continue
        size = int(header.split()[2])
        out.append(data[i : i + size].decode("utf-8", errors="replace"))
        i += size + 1
    return out
