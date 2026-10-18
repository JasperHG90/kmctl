---
type: verdict
title: 'Verdict: opencode-harness reviewer round 2'
description: 'reviewer verdict for round 2 of opencode-harness: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-18T05:19:11+00:00'
slug: opencode-harness
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

Every finding sent back is fixed as the fix summary says, and the fixes broke nothing I could find. kmctl now targets OpenCode 2.x only: one plugin entry point, Bash mapped to shell, r9 on 2.x alone, and docs that say so. The gates and all eleven rows pass in my own stamp. Pass.

## Checked

- `loopctl gate stamp` from the worktree with OpenCode v2.0.32 first on PATH: lint, format, tests and integration pass; rows r1 to r11 pass; "stamp green: fc5c93b678b4ed6cfc3d25fac659bd294a42601be4091c4cf599ba7930227c32", which matches the fingerprint of this round.
- Read src/kmctl/opencode.py in full: PLUGIN_SOURCE has only the setup export, TOOLS maps Bash to shell, and write() runs `_instructions(_config(cwd))` before its write loop, so its docstring ("nothing is written then") now holds.
- Checked the tests against the re-signed rows in the primary's rows.json. r1 expects `shell`. r5's node harness loads only setup, with an empty ctx and a full one, and asserts the pushed part and that nothing is pushed or thrown with kmctl missing, failing or silent. r9 runs `opencode debug agents` with `check` on its exit code and parses JSON, so 1.x fails it. The new non-list instructions test compares the whole tree before and after. The help test names opencode.agents, rules, okf-mcp and hook in full.
- Grepped the docs and the code for leftover 1.x, `bash`, `server` and "prints the briefing" text. The only 1.x mentions left are the ADR's context and consequences, which say what 1.x users get. That is correct. README:46 "prints the briefing" is about the Claude SessionStart hook, which is correct.

## Findings

- f1: resolved. The plugin keeps only the 2.x `{id, setup}` export.
- f2: resolved. TOOLS maps Bash to shell. The ADR records a live 2.0.32 check of the permissions.
- f3: resolved. r9 is 2.x-only and fails, rather than branching, on another version.
- f4: resolved. The ADR, the reference, the how-to, the README, the overview and the comments say 2.x only.
- f5: resolved. The pre-check covers instructions, and a test proves nothing is written.
- f7: resolved. The full ids are asserted.
- f8: resolved. The wording is fixed.

## Notes

f6 was deferred to opencode-harness-reviewer-f6 and is not judged here. The worktree's `.loop/evals/opencode-harness/rows.json` still holds the old r1, r5 and r9 text (with 1.x). The primary's re-signed copy differs. The row commands are the same, so the stamp is unaffected, but the coordinator should make sure the stale copy is not what lands. The commands reference names only "not a JSON object" as a refusal and leaves out the non-list instructions case. That is incomplete but not false.
