---
type: verdict
title: 'Verdict: okf-summary-nudge plan-reviewer round 3'
description: 'plan-reviewer verdict for round 3 of okf-summary-nudge: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-18T21:56:00+00:00'
slug: okf-summary-nudge
pass: plan-reviewer
round: 3
body_schema: verdict/1
---

## Summary

The revision takes round 2's fix. Setting KMCTL_PINNED=1 in the hook command stops every copy on PATH from handing off, including the v0.7.0 and v0.8.0 copies already installed. hand_off stays as it is, and the new decision records in one line that the nudge runs on the copy on PATH. No open risk could break the plan.

## Checked

- `git show v0.7.0:src/kmctl/pin.py` and `git show v0.8.0:src/kmctl/pin.py`: `PINNED_ENV = "KMCTL_PINNED"`, `pinned()` is `bool(os.environ.get(PINNED_ENV))`, and `handoff_pin` returns None first thing when `pinned()` is true. `hand_off` returns None when `handoff_pin` does.
- `git show v0.7.0:src/kmctl/__init__.py` and `git show v0.8.0:src/kmctl/__init__.py` `main`: `app()` runs when hand_off returns None. v0.7.0 has no `summary` group and v0.8.0 has `summary ack` but no `nudge`, so either one exits 2 with a Click usage error, which the guard turns into `{}`.
- The current `src/kmctl/pin.py` uses the same env name, so setting it in the hook command covers this release too.
- apm/claude/.apm/hooks/hooks.json: the SessionStart guard pattern that the PostToolUse entry copies.
- Both spikes cited under "Could invalidate this plan" (2 and 3) were accepted in earlier rounds, and the revision does not change what they cover.

## Findings

- p1 (resolved): the hook command sets KMCTL_PINNED=1, so no copy hands the nudge to uvx; r2 tests it.
- p2 (resolved): v0.7.0 and v0.8.0 check KMCTL_PINNED before reading the lock, so they run the verb themselves and fail with a usage error that the guard turns into {}; r2 tests the missing-verb case.

## Notes

KMCTL_PINNED=1 also turns off the newer-release notices for the call. The nudge does not need them, and the SessionStart briefing still shows them. A copy older than v0.7.0 has no hand-off, so it ignores the variable and gives the same usage error. Nothing here suggests a split.
