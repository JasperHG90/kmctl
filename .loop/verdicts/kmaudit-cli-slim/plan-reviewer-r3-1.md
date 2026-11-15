---
type: verdict
title: 'Verdict: kmaudit-cli-slim plan-reviewer round 3'
description: 'plan-reviewer verdict for round 3 of kmaudit-cli-slim: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-15T06:40:56+00:00'
slug: kmaudit-cli-slim
pass: plan-reviewer
round: 3
body_schema: verdict/1
---

## Summary

Pass. p1 is resolved; no other open risk could break the plan.

## Checked

- Grepped kmaudit's source for the dropped verbs. Every hit is in a file under `packages/kmaudit/src/kmaudit/` (flat, no subpackages) or `ui.html`: cli.py, verbs.py, check_verbs.py, judge.py, sections.py, coverage.py, mcp_server.py, models.py, check_store.py, instructions.py, check_instructions.py, ui.py, ui.html, and docstrings in anchors.py, feedback.py, __init__.py, settings.py, guard.py. The prose names each site and the `*.py` glob covers them.
- Outside kmaudit, hits are the three .okf files in touches, plus the apm skills, agents, their evals and kmctl's test_apm_package.py, which kmaudit-skills-mcp (a dependency) moves to the MCP tools and touches itself.
- Every dropped verb except guard has an MCP tool in mcp_server.py (claims_todo, claims_submit, checks_todo, checks_try, checks_submit, checks_run, coverage, judge), so "exits 2 naming its MCP tool" is possible.
- Facts still match the prose: one behaviour outcome, no needs, fixes P1.
- ADR 0043 on disk still says the agents' guard hook is `kmaudit guard` (lines 38-39), and ADR 0040 describes the hook. Updating them is a docs step for the build: 0043 is in touches, and kmaudit-skills-mcp touches 0040. It does not put the plan at risk.

## Findings

- p1 (resolved): touches now cover every kmaudit source file and ui.html that names a dropped verb, and the prose lists each site.
- p2 (resolved): the UI rerun button and POST /api/rerun are in the plan and its checks.
- p3 (resolved): the plan lists the CLI-only behaviours whose tests go.
