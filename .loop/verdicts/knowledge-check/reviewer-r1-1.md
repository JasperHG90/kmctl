---
type: verdict
title: 'Verdict: knowledge-check reviewer round 1'
description: 'reviewer verdict for round 1 of knowledge-check: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T10:37:59+00:00'
slug: knowledge-check
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The check works on the main paths. Every eval row's test asserts its fails_when, and the gates pass. It also passes on this repo's own .okf/ and on a tree that kmctl init creates. One blocking defect remains: list items inside code fences count as index entries, so an index that shows an example fails. The other findings are plain fixes.

## Checked

- Read the staged diff (src/kmctl/__init__.py, src/kmctl/checks.py, tests/test_check.py) in full against the plan's index format.
- Ran `loopctl gate stamp` in the worktree. Result: lint, format and tests pass, eval rows r1 to r6 pass, "stamp green: 321a90aba33791bac95f603c480b1e3219dc7f67a6f7be4f9bb58762c6675b7e".
- Rows: r1 asserts exit 0 and no error findings. r2 asserts a nonzero exit and the exact set of unlisted files under check index. r3 asserts exactly one finding with file docs/README.md, line 3 and check index. r4 asserts a nonzero exit and the single file .okf/practices. r5 asserts exit 0 and "skipped docs/" on stdout. r6 asserts a JSON list whose items each carry the four keys. Every test fails when its row's behaviour breaks.
- Ran `kmctl check` on the repo's .okf/ (pass, docs skipped) and on a fresh `kmctl init` tree (pass).
- Probed edge cases in a scratch repo: a list item inside a code fence, a ../ entry, a hidden docs folder, a non-section folder in .okf/, and a non-UTF-8 index.

## Findings

- f1 (blocking): the parser does not track code fences, so it reports false failures on the format this ticket defines for every verb that writes an index.
- f2: out-of-folder targets count as entries, against the plan.
- f3: dot-folders are skipped as sections but not as pages.
- f4: a non-UTF-8 index crashes the command with a traceback.
- f5: missing docstrings and type hints.
- f6: no help tests for the new verb.

## Notes

The .okf/assets probe gave two findings for one folder (not linked, and no index.md). That matches the plan's rule that every folder is a section, so it is not a finding.
