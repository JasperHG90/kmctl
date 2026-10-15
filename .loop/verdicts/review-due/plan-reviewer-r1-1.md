---
type: verdict
title: 'Verdict: review-due plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of review-due: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T08:19:46+00:00'
slug: review-due
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach works: three reasons from OKF's own fields, handoffs as concepts with `stale_after` (ADR 0008), the shallow-clone skip, and a callable function. The spike's evidence shows URL scheme and `git ls-files` never overlap. But the plan applies that result too broadly. It checks raw entries against `git ls-files`, which misses the path forms the OKF spec defines (p1). It also makes legal scope descriptors a permanent due reason (p2). Both are revisions, not a rethink.

## Checked

- Plan, empty eval, spike review-due/1 (README outcome, stdout, run.json, classify_sources.py). The spike tested concept resolution, but the sample held no spec-form or concept sources.
- OKF SPEC sections 5.1, 5.2 (verified may be a bare mapping, "how recent" is the latest `at`), 5.5 and 6.2.
- ADR 0006, ADR 0008 (handoffs live in .okf/handoffs/ with stale_after, so they need no new format), manifesto I4.
- Repo: src/kmctl has only a typer app in `__init__.py` and `pyproject.toml` declares the entry point, so `depends_on: []` holds.

## Findings

- p1: the git check matches raw entries against `git ls-files`, which ignores section 6.2's bundle-relative and concept-relative paths, so spec-conformant and concept sources show as 'source not found' and their changes go unnoticed.
- p2: 'source not found' as a due reason keeps concepts with legal scope descriptors due forever, and verifying cannot clear them.

## Notes

The rest can be found while building and is not a finding: the bare-mapping `verified` form, comparing a datetime with a date, and which git date to use.
