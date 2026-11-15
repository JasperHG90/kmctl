---
type: verdict
title: 'Verdict: kmaudit-install-hints-pinned reviewer round 3'
description: 'reviewer verdict for round 3 of kmaudit-install-hints-pinned: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-15T08:33:32+00:00'
slug: kmaudit-install-hints-pinned
pass: reviewer
round: 3
body_schema: verdict/1
---

## Summary

f2 is fixed. The release.yml header comment and the release.py module docstring now both name the docs/commands.md kmaudit[tracing] line along with the README. The sweep found one more stale description. It is a test docstring that the ticket's own change left behind (f3). It is a one-line wording fix and does not block. The gates are green.

## Checked

- I read the round's diff to release.yml and release.py. release.yml:13-14 now says the kmaudit bump "pins the install lines in its README and docs/commands.md". release.py:21-23 now says set pins the install lines in packages/kmaudit/README.md and the kmaudit[tracing] line in packages/kmaudit/docs/commands.md. Both match what set_kmaudit_version writes and what the workflow stages with git add.
- I grepped the worktree for other text on what the kmaudit bump pins: workflows, scripts, tests, .claude/skills/release/SKILL.md, docs, packages/kmaudit/docs and .okf. The release skill and .okf say nothing about which lines get pinned. The only matches in .loop/ belong to older tickets' plans and evals, which record history. The one stale hit is the test docstring in f3.
- I re-ran `loopctl gate stamp` in the worktree. Gates lint, format, tests and integration pass, and so do eval rows r1 and r2. Result: "stamp green: 1fc3260938e60a2d2e9f3c3f6a14d65cd620672133c65386484d8909d4ff57d1".

## Findings

- f1 (resolved in round 2): release.yml:328's WHAT text and release.py:391's set help name both lines.
- f2 (resolved): release.yml:13-14 and scripts/release.py:21-23 now name packages/kmaudit/docs/commands.md's kmaudit[tracing] line as well as the README.
- f3 (docs, non-blocking): at tests/scripts/test_release.py:637 the docstring says "``--package kmaudit set`` writes its apm.yml's version and pins the README install line to kmaudit-vX.Y.Z". This ticket extended the test body to assert that docs/commands.md is written and its kmaudit[tracing] line is pinned, so the docstring now describes less than the test checks. It should name the commands reference line too.
