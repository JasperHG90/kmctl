---
type: verdict
title: 'Verdict: new-concept-verbs reviewer round 2'
description: 'reviewer verdict for round 2 of new-concept-verbs: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T10:50:01+00:00'
slug: new-concept-verbs
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

All four round-1 findings are fixed and the fixes broke nothing I could find. One small new gap: the bracket test passes even if `kmctl new` fails, because `kmctl check` passes on an empty bundle. That is a one-line test fix, so the label is fix.

## Checked

- Ran `loopctl gate stamp` in the worktree: lint, format, tests and rows r1 to r5 pass, stamp green 170b33b90585fcb1bd80fbda8cc827134b0796362ee10e32b15009cf3ae620aa.
- Read src/kmctl/concepts.py and tests/test_new_concept.py in full, and the `_ENTRY` regex in checks.py.
- Probed in a scratch repo with the worktree's kmctl: practice 'Use [WIP] flags (x)' with a two-line description wrote `- [Use (WIP) flags (x)](use-wip-flags-x.md): a b`, and the front matter title kept the brackets. Decision 'Café ]weird[' became 0001-cafe-weird.md with link text 'ADR 0001: Café )weird('. kmctl check passed on both.
- r1's test now asserts the path and front matter title for every kind, which covers "misnamed" in its fails_when.

## Findings

- f1: resolved. `_link_text` at concepts.py:64 turns brackets into parentheses in the link text only. Parentheses inside the brackets do not trip `_ENTRY`, and the probe passed kmctl check.
- f2: resolved. concepts.py:54 folds with NFKD before slugging, tested by test_new_title_with_accents_keeps_its_letters.
- f3: resolved. concepts.py:150 collapses all whitespace, so the index entry and front matter stay on one line, with a test.
- f4: resolved. test_new_creates_each_kind checks every kind's path and title.
- f5: open, non-blocking. test_new_title_with_brackets_stays_listed should assert `_new(...).exit_code == 0` and that the entry is in practices/index.md. Without that, a regression where new refuses bracketed titles would still pass. Non-blocking because the fix is a plain extra assertion I trust without a second look; the code it guards is correct today.
