---
type: verdict
title: 'Verdict: prototype-check reviewer round 1'
description: 'reviewer verdict for round 1 of prototype-check: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T10:55:13+00:00'
slug: prototype-check
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

check_prototypes does what the plan asks. It flags each visible folder directly under .okf/prototypes/ that has no README.md, under check name prototype. It skips files, hidden folders and deeper folders, and it returns nothing when there is no prototypes/ folder. It runs from run_checks. The tests cover all three rows and would fail if the behavior broke. One docs gap is left in the command help, and a plain fix will do.

## Checked

- Ran loopctl gate stamp from the worktree: lint, format and tests passed, and rows r1, r2 and r3 passed. Result: "stamp green: e42789ab1dd5a7d7e6254e44bee2dbd05060f12a5458de0faf11406e39b49146". The change is staged but not committed in the worktree, so git diff main...HEAD is empty. I reviewed the staged diff.
- Read checks.py in full. No duplicate finding: _section_concepts already leaves out prototype folders with no README.md, so the index check does not report the same folder a second time. check_prototypes still runs when check_okf returns early because .okf/index.md is missing, which is fine.
- r1: test_prototype_check_passes checks for exit 0 and no prototype findings on a fixture with a linked prototype.
- r2: test_prototype_check_ignores_nested_folders adds speed/results/ and speed/src/ with no README.md and checks for no prototype findings. A version that walked into nested folders would flag those two folders, so the test would catch it.
- r3: test_prototype_check_fails_without_readme checks for exit 1 and that the prototype-check findings are exactly [".okf/prototypes/bare"].
- Consistency: the new line in the module docstring matches docs-layout.md (a prototype is one folder, .okf/prototypes/<name>/, with its README.md). There is no docs/ tree in this repo to update.

## Findings

- f1 (docs, non-blocking): the help for kmctl check (the command docstring at src/kmctl/__init__.py:116) and the first line of the checks.py docstring describe only the index checks. They should also say that each prototype folder needs a README.md. It is non-blocking because the fix is a one-line wording change with no behavior risk.
