"""Spike: does deepseek-v4.1-flash keep the release-notes checks when it rewrites a real draft?

Generates drafts with scripts/release_notes.py for TAGS, sends each RUNS times
through Bifrost (OpenAI-compatible) with the draft prompt, and applies the
plan's acceptance checks. Exits 0 when the pass rate is at least THRESHOLD.

Needs BIFROST_URL (ending in /v1) and BIFROST_VIRTUAL_KEY in the environment.
Never prints either.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.request
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROMPT = (HERE / "release-notes-system.md").read_text()
MODEL = "ollama/deepseek-v4.1-flash"
TAGS = ["v0.12.1", "v0.12.0", "v0.11.0", "v0.10.0", "v0.9.0"]
RUNS = 3
THRESHOLD = 0.7
REF = re.compile(r"\(`[^`\s]+`\)|\(#\d+\)")


def clean(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL).strip()
    i = text.find("## ")
    if i > 0:
        fenced = "```" in text[:i]
        text = text[i:]
        if fenced and text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    return text.strip()


def headings(text: str) -> list[str]:
    return [ln.rstrip() for ln in text.splitlines() if ln.startswith("## ")]


def tail(text: str) -> list[str]:
    i = text.find("## Other changes")
    return [ln.rstrip() for ln in text[i:].rstrip().splitlines()] if i >= 0 else []


def bullets(text: str) -> list[str]:
    m = re.search(r"## What changed\n(.*?)(?=\n## |\Z)", text, flags=re.DOTALL)
    body = m.group(1) if m else ""
    out: list[str] = []
    for ln in body.splitlines():
        if ln.startswith("- "):
            out.append(ln)
        elif ln.strip() and out:
            out[-1] += " " + ln.strip()
    return out


def check(draft: str, response: str) -> str | None:
    """The name of the first failed check, or None when the rewrite is kept."""
    resp = clean(response)
    if not resp:
        return "empty"
    if headings(resp) != headings(draft):
        return "headings"
    if tail(resp) != tail(draft):
        return "tail-changed"
    db, rb = bullets(draft), bullets(resp)
    dref = Counter(r for b in db for r in REF.findall(b))
    rref = Counter(r for b in rb for r in REF.findall(b))
    if set(rref) - set(dref):
        return "ref-added"
    if set(dref) - set(rref):
        return "ref-dropped"
    if any(not REF.search(b) for b in rb):
        return "bullet-without-ref"
    return None


def ask(draft: str) -> str:
    url = os.environ["BIFROST_URL"].rstrip("/") + "/chat/completions"
    body = json.dumps(
        {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": draft},
            ],
        }
    ).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-bf-vk": os.environ["BIFROST_VIRTUAL_KEY"],
        },
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.load(r)
    return data["choices"][0]["message"]["content"] or ""


def main() -> int:
    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    results: list[tuple[str, int, str | None]] = []
    for tag in TAGS:
        draft = subprocess.run(
            [sys.executable, str(repo / "scripts/release_notes.py"), "--repo", str(repo), tag],
            capture_output=True, text=True, check=True,
        ).stdout
        for n in range(1, RUNS + 1):
            try:
                resp = ask(draft)
                fail = check(draft, resp)
            except Exception as e:  # noqa: BLE001 - a call failure counts as a fallback
                resp, fail = f"<call failed: {type(e).__name__}>", "call-failed"
            results.append((tag, n, fail))
            print(f"===== {tag} run {n}: {'KEPT' if fail is None else 'FALLBACK ' + fail}")
            print(resp.rstrip())
            print()
    kept = sum(1 for _, _, f in results if f is None)
    rate = kept / len(results)
    print("===== SUMMARY")
    for tag, n, fail in results:
        print(f"{tag} run {n}: {fail or 'kept'}")
    print(f"kept {kept}/{len(results)} = {rate:.0%}; failures: {dict(Counter(f for *_, f in results if f))}")
    return 0 if rate >= THRESHOLD else 1


if __name__ == "__main__":
    sys.exit(main())
