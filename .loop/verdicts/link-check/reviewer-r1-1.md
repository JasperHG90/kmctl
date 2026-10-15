---
type: verdict
title: 'Verdict: link-check reviewer round 1'
description: 'reviewer verdict for round 1 of link-check: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T11:01:52+00:00'
slug: link-check
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The link check is wired in, the fence tracking moved out cleanly, and every gate and row is green. One real gap blocks: on docs/README.md the code skips every list-item line, not just the targets the index check reports, so broken links that leave docs/ and `/` links in list items pass silently. The rest are a stale help line, a weak r3 test and parser edge cases.

## Checked

- `loopctl gate stamp` from the worktree: lint, format and tests pass, rows r1 to r5 pass, "stamp green: 97af93f3e312e801e7f1a796e93aac756639a2f05bd4dfadf5f96970b1ecf0f4".
- Read the staged diff and all of src/kmctl/checks.py, plus the kmctl check command in src/kmctl/__init__.py.
- Rows: r1, r2 and r4 assert exact (file, line) lists under check name link. r5 covers http, mailto, #anchor and a fenced link. r3 is weak (f3).
- Ran kmctl check on a scratch repo whose docs/README.md had list items linking ../CONTRIBUTING.md, /src/gone.py and a second link gone2.md on an entry line. None was reported by either check. A prose line with my%20page.md (file exists) and how-to/install.md?plain=1 was reported as broken.
- Ran kmctl check on the worktree itself: it passes.

## Findings

- f1: `skip_entries` checks `_ENTRY.match(text)` on the whole line, but `_entries` keeps only the first link and only when it stays in the folder and is not `/`. Fix: skip a target only when it is the line's first link and `_entries` would keep it, and check the rest. Add a test for a broken out-of-folder or `/` list item in docs/README.md. Blocking, because the fix has to match `_entries` filtering exactly or it double-reports or leaves gaps again.
- f2: the docstring at src/kmctl/__init__.py:118 is the `kmctl check --help` summary an agent reads. It and checks.py line 1 should name the link check. Non-blocking: a plain text fix.
- f3: assert `findings == [(".okf/decisions/0001-first.md", N)]` with the computed line, or check the message names gone.py. Non-blocking: a test I only want stronger, and the code behaves correctly.
- f4: url-decode the target and drop a `?query` before resolving. Single-quoted titles, angle brackets with spaces and reference definitions are worth covering or naming as out of scope. Non-blocking: hardening for less common syntax, with a plain fix.

## Notes

The %20 false positive also affects the existing index check (`entry links my%20page.md, which does not exist`), so the fix for f4 could live in shared target handling.
