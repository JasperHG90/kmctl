---
type: verdict
title: 'Verdict: review-due reviewer round 1'
description: 'reviewer verdict for round 1 of review-due: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T10:47:30+00:00'
slug: review-due
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. The three reasons, source resolution, handoff exclusion, shallow skip and JSON output all work, and every eval row's test asserts its fails_when. One blocking bug: `git ls-files` quotes non-ASCII paths by default, so a tracked source with such a name never resolves and a real change goes unreported. Three non-blocking findings sit beside it.

## Checked

- Ran `loopctl gate stamp` in the worktree: lint, format, tests and eval rows r1 to r7 all pass, "stamp green: b56bf3ba7c38...".
- Read src/kmctl/review_due.py, the staged diff to src/kmctl/__init__.py and tests/test_help.py, and tests/test_review_due.py in full. Compared them with OKF SPEC 3, 5.1, 5.2, 5.5 and 6.2, ADR 0006, the manifesto and the spike review-due/1.
- Rows: r1 and r2 assert the exact reason map. r3 asserts `{}` before the change and one "source changed" reason per form after it. I traced each form through `_resolve` and each one resolves through the step it is meant to test. r4 asserts no due entry and only the free-text notice. r5 asserts that the live handoff is not due and the expired one appears only under expired_handoffs. r6 uses a real `--depth 1` clone where, without the skip, the source would count as changed. r7 is weaker (f4).
- Probed it on a scratch repository. A tracked `src/café.py` changed after verification is reported as "source not resolved" (f1). A directory source gives a notice (f3). `--path` pointing at a subfolder exits 0.
- The prototypes rule and the rule that hidden paths are not concepts match checks.py. No docs/ page lists the CLI verbs, so no docs need updating.

## Findings

- f1 (blocking): a quoted ls-files output breaks resolution for any non-ASCII path. The fix is small, but it needs a test with such a filename, so I want to see it.
- f2 (non-blocking): a one-character fix in the shared `has_passed` (`<=`), plus its docstring. It is wrong only at one exact instant. It predates this ticket but this ticket relies on it, and the repo rule says such issues get fixed when found.
- f3 (non-blocking): a design gap, not a contract break. The plan only promises files. Supporting a tracked directory, for example by checking `git ls-files -- dir` is non-empty, is a plain addition. A notice is also acceptable if the help says so.
- f4 (non-blocking): add `assert data["due"]` and check the `--json` exit code. That makes the test stronger without changing the behaviour.
