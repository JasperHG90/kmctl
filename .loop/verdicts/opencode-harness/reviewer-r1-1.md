---
type: verdict
title: 'Verdict: opencode-harness reviewer round 1'
description: 'reviewer verdict for round 1 of opencode-harness: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-18T04:59:38+00:00'
slug: opencode-harness
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The OpenCode harness is built well against the plan and the signed eval, and every gate and row is green in my own stamp. But the coordinator relayed a requirement from the operator, given after this round opened: only OpenCode 2.x must be supported. The plugin's `server` entry point, the `bash` mapping, r9's 1.x branch, and the 1.x text in the ADR and docs exist only for 1.x. Rows r1, r5 and r9 were re-signed to require that 1.x support, so the contract has to change (operator re-sign) before the code can follow. Hence fail, with eval_row set on f1 to f3. The plan itself already targets 2.x (setup, `shell`), so it still holds.

## Checked

- `loopctl gate stamp` from the worktree, with OpenCode 2.0.32 first on PATH: lint, format, tests and integration pass; rows r1 to r11 pass; "stamp green: 9f822e472ba3d4c92faebc19c2d73389bc69cb4239234e725e0e1a12926543ec".
- r9 again by hand with OpenCode 1.19.3 on PATH: 1 passed.
- Read the full diff of src/kmctl/opencode.py, plugin.py, doctor.py and __init__.py, the new tests/test_opencode.py, the changed tests, ADR 0024, the manifesto, the commands reference and the how-tos.
- Each row's test against its fails_when: r1 checks the exact map, the order, dropped keys, the body, determinism and the unknown-tool refusal; r2 and r3 check the tree, idempotence, other keys and the refusal; r4 covers the three lock cases in both modules; r5 runs the plugin under node with missing, failing and silent kmctl stubs; r6 diffs the tree after undo; r7 breaks each piece and checks the detail and fix; r8 and r9 run real APM and OpenCode. Only the help part of r7 is weak (f7).
- The author's claims. The two deviations were justified for the brief as it stood: 1.x refused a setup-only plugin and knows only `bash`. ADR 0024 records both, plus the `.env` side effect. They are now out of scope (f1, f2). opencode.json written as APM writes it is right, because r8's reinstall-then-patch check showed no change. The test_antigravity fixture matches real locks: kmctl_files (ADR 0020) folds in the kmctl-antigravity sub-package, which lists Antigravity's rules, and the real-APM Antigravity integration tests pass with the new detection. The worktree rows.json is byte-identical to the primary's signed copy, per the brief. I did not re-diff it.
- Reproduced f5 in a scratch repository: with `"instructions": "AGENTS.md"`, write() wrote eight files and then raised.

## Findings

- f1: the 1.x `server` entry point is out of scope under the 2.x-only requirement. Drop it and the 1.x half of r5, which the operator needs to re-sign.
- f2: map Bash to `shell`, as the plan said, now that 2.x is the only target. Re-sign r1 and confirm through r9 on 2.x that the agents still load with the permissions intended.
- f3: r9 should test 2.x only. Remove the `agent list` branch and re-word the row.
- f4: rewrite ADR 0024, the commands reference, the code comments and the r10 docs test to say kmctl targets OpenCode 2.x only, and record that choice in the ADR. Blocking, because it changes what the decision records.
- f5: write() writes files before it refuses a non-list `instructions`. The fix is plain: check it up front.
- f6: `--undo --scope user` deletes project-scope OpenCode files. This is pre-existing for Antigravity and worth fixing for both.
- f7: the doctor-help assertion passes even if the opencode ids are missing from the epilog.
- f8: the how-to's wording for what the plugin does is wrong.

## Notes

The 2.x-only requirement came through the coordinator, after the eval was signed. f1 to f3 carry eval_row because the signed rows themselves need the operator's re-sign.
