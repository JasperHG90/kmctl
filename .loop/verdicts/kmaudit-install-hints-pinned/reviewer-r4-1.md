---
type: verdict
title: 'Verdict: kmaudit-install-hints-pinned reviewer round 4'
description: 'reviewer verdict for round 4 of kmaudit-install-hints-pinned: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-15T08:46:07+00:00'
slug: kmaudit-install-hints-pinned
pass: reviewer
round: 4
body_schema: verdict/1
---

## Summary

f3 is fixed. The test docstring now names both the README's and docs/commands.md's install lines, which matches what the test asserts. Nothing else regressed and the gates are green, so the change can be committed.

## Checked

- tests/scripts/test_release.py:639 now reads "``--package kmaudit set`` writes its apm.yml's version and pins the README's and docs/commands.md's install lines to kmaudit-vX.Y.Z." The body at 642-669 asserts that the manifest, the README and docs/commands.md are written, and that both pinned lines are present. Docstring and assertions agree.
- I read the nearby kmaudit set tests (672-700). Their docstrings describe only what each one asserts: the older-pin test checks only the README, and the refusal tests name their own file.
- I re-ran `loopctl gate stamp` in the worktree. lint, format, tests, integration and eval rows r1 and r2 all pass. Result: "stamp green: b387347cf04d8ec14715682c32d5d38b5d91b3fa5cae08266e3aa6108a344b63". That matches the fingerprint this round is bound to.

## Findings

- f1 (resolved in round 2): release.yml's WHAT text and release.py's set help name both lines.
- f2 (resolved in round 3): release.yml:13-14 and scripts/release.py:21-23 name the docs/commands.md kmaudit[tracing] line along with the README.
- f3 (resolved): tests/scripts/test_release.py:639 names both install lines.
