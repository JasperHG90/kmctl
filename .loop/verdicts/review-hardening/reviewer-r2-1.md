---
type: verdict
title: 'Verdict: review-hardening reviewer round 2'
description: 'reviewer verdict for round 2 of review-hardening: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T12:05:05+00:00'
slug: review-hardening
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

f1 is fixed. `_REF_DEF` now uses `\[(?!\^)[^\]]+\]:`, so footnote definitions are no longer read as links, and the reference test would fail if they were. Gates and rows r1 to r5 pass. The change can be committed.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests and eval rows r1 to r5 pass, `stamp green: cb38e942f6ee612a1dd99ed0d2b8c7e3dba1cd3d55d4aeee4cec94fc6b96528b`.
- Read the staged diff of src/kmctl/checks.py and tests/test_check.py. The fix only changes the `_REF_DEF` pattern and adds a comment above it.
- Re-ran my round 1 scratch repo, whose page has `[^1]: A footnote here.`, `[site]: https://example.com` and `[a]: #top`. `kmctl check` no longer reports the footnote, and it still skips the external and anchor-only definitions.
- test_reference_style_links now adds `[^1]` to the prose and `[^1]: A footnote here.` at line 7. It asserts that the only link finding is line 6 (`[x]: missing.md`), so a footnote reported at line 7 would fail it. Row r4's fails_when still holds.

## Findings

- f1 (resolved): fixed at src/kmctl/checks.py:35 with the `(?!\^)` lookahead, and covered by the footnote case in tests/test_check.py::test_reference_style_links.
