---
type: verdict
title: 'Verdict: action-failure-points-to-summary plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of action-failure-points-to-summary: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-26T13:11:29+00:00'
slug: action-failure-points-to-summary
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The plan is small and holds up as written. It adds one `::error` line to stdout when `kmctl check` fails or `kmctl review due` crashes, and both of those paths already set `status` in `action/knowledge-ci.sh`. The plan lists no risks, and I found none that would break the approach, the scope or the contract.

## Checked

- `action/knowledge-ci.sh`: the check result is `check_status` (lines 67-72) and the crash path for `review due` is lines 104-108. Both are clear places to emit the line. Stdout is the job log when `GITHUB_STEP_SUMMARY` is set, and `action.yml` runs the script as a bash step, so stdout reaches the log.
- The script falls back to writing the summary to stdout when `GITHUB_STEP_SUMMARY` is unset. Row r3 already covers the case outside GitHub (no broken link).
- `packages/kmctl/tests/test_action.py`: `_run` captures stdout separately from the summary file and passes `extra` env, so the new tests can set the GITHUB_* run variables and assert on stdout. Fixtures already exist for a broken bundle (`broken=True`) and for a `review due` crash (`crash_review_due=True`).
- `kmctl` source never prints `::error`, so the passing-run assertion in r3 cannot be tripped by kmctl's own output.
- Eval rows r1-r4 match the one outcome. The docs file in `touches` exists and has a section on the Action's failure behaviour (around lines 215-231).
- 2.0 facts: one problem, one goal and one `behaviour` outcome. It ships alone, `needs: none` is correct, and `touches` lists the script, the tests and the how-to the prose and r4 name.

## Findings

None.

## Notes

Left to the build: what to print when `GITHUB_RUN_ATTEMPT` alone is missing (drop the `/attempts/N` part), and whether a run where both commands fail prints one line or two. Neither changes the plan.
