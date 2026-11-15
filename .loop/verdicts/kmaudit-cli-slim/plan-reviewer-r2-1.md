---
type: verdict
title: 'Verdict: kmaudit-cli-slim plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of kmaudit-cli-slim: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-15T06:39:27+00:00'
slug: kmaudit-cli-slim
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

Fail. p2 and p3 are resolved. p1 is narrower now, but O1's touches still miss mcp_server.py, models.py, check_store.py and coverage.py. Those files hold text agents read that names dropped verbs: the server instructions, the tool descriptions and the answer-schema field descriptions. The plan's own "no string names a dropped verb" test will fail on them. This is a revision, not a rethink.

## Checked

- The facts match the prose: one behaviour outcome, no needs, it fixes P1, and the rerun button and the deleted-test list are both in checked-by.
- Dropping guard is consistent with kmaudit-skills-mcp. That plan keeps guard only for people who still drive kmaudit through a shell, and it removes the hook from kmctl's test_apm_package.py. Nothing in the source imports guard.py except cli.py.
- The UI server is a ThreadingHTTPServer that already handles same-origin POSTs, so /api/rerun follows the pattern of /api/feedback and /api/opinion.
- ADR 0040 describes the guard hook. kmaudit-skills-mcp keeps its prose and moves its sources. Once this plan drops guard, ADR 0043's update in this plan should say guard is gone. That is a docs detail the build can handle, not a risk to the plan.

## Findings

- p1 (open): O1's touches miss mcp_server.py, models.py, check_store.py and coverage.py, which hold agent-facing text that names dropped verbs.
- p2 (resolved): the UI button plus POST /api/rerun, sharing checks_run's function, is in the plan and its checks.
- p3 (resolved): the plan lists the CLI-only behaviours whose tests go.
