---
type: verdict
title: 'Verdict: apm-only-install plan-reviewer round 3'
description: 'plan-reviewer verdict for round 3 of apm-only-install: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-16T20:30:55+00:00'
slug: apm-only-install
pass: plan-reviewer
round: 3
body_schema: verdict/1
---

## Summary

p3 is resolved. When an okf server already exists under any name, install keeps it and adds none. The APM how-to stops telling users to add okf-skills directly. Eval row r6b tests that no second server is added. The note about user scope with no `.okf/` is answered too: the launcher passes `.okf`, so the server starts and its tools report no bundle. No open risk could break the plan. Pass.

## Checked

- Round 2 verdict (plan-reviewer-r2-1.json/.md): p1 and p2 resolved, p3 open on r6b.
- The plan's "okf's MCP server for Claude" item and eval row r6b in .loop/evals/apm-only-install/rows.json. The skip rule matches the server by its command or args, not by name. That covers APM's `bundle` (spike:kmctl-doctor/3 shows APM writes it into .mcp.json for a direct okf-skills dependency) and any server a user named themselves.
- Ordering: install runs `apm install` before it writes the MCP entry. So for a direct okf-skills dependency, APM's `bundle` is already in .mcp.json when kmctl checks.
- The no-`.okf/` fallback matches spike:antigravity-harness/1: the server starts without a usable bundle, and only tool calls fail.

## Findings

- p1: resolved, as in round 2.
- p2: resolved, as in round 2.
- p3: resolved by the skip-if-any-okf-server rule, the how-to change and r6b's new failure case.

## Notes

- For the build: kmctl's own `okf-bundle` also names okf_mcp.py, so the skip check must not match kmctl's own entry. If it does, a later install with a new okf pin would keep the old sha forever. Replace `okf-bundle` by name (as the hook is replaced by command) and skip only for other servers. One r6b case with a changed pin would catch this.
- A user who enabled the okf plugin on purpose keeps its plugin-provided `bundle` server, which is not in .mcp.json, so the check misses it. This is rare and the result is two servers with the same tools, not a failure.
- No split recommended. One contract, and every listed risk is settled by a spike.
