---
type: verdict
title: 'Verdict: hermes-workflows plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of hermes-workflows: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-20T08:34:49+00:00'
slug: hermes-workflows
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

Round 1. No open risk could break this plan. Pass.

## Checked

- Listed risk (copied okf skill trips the hooks): settled by
  spike:hermes-workflows/2. Its script copied the workspace okf skill, both
  prompts and both Hermes workflows into a worktree of HEAD, staged them, and
  `uvx prek run --all-files` exited 0 with kmctl check, ruff and okf validate
  --strict all passing. That answers the risk. Spike 1 is a probe and settles
  nothing, as its README says.
- The gates are ruff check, ruff format, pytest and pytest -m integration.
  Tests that scan `.github/workflows/` (test_action.py wiring, test_ci.py,
  test_workflows.py) list their files by name or only need one workflow to
  use `./`. Adding two `.yaml` workflows does not break them.
  test_old_audit_is_gone checks for "hermes" only in action.yml,
  knowledge-audit.yml and pyproject.toml, none of which the plan touches.
- ADR 0035 is free: 0034 is the highest in `.okf/decisions/`, and no other
  plan or worktree claims 0035.
- The triage workflow checks out the default branch on every trigger, so
  moving the apply step into `scripts/hermes_triage.py` runs trusted code.
  The interactive workflow reads its prompt and skills from a separate
  default-branch checkout, which eval r2 pins.
- The source triage step's trailer parsing and label allowlist carry over.
  The new 800-character cut must run after the trailer is taken out. Eval
  rows r4 and r5 cover that.

## Findings

None.

## Notes

Not raised because building will settle them: the prompts mention `aim.toml`
where kmctl uses `apm.yml`; TRIAGE_AREAS has to be rewritten for kmctl's
folders (src, action, apm, starter, tests, docs, scripts, plus okf and ci for
`.okf/` and `.github/`); the OLLAMA_API_KEY secret has to exist for the
operator to see the workflows run.
