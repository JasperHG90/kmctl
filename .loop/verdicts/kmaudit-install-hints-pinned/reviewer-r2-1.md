---
type: verdict
title: 'Verdict: kmaudit-install-hints-pinned reviewer round 2'
description: 'reviewer verdict for round 2 of kmaudit-install-hints-pinned: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-15T08:21:43+00:00'
slug: kmaudit-install-hints-pinned
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

f1 is fixed: the WHAT text in release.yml and the `set` help in release.py now name the docs/commands.md (kmaudit[tracing]) line as well as the README. The fix touched only wording and nothing regressed. The same wrong claim still sits in two places that round 1 missed, so I raise f2. It is a plain wording fix and does not block.

## Checked

- I read the round's diff to release.yml and release.py, plus the code around both. The WHAT text at release.yml:327 and the help at release.py:390 now match what set_kmaudit_version writes and what the bump stages with git add.
- I grepped the workflow, the scripts, the release skill, the decisions and docs for other descriptions of the kmaudit bump. That turned up the two places in f2 and nothing else.
- I re-ran `loopctl gate stamp` in the worktree. lint, format, tests and integration all pass, and so do eval rows r1 and r2. The stamp is green: 7d01e3e632911497851df3a0b0f2e465c809c4a785e9d1d3ca0953c5de47097c.

## Findings

- f1 (resolved): release.yml:327 now says the bump "pins the install lines in the README and docs/commands.md (kmaudit[tracing]) to $TAG", and release.py:390's set help says it pins "the install lines in its README and docs/commands.md".
- f2 (docs, non-blocking): the header comment at release.yml:13 still says that for kmaudit, set "pins its README's install line". The module docstring at scripts/release.py:21-22 says set "pins the install line in ``packages/kmaudit/README.md``". Both should also name packages/kmaudit/docs/commands.md's kmaudit[tracing] line. This is the same false claim as f1. Round 1 missed it, and the fix did not cause it.
