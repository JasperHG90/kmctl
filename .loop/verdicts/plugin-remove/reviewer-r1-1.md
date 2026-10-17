---
type: verdict
title: 'Verdict: plugin-remove reviewer round 1'
description: 'reviewer verdict for round 1 of plugin-remove: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T08:24:24+00:00'
slug: plugin-remove
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. `apm uninstall` runs on the name built from the entry's own git: URL. The kept harnesses are reinstalled at the removed entry's ref. A target is dropped only when no other dependency is left. The hook, MCP and Antigravity cleanup leaves other people's pieces alone. Doctor's harnesses_found no longer counts a kept target once the lock lists kmctl. The stamp is green. The four findings are small and none of them needs another review: a wrong summary line, a misleading next step in APM failure messages during remove, one stale verbs list in the reference, and a test that does not pin down the reinstall source.

## Checked

- Gates: I re-ran `loopctl gate stamp` from the worktree with an empty scratch HOME. Result: `stamp green: 0023e63a350eae26202f4404f8ecf6ecb4d0e98bd10bca78a951d5203a9b3509`, with lint, format, tests, integration and eval rows r1 to r8 all passing. The state commit was deferred because the scratch HOME has no git identity.
- I read the full uncommitted diff against HEAD (4a5c207d): plugin.py remove, uninstall_name, _kmctl_entries, _drop_targets, unhook, _remove_mcp, _remove_antigravity, and ref threaded through install/write_manifest/kmctl_entry; the __init__.py command and the _harnesses remove branch; doctor.harnesses_found; tests; the docs and ADR 0019.
- harnesses_found: _manifest_targets already returns targets only while apm.yml names kmctl's entry, so after a full remove a kept target does not mark a harness as installed. After a partial remove, the lock lists kmctl and targets are ignored. test_after_remove_doctor_reports_only_the_kept_harness would fail without the doctor change, because the reinstall puts kmctl's entry back and antigravity stays in targets.
- Eval rows: r1 covers prompt, default, refusal without a terminal or with --json, and nothing installed with no APM calls. r2 is parametrized over https, http host:port, scp-style and string entries, and checks the actual call and -g. r3 checks the ref and target of the reinstall and the failure message (see f4 for the source). r4 checks other hooks, keys and servers, a foreign okf server, user-scope claude mcp remove, hooks.json {} against a non-empty one, and both target cases with the note. r5 checks doctor after a partial remove, that a second remove changes no file and makes no call, and the Next line. r6 is a real APM integration test: two removes, doctor's claude checks pass after the first, no APM files, settings hook, .mcp.json or lock after the second, and README kept. r7 checks help terms, the reference, the how-to and the ADR.
- I confirmed f1 with a throwaway probe test run from the scratchpad (since deleted). The tree is unchanged.
- Consistency: the ADR, the architecture overview row and the reference section match the code, except f3.

## Findings

- f1: `_report_remove` falls back to "kmctl is not installed here" whenever `removed` is empty, even when `kept` is non-empty. Name the harnesses still installed, or say only the named ones were not installed.
- f2: remove calls `_apm`, whose `_require` message tells the reader to run `kmctl plugin install again`. Remove needs its own next step, for example to run the uninstall by hand and then `kmctl plugin remove` again.
- f3: update the Verbs list in the commands table row for `kmctl plugin`.
- f4: in the r3 test, give the installed entry a non-default git: source and assert the reinstalled entry keeps it.

## Notes

`uninstall_name`'s string branch cannot be reached through remove, because `_is_kmctl_entry` matches only mappings. It is harmless, and r2 asks for it.
