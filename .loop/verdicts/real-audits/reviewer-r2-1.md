---
type: verdict
title: 'Verdict: real-audits reviewer round 2'
description: 'reviewer verdict for round 2 of real-audits: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T16:40:27+00:00'
slug: real-audits
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

All three findings sent back are fixed. The fixes touch nothing else, and
the gates pass. The change can be committed.

## Checked

- Ran `loopctl gate stamp` from the worktree. Lint, format, tests,
  integration and eval rows r1 to r4 all pass: "stamp green:
  af77557bdad77dc1b8ab76c26a299b25dfd50357bfefd233d58534eab1f7672a".
- Read `git diff HEAD` in the worktree around `bad_citations`, the
  `UnexpectedModelBehavior` handler, `render`, the ADR 0017 correction and
  the how-to paragraph.
- Searched the worktree, `.loop/` excluded, for any "five tries" or "5 tries"
  left behind. There are none.

## Findings

- f1: resolved. `bad_citations` in action/agent.py now rejects a citation
  unless `1 <= first <= last`, before it resolves the file or checks the
  range. `test_evidence_unread_lines_are_sent_back` cites `big.md:9-1` and
  `big.md:0` and asserts that the retry message names both. Without the
  check, `9-1` would give an empty range and pass, so the test would catch a
  regression.
- f2: resolved. The stderr message says "after {OUTPUT_RETRIES} retries".
  ADR 0017's correction and the how-to say "after five retries". Both match
  `retries={"output": 5}`.
- f3: resolved. The `render` docstring now says the checked list comes after
  the findings table.

## Notes

My round-1 note still applies: if a later output fails for a reason other
than citations, the stale `ws.unchecked` could make the give-up message blame
citations. It is not a finding.
