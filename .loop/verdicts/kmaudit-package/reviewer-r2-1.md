---
type: verdict
title: 'Verdict: kmaudit-package reviewer round 2'
description: 'reviewer verdict for round 2 of kmaudit-package: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-14T12:58:50+00:00'
slug: kmaudit-package
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

Both findings sent back are fixed, and the fixes broke nothing. CI now runs
pytest at the repository root, which collects the same 1379 tests as the
gate, kmaudit's 231 among them. The stale "kmctl" wording is gone from
kmaudit's docstring, both skills and the review page. f2 stays open as
non-blocking hardening, deferred to its own ticket.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests, integration
  and eval rows r1 to r6 pass, "stamp green:
  d57c7a1c289ecd1b49fbda3208328f66910e7c3c11d739490795e7d582273556".
- f1: I read the pinned action (toiminnot actions/pytest/action.yaml at
  dc32088c) through the GitHub API. It runs `uv sync --all-extras
  --all-groups`, then `uv run pytest "$TESTS_DIRECTORY" -v ... -m
  "$TESTS_MARKERS"`, so `directory: .` is one quoted path argument. The dev
  group holds `kmaudit[tracing]` as a uv workspace member, so the sync
  installs it. I ran `uv run pytest . --collect-only -q -m "not
  integration"` in the worktree: 1379/1393 collected, 231 under
  packages/kmaudit/tests, the same count as the gate's bare `uv run
  pytest` (hidden folders such as .loop/ and .okf/ are skipped by pytest's
  default norecursedirs, and no testpaths is set).
- tests/test_ci.py: the pytest-job test pins `directory: "."` and runs a
  collect-only on that directory, asserting test ids rooted in both
  `packages` and `tests`. Pointing the job back at `tests` would fail both
  asserts.
- f3: `__init__.py`'s docstring now says kmaudit; line 8 of both
  extract-claims and write-checks SKILL.md says "kmaudit calls no model
  here"; a grep of ui.html for kmctl finds nothing, and its user-facing
  strings name kmaudit. The remaining `kmctl-claims-extractor` and
  `kmctl-check-writer` mentions are agent names, which this ticket does not
  rename. The skills' evals.json and results.md also moved to the kmaudit
  command names, and results.md says the runs predate the rename.

## Findings

- f1: resolved in .github/workflows/ci.yml and tests/test_ci.py, as above.
- f2: open, non-blocking hardening. It was not sent back this round;
  loopctl deferred it to the stub ticket kmaudit-package-reviewer-f2.
- f3: resolved in packages/kmaudit/src/kmaudit/__init__.py, both SKILL.md
  files and packages/kmaudit/src/kmaudit/ui.html.

## Notes

The new test_ci check only looks at collected ids, so a collection error in
one tree that still left some ids from it would not fail the test. The
tests gate would catch that error anyway, so I do not raise it.
