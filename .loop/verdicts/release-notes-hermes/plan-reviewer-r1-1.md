---
type: verdict
title: 'Verdict: release-notes-hermes plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of release-notes-hermes: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-14T19:51:21+00:00'
slug: release-notes-hermes
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach holds: a deterministic draft, a Hermes rewrite in the notes job, and a script that keeps the rewrite only when it passes mechanical checks and otherwise falls back. Two things need fixing before it goes ahead. Risk 1 rests on a spike that called the model directly, not through the agent action the workflow uses (p1). The same spike shows the checks pass a rewrite that turns shipped work into "postponed", which the plan does not account for (p2). Neither one means rethinking the plan.

## Checked

- Read the plan, the eval rows, the spike folder (README outcome, run.json, stdout, stderr, files/spike.py) and the v0.9.0 draft from `scripts/release_notes.py v0.9.0`.
- Read the hermes action at the pinned SHA (action.yaml and README in JasperHG90/toiminnot@551e8a6). It runs AIAgent with default toolsets unless `enabled_toolsets` or `disabled_toolsets` is set, writes the final reply to `$RUNNER_TEMP/hermes-response.txt` and sets `response_file` only after the runner exits 0. If the step fails under continue-on-error, `response_file` is empty, which the plan's missing-file rule already covers.
- Read `.github/workflows/hermes-issue-triage.yaml`, `scripts/hermes_triage.py` and the current `release.yml`. The release-per-package plan puts the draft in its own notes job, which runs in dry runs and has the workflow-level `contents: read` token. That fits the plan's "runs in dry runs too" and keeps a write token away from the agent.
- Problems, Goals and Outcomes match the prose. O1 is support (seen by nobody, fixes P2) and cannot ship alone. O2 is behaviour, needs O1 and touches the workflow, prompt, workflow test and ADR 0035, as the prose says. Neither the needs nor the fixes are wrong.

## Findings

- p1: the risk 1 evidence comes from a bare chat call, not the hermes agent action with default tools; pin the tools off and test that, or spike through the runner.
- p2: the spike shows a rewrite that reverses meaning ("deferred hardening" shipped became "postponed") passing every check; the plan has to handle that or have the operator accept it explicitly.

## Notes

The ticket is small enough to keep in one piece; it does not need a split.
