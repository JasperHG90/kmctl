---
type: verdict
title: 'Verdict: ci-action reviewer round 1'
description: 'reviewer verdict for round 1 of ci-action: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T11:42:15+00:00'
slug: ci-action
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. The script deepens a shallow clone, writes both reports under headings to the job summary, fails on a failed `kmctl check` or a crashed `kmctl review due`, and never fails because concepts are due. action.yml is a composite action that installs kmctl from its own checkout, and the repository workflow uses `./` with fetch-depth 0 and read-only permissions. Each eval row's test fails when its behavior breaks.

## Checked

- `loopctl gate stamp` from the worktree: lint, format and tests pass, rows r1 to r6 pass, "stamp green: bc8741c88468e53523494f2aaf7ad4a55c03f1a753244c083a1b92ac1e66af6e".
- Read action.yml, action/knowledge-ci.sh, .github/workflows/knowledge.yml and tests/test_action.py in full (the change is staged in the worktree).
- Mutation runs against a scratch copy of the script: removing the unshallow fetch fails r4; ignoring check's exit status fails r2; ignoring a review-due crash fails r5; failing when a concept is listed fails r3. So r2 to r5 detect their `fails_when`.
- I ran the script by hand on a fixture with an unverified concept: exit 0, and the summary lists `due note (unverified)`. On a depth-1 clone whose remote cannot be reached, the unshallow fetch fails, the script writes a note to stderr, and the summary carries review due's own line "shallow clone, so source history was not checked", which is what the plan asks for.
- `kmctl review due` always exits 0 (its help says so), so a nonzero exit from it really does mean a crash, as the script assumes.
- r6: the test checks `runs.using == composite`, a step that runs knowledge-ci.sh, and a workflow containing `uses: ./`.
- Consistency: the manifesto and ADR 0005 describe deterministic checks on every pull request at no model cost, and this change matches. pyproject has a static version and hatchling, so `uv tool install` on the action's checkout builds without git metadata.

## Findings

None.

## Notes

The plan says `kmctl review due --json`, but the script writes the plain table. The job summary is read by people, so the table serves that audience better, and no eval row needs JSON. I do not count this as a defect. The r3 check (`"note"` in the review-due section) is loose but enough on this fixture, which is not shallow.
