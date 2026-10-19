---
type: verdict
title: 'Verdict: review-due-commit-order reviewer round 2'
description: 'reviewer verdict for round 2 of review-due-commit-order: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-19T16:32:41+00:00'
slug: review-due-commit-order
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

Both round 1 findings are fixed and the fixes break nothing they touch. The change passes.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests, integration and eval rows r1 to r7 all pass; "stamp green: 30c2986744c5a6573896d2a2d953c70bbf367cf8980c6fecc26d1027040795ed".
- Read `_show` in src/kmctl/review_due.py. A found object's header is "OID TYPE SIZE" and never echoes the spec, so the trailing-word test cannot misread a found object, even for a path that itself ends in " missing". Only found headers reach `int(header.split()[2])` now.
- Read test_docs_page_with_a_spaced_path_deleted_in_history. It commits, deletes and restores "docs/how/my page.md", so the verification-commit walk asks cat-file for the spec at the deletion commit. Under the old code that header splits into three fields and `int("missing")` raises, so the test fails without the fix. It asserts exit 0 and an empty due list.
- Compared the last lines of .claude/rules/docs-layout.md with apm/claude/.apm/instructions/docs-layout.instructions.md: they match, and both describe commit order.

## Findings

- f1: resolved at src/kmctl/review_due.py:209, which treats headers ending in " missing" or " ambiguous" as no text. The new test covers it.
- f2: resolved. The rule's last line now matches the package copies.
