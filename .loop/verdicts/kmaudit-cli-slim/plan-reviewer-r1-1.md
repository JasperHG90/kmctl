---
type: verdict
title: 'Verdict: kmaudit-cli-slim plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of kmaudit-cli-slim: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-15T05:47:54+00:00'
slug: kmaudit-cli-slim
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The plan can work, but it fails this round. Its touches miss the runtime text and docs that name the dropped verbs (p1). It leaves people with no way to rerun stale checks from the UI or CLI (p2). Its test contract cannot hold for behaviours that exist only on the CLI (p3). None of these invalidates the plan. p2 needs an operator decision; p1 and p3 are revisions.

## Checked

- Every dropped verb except guard has an MCP tool in mcp_server.py (claims_todo, claims_submit, checks_todo, checks_try, checks_submit, checks_run, judge, coverage), backed by Python functions in verbs.py, check_verbs.py, judge.run_judge (keeps `config`) and coverage.coverage. The MCP judge tool has no `config` parameter and coverage has no `--files`/`--all`. Neither matters here: the Python function keeps config, and ui keeps --config.
- Callers: nothing in kmctl's source, the action, the workflows or scripts runs a dropped verb. The only shell callers outside kmaudit are the two skills and two agents (including the `kmaudit guard --allow` hooks, and packages/kmctl/tests/test_apm_package.py:743), and kmaudit-skills-mcp removes them. It leaves guard's fate to this plan, so dropping guard is consistent once it lands.
- The briefing's next steps name /extract-claims, /write-checks and `kmaudit ui` only, so they survive.
- Tests: most CLI tests go through one invoke helper per file and assert on JSON the MCP tools also return, so the move is mechanical.

## Findings

- p1: touches miss the runtime messages, the agent instructions, the UI page, the manifesto and overview.md, all of which name the dropped verbs.
- p2: the UI tells people to run `kmaudit checks run`, and once the verb is gone nothing replaces it for a person.
- p3: 'no behaviour test deleted' cannot hold for behaviours that exist only on the CLI.
