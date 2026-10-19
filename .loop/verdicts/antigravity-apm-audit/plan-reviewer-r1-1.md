---
type: verdict
title: 'Verdict: antigravity-apm-audit plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of antigravity-apm-audit: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-19T15:07:58+00:00'
slug: antigravity-apm-audit
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

No open risk could break this plan. The rename clears `config-consistency` (spike 4). The drift on .agents/hooks.json can't be avoided at install (spike 4). The frozen-install gate is clean on a fresh clone and catches a committed edit (spike 2).

## Checked

- Rename. Spike 4's `rename-okf-bundle-to-bundle` variant passes `config-consistency`, and the only `bundle` in .mcp.json and .agents/mcp_config.json is kmctl's launcher. Spike 3 shows the failure hits every target, Claude Code alone too, so the scope is right.
- Drift stays for Antigravity. Spike 4 shows no APM option keeps okf's Stop handler out without also dropping okf-stop-check.sh, which kmctl's wrapper needs. That makes `--no-drift` plus a frozen-install gate the right shape.
- Listed risk (the gate fails on a clean project): spike 2 settles it for claude+antigravity. The outcome test commits and clones before editing, which covers the uncommitted-edit limit spike 2 found.
- Every place that names `okf-bundle` matches the plan's list (git grep). The hits in ADR 0011 and ADR 0023 are the rule, not the server. No `mcp__okf-bundle__` tool id appears anywhere. Dropping `drop_old_mcp` is required: under the name `bundle` it would delete okf's own server.
- `antigravity.py:411` and `opencode.mcp_present` key on `MCP_NAME` and kmctl's launcher, so they follow the rename with no change.

## Findings

None.

## Notes

Spikes 2 and 4 ran claude+antigravity only, but the outcome test adds opencode. Two things there are untested: whether `apm audit --ci --no-drift --no-policy` exits 0, and whether frozen install plus patch leaves opencode.json and the patched agents byte-identical. Check these early in the build. Both should be deterministic: APM writes opencode.json's `mcp`, and patch adds `instructions` in APM's format. Any fix would sit in this ticket's patch code, so this does not threaten the plan.
