"""Count Hermes rewrites with a non-bullet line under What changed.

Reads a spike stdout that prints each rewrite after a '===== TAG run N' line,
and counts lines under '## What changed' that are neither blank, a '- '
bullet, nor an indented continuation of one.
"""
import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text()
runs = re.split(r"^===== (.+)$", text, flags=re.M)[1:]
total = fired = 0
for name, body in zip(runs[::2], runs[1::2]):
    total += 1
    m = re.search(r"^## What changed\n(.*?)(?=^## |\Z)", body, flags=re.M | re.S)
    section = m.group(1) if m else ""
    seen_bullet = False
    stray = []
    for ln in section.splitlines():
        if not ln.strip():
            continue
        if ln.startswith("- "):
            seen_bullet = True
        elif ln[0].isspace() and seen_bullet:
            continue
        else:
            stray.append(ln)
    if stray:
        fired += 1
        print(f"{name}: {stray}")
print(f"rewrites with a stray line under What changed: {fired} of {total}")
