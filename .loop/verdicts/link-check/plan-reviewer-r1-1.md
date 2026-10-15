---
type: verdict
title: 'Verdict: link-check plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of link-check: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T08:12:38+00:00'
slug: link-check
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach is sound and small. Two points about what the contract means need settling before building. OKF's recommended `/`-rooted link form falls outside "relative links" (p1). Failing on broken `.okf/` links conflicts with OKF §6.1 and repeats the okf validator, which knowledge-check promised not to do (p2). Neither point needs a rethink; both need a sentence in the plan.

## Checked

- Read the plan (risks: none), the empty eval, the ticket state and the knowledge-check plan it extends. `src/kmctl` holds only `__init__.py`, so `kmctl check` does not exist yet; this ticket depends on knowledge-check for it.
- Manifesto line 50 lists "check indexes and links" as kmctl's job, so the scope fits the design.
- Current `.okf/` links are all file-relative (`.okf/index.md`, `.okf/decisions/index.md`).
- okf plugin 0.10.1: SPEC.md §6.1 (two link forms, `/` is bundle-relative and recommended; consumers MUST tolerate broken links), skills/okf/SKILL.md:42 (prefer bundle-relative), skills/validate/scripts/okf_validate.py check_links (already warns on broken `.okf/` cross-links).

## Findings

- p1: `/`-rooted bundle-relative links are OKF's recommended form, and the plan leaves them undefined, so the check either misses them or reports false failures.
- p2: Making broken `.okf/` links fatal conflicts with OKF §6.1, and the plan repeats the okf validator's link check against knowledge-check's no-repeat contract without saying so.

## Notes

No spike is needed; both points are decisions for the plan, not questions a test run would answer. One ticket is the right size.
