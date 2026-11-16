---
type: verdict
title: 'Verdict: readme-badges plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of readme-badges: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-16T09:09:11+00:00'
slug: readme-badges
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

p1 is resolved: O2 is now support and needs O1, so a split cannot separate the beta marking from the badges it checks. I found no other risk that could break the plan, and Problems, Goals and Outcomes still match the prose. Pass.

## Checked

- The plan changed only O2's kind and needs since round 1. The repo facts checked in round 1 still hold: the root README has 42 lines against the test's limit of 80, the link check skips absolute badge URLs, scripts/release.py's install-line regexes do not match badge URLs, and neither pyproject has classifiers yet.
- packages/kmaudit/tests/test_mcp.py reads docs/reference/kmaudit-commands.md and the kmaudit README for tool names, command headings and the reference link. A beta sentence and badges do not remove any of those, so the test is unaffected.
- release.yml commits the kmaudit README and the command reference when it pins install lines. It touches only those lines, so the new text survives a release.
- Facts against the prose: P1 (no badges) and P2 (no beta notice) are separate causes. O1 is a behaviour that ships alone. O2 is support that waits on O1's lifecycle badge and adds to it, which is how earlier plans here use support. Its fixes (P2) and touches (kmaudit README, command reference, both pyprojects, root README, tests/test_readmes.py) cover what the prose says changes. Eval r2 runs the whole test_readmes.py, which matches building both outcomes as one change.
- No risks are listed and no spike exists. None is needed: every claim here can be checked by reading the repo.

## Findings

- p1: resolved. O2 now says kind: support and needs: O1.

## Notes

O2's text and classifier parts could ship without O1. Only its badge part waits on O1. With needs: O1 a split keeps them together either way, so calling it support or behaviour does not change what gets built.
