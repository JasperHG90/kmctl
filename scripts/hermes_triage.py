"""Post Hermes' triage comment on an issue and apply its labels (ADR 0035).

Usage::

    python3 scripts/hermes_triage.py RESPONSE_FILE

The issue number comes from ``ISSUE_NUM``, the area names from
``TRIAGE_AREAS`` (space-separated), and ``gh`` posts with ``GH_TOKEN``.
Hermes ends its response with a ``<!-- hermes-triage: {...} -->`` trailer
holding the priority and labels. The trailer is stripped, the comment is cut
to about 200 tokens, and only allowed labels are applied, one at a time, so
one failure does not drop the rest.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Iterable
from pathlib import Path

# About 200 tokens at four characters a token.
MAX_CHARS = 800
TYPES = ("bug", "enhancement", "rfc", "question", "documentation")
PRIORITIES = ("critical", "high", "medium", "low")
TRAILER = re.compile(r"<!--\s*hermes-triage:\s*(\{.*?\})\s*-->", re.DOTALL)
NOTE = "\n\n_Cut at 200 tokens._"


def allowed_labels(areas: Iterable[str]) -> set[str]:
    """The labels triage may apply: the types, one ``area/*`` per area and the priorities."""
    return (
        set(TYPES)
        | {f"area/{a}" for a in areas}
        | {f"priority/{p}" for p in PRIORITIES}
    )


def cut(comment: str) -> str:
    """Cut ``comment`` at the last line break that keeps it, with a note, within MAX_CHARS."""
    if len(comment) <= MAX_CHARS:
        return comment
    head = comment[: MAX_CHARS - len(NOTE)]
    head = head[: head.rfind("\n")] if "\n" in head else head
    return head.rstrip() + NOTE


def parse(response: str, areas: Iterable[str]) -> tuple[str, list[str]]:
    """The comment to post and the allowed labels, priority first, from Hermes' response."""
    payload: dict[str, object] = {}
    if m := TRAILER.search(response):
        try:
            payload = json.loads(m.group(1))
        except json.JSONDecodeError as e:
            print(
                f"::warning::could not parse hermes-triage trailer: {e}",
                file=sys.stderr,
            )

    raw = [
        label.strip()
        for label in payload.get("labels") or []
        if isinstance(label, str) and label.strip()
    ]
    priority = str(payload.get("priority") or "").strip().lower()
    if priority in PRIORITIES:
        raw.insert(0, f"priority/{priority}")
    raw = list(dict.fromkeys(raw))

    allowed = allowed_labels(areas)
    if rejected := [label for label in raw if label not in allowed]:
        print(f"::warning::rejected unknown labels: {rejected}", file=sys.stderr)

    comment = TRAILER.sub("", response).strip() or response
    return cut(comment), [label for label in raw if label in allowed]


def main(argv: list[str]) -> int:
    """Post the comment and apply the labels; exit 1 when the response file is missing."""
    path = Path(argv[1])
    if not path.is_file():
        print("::error::Hermes produced no response file", file=sys.stderr)
        return 1
    issue = os.environ["ISSUE_NUM"]
    comment, labels = parse(path.read_text(), os.environ["TRIAGE_AREAS"].split())

    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(comment)
    subprocess.check_call(["gh", "issue", "comment", issue, "-F", f.name])

    for label in labels:
        try:
            subprocess.check_call(["gh", "issue", "edit", issue, "--add-label", label])
            print(f"Applied label: {label}")
        except subprocess.CalledProcessError:
            print(f"::warning::failed to apply label: {label}", file=sys.stderr)
    if not labels:
        print("No labels to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
