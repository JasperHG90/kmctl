---
type: verdict
title: 'Verdict: apm-hands-back reviewer round 1'
description: 'reviewer verdict for round 1 of apm-hands-back: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T15:02:37+00:00'
slug: apm-hands-back
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The package split, the generated Antigravity rules, the slimmer install and the ADR work hang together, and every gate is green. Two defects block. Doctor's files checks no longer see kmctl's rules in a real install: APM records them under the sub-packages' lock entries, and the unit test hides this with a fake lock (f1). The migration step can also delete a user's own SessionStart hook when it shares a group with kmctl's old one (f2). Both were reproduced. Three smaller items need no second look.

## Checked

- Ran `loopctl gate stamp` from the worktree with a fresh empty scratch HOME. lint, format, tests and integration all passed, and eval rows r1 to r8 passed. "stamp green: 3ef55ec521f63b8f31dbcbedeb099b6970d4329275949b1bbac69d8be286e916". The state commit was deferred because git had no identity in the scratch HOME.
- Read the full plugin.py and antigravity.py, the doctor.py diff, the sync script, the three apm.yml files and their hooks.json files, the release.py and pyproject changes, ADR 0020 and the amendments to 0014, 0015, 0016 and 0018, the manifesto, overview, README and docs diffs, and the new and changed tests.
- Read APM 0.33.0's hook_ownership code. It strips `_apm_source` from settings.json and keeps it in the sidecar, so comparing groups against the stripped sidecar is sound.
- f1: ran the real-install integration test with --basetemp in scratch and read the consumer's apm.lock.yaml. The rules are listed under `kmctl-claude` and `kmctl-antigravity`, not `kmctl`. With one rule per harness deleted, `kmctl doctor` still printed `ok claude.files: 29 ...` and `ok antigravity.files: 28 ...`.
- f2: called plugin.drop_old_hook on a settings.json whose one group held `echo mine` and `kmctl briefing`. It returned True and left `{}`.
- Eval rows: r2 to r5 and r7 assert their fails_when. r3 covers the handler being dropped and the wrapper kept. r4 covers both scopes, recorded and unrecorded groups, and stale and current okf-bundle. r1 and r6 are weaker (f4, f3). r5's rules case is the fake-lock problem in f1.

## Findings

- f1 (bug, blocking): doctor's files checks read only the shared `kmctl` lock entry, and APM records the rules under the `kmctl-claude` and `kmctl-antigravity` entries. claude.files lost its rule coverage, and r5's "antigravity.files covers kmctl's rules again" does not hold against real APM. Fix: also check the sub-package entries (repo matching kmctl's, virtual_path apm/claude or apm/antigravity), and make the fake lock in tests/test_doctor.py match the real shape.
- f2 (bug, blocking): drop_old_hook removes whole groups. It should remove only kmctl's hooks from an unrecorded group, as unhook does, dropping the group only when it is left empty. Add a migrate test with a mixed group.
- f3 (test-strength): the r6 uninstall assertions should check that okf-bundle is gone from .mcp.json and .agents/mcp_config.json and that STOP_COMMAND is gone from .agents/hooks.json.
- f4 (test-strength): r1's selector misses the "no instructions in the shared package" and Claude-rule assertions.
- f5 (docs): the epilog and the overview row give the migration order backwards, and doctor's claude hook and MCP details still say kmctl writes them.

## Notes

At project scope, `kmctl plugin remove --harness claude` with antigravity kept reinstalls with `--target antigravity`. I did not check whether APM then writes okf-bundle back into .mcp.json. Worth a look when f1 is fixed, but I am not raising it.
