---
type: verdict
title: 'Verdict: release-per-package-reviewer-f1 reviewer round 1'
description: 'reviewer verdict for round 1 of release-per-package-reviewer-f1: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-15T05:12:23+00:00'
slug: release-per-package-reviewer-f1
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The fix is correct and does what the plan asks. For a merge, the step reads the newest Drafted-From trailer from the release branch's own commits (FIRST..second parent) and falls back to the parent of the second parent only when it finds none. Commits that an "Update branch" merge pulled in from main can be reached from FIRST, so they fall outside that range, and an older release's trailer on main cannot be picked up by mistake. The new test fails on the old workflow and passes on the new one. One non-blocking gap: the fallback path is no longer tested.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests, integration, eval-row r1 and r2 all pass, "stamp green: 8521fdf04dada517b1fdfbe97509a20a37c1063fe8aee36caee80264c2772325".
- Read the whole step in release-tag.yml and the fixture and helpers in test_workflows.py (released, _land_late_commits, _merge_release, _late).
- r1: ran the test suite in a scratch copy against the base release-tag.yml. test_release_tag_reads_the_trailer_past_an_update_branch_merge fails there (no warning at all) and the other 22 pass. The test asserts the late kmaudit commit and the drafted hash in the warning, and the late commit in the summary, which matches fails_when.
- r2: broke the fallback in a scratch copy (DRAFTED=""). All release_tag tests still pass, which is f1. Squash-with-trailer and no-trailer warning paths are covered by existing tests that use the shared drafted_from awk helper.
- awk helper: uses only POSIX match/RSTART/RLENGTH, so it works with mawk on Ubuntu runners. It reads all input, which avoids SIGPIPE under pipefail. It keeps the old 7 to 40 hex length bounds.
- Docs: the ADR 0012 sentence and the workflow comment match the new behaviour. summary.md acked against ADR 0012.

## Findings

- f1 (test-strength, non-blocking): add a merge test whose release commit has no Drafted-From trailer, for example by letting `_merge_release(..., trailer=False)` amend the branch commit for the merge case. Assert that the step still names the late commit and the drafted hash through the parent fallback.

## Notes

The new ADR 0012 sentence leaves "Only a kmctl release is marked Latest." on the end of a line of about 98 characters, longer than the surrounding wrap. That is cosmetic and does not need a round.
