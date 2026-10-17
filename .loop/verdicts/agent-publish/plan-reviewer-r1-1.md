---
type: verdict
title: 'Verdict: agent-publish plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of agent-publish: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T07:42:14+00:00'
slug: agent-publish
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

Fail. The plan lists no risks and cites no spikes. Three unlisted risks could break it. The one that matters most is p1: the token step would run code that the agent step can write to.

## Checked

- action/agent.py already has Report, SEVERITIES, render and the exit-code convention (UsageError means 2), which publish can reuse.
- action.yml and .github/workflows/knowledge-audit.yml already give the token to one step only, and that step runs action/knowledge-audit-issue.sh.
- run_shell keeps HOME and PATH and runs as the same user (SHELL_ENV_KEEP), so the agent step can write to the checkout and to the uv cache.
- ADR 0017 states that no command can reach the GitHub token.
- The repo has no CODEOWNERS file in .github/, the root or docs/, so the default run here mentions no one, as the plan says.

## Findings

- p1: Running agent.py with its third-party dependencies in the token step means the token step runs code the agent step could have changed: the checkout copy of agent.py, the folder it imports from, and the uv cache. Spike question: can a run_shell command in the run step change what `uv run --script action/agent.py publish` imports in the next step?
- p2: An @-mention in an edited issue body probably does not notify anyone, so owners would hear only about the run that opens the issue.
- p3: Below the threshold, nothing is posted, so an open issue from an earlier run stays up and lists findings that may be fixed. The operator should decide what happens to it.

## Notes

All three findings are about one command, so the ticket does not need splitting. p2 and p3 can be settled by an operator decision. p1 needs a change to the design of the token step.
