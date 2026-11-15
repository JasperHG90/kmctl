---
type: verdict
title: 'Verdict: release-per-package-reviewer-f1 plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of release-per-package-reviewer-f1: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-15T04:47:57+00:00'
slug: release-per-package-reviewer-f1
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

No open risk could break this plan. The premise holds, the approach works, and the prior diff still applies and fixes P1 in a test.

## Checked

- Premise: `.github/workflows/release-tag.yml` (the "Name commits that landed after the notes were drafted" step) still sets `DRAFTED="$(git rev-parse "${PARENTS[2]}^")"` for a merge. After an "Update branch" merge followed by a later commit, that resolves to the update merge, whose history already holds the late commits.
- Approach: `git log FIRST..SECOND_PARENT` lists only the release branch's own commits: the notes edit, the update merge and the release commit. Main's commits that came in through the update merge are reachable from FIRST, so they drop out, and no other release's Drafted-From trailer can be picked up. The late-commit walk (`--first-parent DRAFTED..FIRST`) does not change. A rebase-style branch update, which rewrites the release commit's parent, is covered too, because the trailer survives the rebase.
- Prior diff: I checked it in a throwaway worktree. The workflow hunk applies with an offset (patch with fuzz), and the test hunk lands at the end of test_workflows.py. All 23 release_tag tests pass. The new test fails when the workflow change is taken out, so it catches P1.
- Facts against prose: one problem, one cause and one behaviour outcome that ships alone, with needs none and the two files the prose names in touches. They match.
- Risks section: none listed, which fits a one-outcome hardening change with a tested prior diff.

## Findings

None.
