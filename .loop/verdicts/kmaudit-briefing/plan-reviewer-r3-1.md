---
type: verdict
title: 'Verdict: kmaudit-briefing plan-reviewer round 3'
description: 'plan-reviewer verdict for round 3 of kmaudit-briefing: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-14T14:06:28+00:00'
slug: kmaudit-briefing
pass: plan-reviewer
round: 3
body_schema: verdict/1
---

## Summary

All three earlier findings are fixed and I found no new risk that could break the plan. The p3 change holds: a read-only open leaves the main `.sqlite` file's bytes unchanged and sees rows a writer has not checkpointed, which is the reason the plan gives for not using `immutable=1`. No split needed.

## Checked

- Plan, signed eval r1 to r4, round 1 and 2 verdicts, spike kmaudit-briefing/1 (README outcome).
- p3: on a scratch copy of the operator's store (I did not open the real one), a `mode=ro` open read 207 sections, created `-shm` and `-wal`, and left the main file's sha256 unchanged. On a synthetic WAL store with `wal_autocheckpoint=0` and a writer still open holding an uncheckpointed row, a `mode=ro` reader saw the row and the main file's bytes stayed the same. So eval r2 as now worded (no `.kmaudit/`, no new `.sqlite`, unchanged `.sqlite` bytes, sidecars allowed) can pass with the plan's read path, and the plan's argument against `immutable=1` is correct.
- `previous_keys` and `PREVIOUS_HASHES` exist in `sections.py` and `instructions.py` as the plan and eval r3 assume.
- 2.0 facts: unchanged since round 2 except prose about sidecars, which sits inside O1's read-only behaviour. O1 (behaviour, fixes P1) and O2 (support, needs O1, fixes P2) still match the prose; touches cover briefing.py, cli.py, the tests, commands.md and the README.

## Findings

- p1 resolved: Store is no longer opened; a read-only handle feeds status_row.
- p2 resolved: pending is the briefing's own count, matched by eval r1.
- p3 resolved: sidecars are allowed in the prose, acceptance case and eval r2, and the main file stays byte-identical under `mode=ro`, as checked above.

## Notes

If the sidecar folder is not writable, a `mode=ro` open of a WAL store fails; the plan's unavailable-line path covers that.
