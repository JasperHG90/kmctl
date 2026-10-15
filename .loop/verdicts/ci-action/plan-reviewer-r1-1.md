---
type: verdict
title: 'Verdict: ci-action plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of ci-action: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T08:12:17+00:00'
slug: ci-action
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach is sound: a composite action that installs kmctl, runs `kmctl check` (fails on non-zero) and `kmctl review due --json` (exits 0 by the review-due plan), and writes both to the job summary matches ADR 0005's free tier. Two gaps could still make it break or mean something else: a shallow CI checkout makes the review-due report wrong (p1), and the done condition can only be checked by a remote PR run that depends on repo state outside this ticket (p2). Fail, revise and look again.

## Checked

- Plan and eval (0 rows); no spikes; the placeholder r1 verdict.
- ADR 0005: deterministic checks on every PR, report as job summary; the plan matches.
- Dependency plans: knowledge-check gives a non-zero exit on failure and `--json`; review-due exits 0 whether or not anything is due, offers `--json`, and uses git history for its sources reason. So "fail only on check" works with the planned exit codes.
- Repo: src/kmctl has only `__init__.py` (both dependencies are unbuilt, as expected from depends_on); no .github/workflows yet; no docs/ folder; pyproject at the repo root, so installing from the action's own path is possible.

## Findings

- p1: shallow checkout breaks review-due's git-history reason in CI; the plan must state the fetch-depth requirement. A spike can confirm the git behaviour.
- p2: the done condition needs a remote PR run the loop cannot do alone, and depends on this repo passing a check whose rules are not yet fixed; needs an operator acceptance or a local check.

## Notes

The plan does not say where the action installs kmctl from (it is not on PyPI). Installing from the action's own checkout path is the obvious answer and the build will settle it, so it is not a finding.
