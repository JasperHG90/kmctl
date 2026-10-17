---
type: verdict
title: 'Verdict: antigravity-okf-stop-hook-reviewer-f4 plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of antigravity-okf-stop-hook-reviewer-f4: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T08:07:33+00:00'
slug: antigravity-okf-stop-hook-reviewer-f4
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The plan holds. Doctor's `antigravity.apm-hooks` check will parse `.agents/hooks.json` the same way `drop_apm_okf_stop` does. It fails with a repair-by-hand fix when the file is not a JSON object, and otherwise fails only on a handler that runs `okf-stop-check.sh`. That closes the gap where doctor sent the user to `kmctl plugin install` for a file install leaves alone. The plan lists no risks, and I found none that could break it.

## Checked

- `src/kmctl/antigravity.py`: `apm_okf_stop_present` (line 276) matches the raw text. `drop_apm_okf_stop` (line 284) returns early on a JSONDecodeError or a non-dict top level, and filters `name -> event -> [handler]` through `_runs_okf_stop`. A shared parse that both functions use fits naturally.
- `src/kmctl/doctor.py` `_antigravity_apm_hooks` (line 495): one call site, and the fix it shows is `antigravity.FIX`. A second fix string for the unparsable case is a local change.
- Tests: `tests/test_antigravity.py:1137` already pins that install leaves `"not json okf-stop-check.sh"` alone. `tests/test_doctor.py:1027` covers the flat handler shape and the pass with no okf handler. The plan's success test extends these.
- Docs: the `antigravity.apm-hooks` row in `docs/reference/commands.md:408` and the sample doctor output in the how-to (line ~431 shows `antigravity.hook` but no `apm-hooks` line) are the places the plan names.
- Handler shape: ADR 0018 and the `APM_OKF_HANDLER` fixture (a flat `{"type","command",...}` under `name -> Stop`) come from the first live agy session with APM 0.33.0.

## Findings

None.

## Notes

The plan narrows doctor from a raw-text match to the handler-level match install uses. That means doctor no longer catches a case install misses, for example if a later APM version nested handlers as `{"hooks": [...]}` the way Claude settings do. The shape the code assumes was observed live (ADR 0018), and install has the same blind spot either way, so this does not break the plan. It is worth remembering if APM's hooks format changes.

Nothing in the plan calls for a spike or a split.
