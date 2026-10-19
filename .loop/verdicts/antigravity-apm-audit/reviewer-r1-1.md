---
type: verdict
title: 'Verdict: antigravity-apm-audit reviewer round 1'
description: 'reviewer verdict for round 1 of antigravity-apm-audit: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-19T16:40:44+00:00'
slug: antigravity-apm-audit
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The rename to `bundle` is complete and consistent, `drop_old_mcp` and its tests are gone, doctor's Claude check passes okf's own `bundle` and fails one that runs no okf script with a fix that removes it first, the starter gains `check-install`, and the install how-to gives a CI route per harness. All gates and eval rows are green on my own stamp. One ADR sentence overstates doctor's behaviour; a plain fix, so the label is fix.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests, integration, and rows r1 to r4 all pass; stamp green 882a6f3cdff0469ce617a71ca7cd4699bea07bbb437a804792193c73d45028db.
- Read the full uncommitted diff (src, apm, starter, tests, docs, README, .okf). Grepped for `okf-bundle`, `drop_old_mcp` and `okf_server_current`: what is left is the okf-bundle rule, ADR bodies covered by the new Corrections, and the Antigravity check, which uses `okf_server_current` on purpose.
- r1: `test_bootstrap_audit_passes_for_claude_and_antigravity` runs `apm audit --ci --no-drift --no-policy` through `_run`, which asserts exit 0. Under the old name, config-consistency would fail it (spike 3/4).
- r2: the render test checks the recipe, `git status --porcelain` and the clean-checkout comment. The bootstrap test commits, clones, runs `just check-install` (asserting exit 0 and an empty porcelain), then commits a skill edit, clones again, and asserts a nonzero exit with the skill's path in stdout. So an install failure cannot pass for detection.
- r3: `test_split_package_declares_okf_mcp_at_the_pin` asserts `MCP_NAME == "bundle"` and that apm.yml's entry matches it.
- r4: `-k bundle` collects `test_all_ok_with_okf_own_bundle_server` (okf's own entry, exit 0, exact detail) and `test_broken_piece_fails_naming_it_and_its_fix[bundle-runs-no-okf-script]` (fail, with the remove-first fix).
- r5 (judgment): step 4 of the install how-to gives Claude Code only `apm audit --ci`, Antigravity `--no-drift` plus the install check, and OpenCode the install check alone, with the reason (content-integrity), which matches the amended r1. Spike 3 backs claude's drift passing after install; the policy check fails open without an org policy (spike 3 output: "enforcement skipped"). ADR 0014 (folded into its 2026-10-19 Correction, count bumped to five), 0018 (dated Consequence), 0019 (name updated) and 0020 (dated Correction, including the end of `drop_old_mcp`) are all done, and the log has a line. `drop_old_mcp` no longer exists.
- Doctor: only Claude's check takes a `bundle` that is not kmctl's launcher. That departs from the plan's plural "checks", but it is sound: spike 4 shows APM writes kmctl's launcher for Antigravity, and the commands reference states each check's rule correctly.

## Findings

- f1 (docs, not blocking): ADR 0020's Correction ends "`kmctl doctor` passes a `bundle` that runs okf's script, kmctl's launcher or not". That holds only for `claude.okf-mcp`; the Antigravity and OpenCode checks still need kmctl's launcher. Say "doctor's Claude Code check".

## Notes

The Claude-only "apm audit --ci passes on a clean install" route has no test with drift and policy on. The spike evidence covers it, and adding one is not needed for this ticket.
