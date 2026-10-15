---
type: verdict
title: 'Verdict: review-due plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of review-due: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T08:22:50+00:00'
slug: review-due
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

Both round 1 findings are resolved: sources are resolved the way section 6.2 says, with a repository-root fallback the spike backs, and unresolved entries are a notice, not a due reason. One new gap: handoffs are OKF concepts without a verified entry, and the plan never leaves them out of the concept checks, so every handoff would be due from the start and expired ones would show twice (p3). That needs one line and a test, not a rethink.

## Checked

- The revised plan, the empty eval, my round 1 verdict, spike review-due/1 (README outcome, stdout). The spike shows the real bundle uses repository-root paths, which backs the fallback.
- OKF SPEC sections 5.1, 5.2, 5.5, 6.1 and 6.2.
- ADR 0006, 0008 and 0009, and the handoffs-list and handoff-and-continue-skills plans: handoffs live in .okf/handoffs/ with stale_after, and kmctl writes them with no verified entry.
- Repo: .okf/ has no handoffs folder yet and src/kmctl is a bare typer app, so depends_on: [] holds.

## Findings

- p1 resolved: section 6.2 path forms and concept ids are now resolved before the git check.
- p2 resolved: free-text and dead sources are a separate notice and never keep a concept due.
- p3 open: the concept checks are not scoped away from .okf/handoffs/, so handoffs are always due for 'no verified entry' and expired ones are listed twice.

## Notes

Not findings, settle while building: skipping index.md and log.md in the walk, the bare-mapping verified form, and that a default actions/checkout is shallow, so the CI action ticket needs fetch-depth: 0 for the history reason to run.
