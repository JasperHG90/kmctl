---
type: verdict
title: 'Verdict: antigravity-okf-stop-hook reviewer round 1'
description: 'reviewer verdict for round 1 of antigravity-okf-stop-hook: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T07:29:06+00:00'
slug: antigravity-okf-stop-hook
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. The plugin folder gets a kmctl-okf-stop Stop handler that runs okf's own script from the repository root. It continues only on executionNum 0, maps okf's block to continue, and prints {} with exit 0 in every other case. Install takes APM's broken handler out of .agents/hooks.json, and doctor reports it if it comes back. I1 is reworded accurately, and the tests it names exist and pass. Three small fixes remain, none of which needs another review. The Claude doctor check got the Antigravity wording (f1). The hooks.json clean-up can delete a hook that was already empty (f2). Row r1's command misses the structure test (f3).

## Checked

- Ran `loopctl gate stamp` from the worktree with a scratch HOME: lint, format, tests and integration pass, and eval rows r1 to r6 pass. Stamp green: 10ed0192e608a4814f1d9a4056e987d8ed5fec79ed09e910781723d57fa1f8af. agy is on PATH, so r4's validate and consumer integration tests ran (2 passed) and were not skipped.
- Read the diff in src, tests, docs and .okf, plus ADR 0017 and the fixture.
- tests/fixtures/okf-stop-check.sh is byte-identical to the okf-stop-check.sh that APM deployed in a scratch consumer, apart from its added header line. Its sha matches the pin in apm/apm.yml.
- The real APM 0.33.0 .agents/hooks.json from the spike consumer has the same shape as the test's APM_OKF_HANDLER: a flat handler under the "apm" named hook.
- STOP_COMMAND: the executionNum regex rejects 1 and 10 and accepts 0 followed by a comma or brace. `cd ../../..` from .agents/plugins/kmctl reaches the repository root. `a && b || c` falls back to {} when either step fails. The sed rewrite only fires on okf's exact block JSON. Tests check that output matches okf's reason exactly, and they cover execution 1, a clean tree, no opt-in, a bundle change, and a missing or failing script.
- r2 tests run the real install with fake tools. They cover a mixed hook, a hook left empty, grouped handlers, a second install changing nothing, a missing file and an unparsable file. r3 tests cover the doctor check failing with the fix named, passing, and antigravity.hook failing when a hook is removed. r5 checks the decision's terms and the docs.
- I1 now reads that kmctl has one hook of its own, SessionStart, and in Antigravity relays okf's opt-in Stop check, which prints {} and exits 0 without a working script. test_okf_stop_never_blocks_without_a_working_script covers that, and the claim matches ADR 0017 and the ADR 0004 amendment. The manifesto, architecture overview, ADR 0015 pointer, commands reference, doctor epilog and how-to agree with the code, apart from f1.
- I reproduced f2 by calling drop_apm_okf_stop on a scratch file outside the worktree.

## Findings

- f1: doctor.py:395 changed the claude.hook pass detail instead of antigravity.hook's at line 486. The Claude message is now false, and the Antigravity message leaves out the new hook.
- f2: the `changed` flag in drop_apm_okf_stop carries across named hooks, so an empty named hook that comes after a removed okf handler gets deleted.
- f3: r1's `-k okf_stop` selects no test that checks hooks() has both named hooks with flat handlers.

## Notes

- apm_okf_stop_present matches raw text, but drop_apm_okf_stop skips an unparsable file. So for a broken .agents/hooks.json that mentions the script, doctor names `kmctl plugin install` as the fix, and install will not change the file. That is a rare state; you could name the file in the fix or leave it.
- The relay uses a 10 s timeout where okf's own handler has 15 s. On a very large repository git status could get close, but the result is still safe: agy kills the hook and the agent stops.
