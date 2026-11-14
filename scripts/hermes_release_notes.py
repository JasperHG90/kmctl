"""Keep Hermes' rewrite of the release notes only when it passes the checks (ADR 0035).

Usage::

    python3 scripts/hermes_release_notes.py DRAFT RESPONSE_FILE [--before PATH]

DRAFT is the notes ``scripts/release_notes.py`` wrote; RESPONSE_FILE is what
Hermes replied, rewriting the What changed bullets for users. The script
prints the notes the release commits: the cleaned rewrite when it passes every
check, else the draft byte for byte with a ``::warning::`` naming the failed
check. It always exits 0, so a Hermes failure never blocks a release.

When the rewrite is kept and ``--before`` is given, the draft's What changed
section goes to that file in a collapsed "Draft before Hermes" block, so the
person who merges the version pull request can read each rewritten line
against the line it came from. On a fallback the file is removed.

The checks, in order: the response file exists (``missing``) and is non-empty
once cleaned (``empty``); its ``## `` headings are the draft's, in order
(``headings``); everything after the What changed section matches the draft,
ignoring trailing whitespace (``tail``); and under What changed the set of
references, ``(`slug`)`` and ``(#N)``, equals the draft's (``ref-added``,
``ref-dropped``), with at least one on each bullet (``bullet-without-ref``).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REF = re.compile(r"\(`[^`\s]+`\)|\(#\d+\)")
HEADING = re.compile(r"^## ", re.MULTILINE)
COMMENT_LINE = re.compile(r"^[ \t]*<!--.*?-->[ \t]*(?:\n|\Z)", re.MULTILINE | re.DOTALL)
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
WHAT_CHANGED = "## What changed"


def clean(response: str) -> str:
    """Strip HTML comments, any preamble before the first heading and a fence round the reply."""
    text = COMMENT.sub("", COMMENT_LINE.sub("", response)).strip()
    if m := HEADING.search(text):
        preamble, text = text[: m.start()], text[m.start() :]
        if "```" in preamble and text.endswith("```"):
            text = text[:-3].rstrip()
    return text.strip()


def headings(text: str) -> list[str]:
    """The ``## `` headings of ``text``, in order."""
    return [ln.rstrip() for ln in text.splitlines() if ln.startswith("## ")]


def _split(text: str) -> tuple[str, str]:
    """The What changed section of ``text`` and everything after it."""
    start = text.find(WHAT_CHANGED)
    if start < 0:
        return "", text
    m = HEADING.search(text, start + len(WHAT_CHANGED))
    end = m.start() if m else len(text)
    return text[start:end], text[end:]


def _lines(text: str) -> list[str]:
    """``text``'s lines without trailing whitespace or trailing blank lines."""
    return [ln.rstrip() for ln in text.rstrip().splitlines()]


def _bullets(section: str) -> list[str]:
    """The bullets of ``section``, each joined with its continuation lines."""
    out: list[str] = []
    for ln in section.splitlines():
        if ln.startswith("- "):
            out.append(ln)
        elif ln.strip() and out:
            out[-1] += " " + ln.strip()
    return out


def check(draft: str, rewrite: str) -> str | None:
    """The name of the first check the cleaned ``rewrite`` fails, or None when it passes."""
    if not rewrite:
        return "empty"
    if headings(rewrite) != headings(draft):
        return "headings"
    draft_changes, draft_tail = _split(draft)
    changes, tail = _split(rewrite)
    if _lines(tail) != _lines(draft_tail):
        return "tail"
    want = set(REF.findall(draft_changes))
    bullets = _bullets(changes)
    got = {ref for b in bullets for ref in REF.findall(b)}
    if got - want:
        return "ref-added"
    if want - got:
        return "ref-dropped"
    if any(not REF.search(b) for b in bullets):
        return "bullet-without-ref"
    return None


def before_block(draft: str) -> str:
    """The draft's What changed section in a collapsed "Draft before Hermes" block."""
    section = _split(draft)[0].rstrip()
    return (
        "<details>\n<summary>Draft before Hermes</summary>\n\n"
        f"{section}\n\n</details>\n"
    )


def choose(draft: str, response: str | None) -> tuple[str, str | None]:
    """The notes to commit and the failed check's name, None when the rewrite is kept."""
    if response is None:
        return draft, "missing"
    rewrite = clean(response)
    if failed := check(draft, rewrite):
        return draft, failed
    return rewrite + "\n", None


def read_response(name: str) -> str | None:
    """Return Hermes' response, or None when there is none to read.

    A missing file, one that cannot be read, or one that is not UTF-8 all
    count as no rewrite, so the draft stands and the run goes on.
    """
    if not name:
        return None
    try:
        return Path(name).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def main(argv: list[str] | None = None) -> int:
    """Print the chosen notes, write or remove the --before file; always exit 0."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("draft", type=Path, help="the notes release_notes.py wrote")
    parser.add_argument(
        "response", help="Hermes' response file; empty or missing means no rewrite"
    )
    parser.add_argument(
        "--before",
        type=Path,
        help="when the rewrite is kept, write the draft's What changed section here",
    )
    args = parser.parse_args(argv)

    draft = args.draft.read_text()
    response = read_response(args.response)
    notes, failed = choose(draft, response)
    if failed:
        print(
            f"::warning::Hermes' rewrite failed the {failed} check, so the draft stands.",
            file=sys.stderr,
        )
    if args.before:
        if failed:
            args.before.unlink(missing_ok=True)
        else:
            args.before.write_text(before_block(draft))
    sys.stdout.write(notes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
