---
type: verdict
title: 'Verdict: adr-kmaudit-stale-lines plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of adr-kmaudit-stale-lines: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-16T06:45:39+00:00'
slug: adr-kmaudit-stale-lines
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach is sound. ADR 0012's 2026-11-14 correction names `apm/apm.yml` and `packages/kmaudit/VERSION`, which are both gone. `release-tag.yml` watches `packages/kmctl/apm/apm.yml` and `packages/kmaudit/apm/apm.yml`. A new dated correction that links ADR 0045 fits the existing test of the ADR's structure and the repo's habit of adding corrections. One gap in scope blocks the plan: the decisions index still tells readers that `apm/apm.yml` is the one version source, and the plan does not touch the index.

## Checked

- ADR 0012 in full, including its 2026-11-14 and 2026-11-15 corrections. ADR 0045's Context and Decision. ADR 0044's Amended section, which already points to ADR 0045.
- `.github/workflows/release-tag.yml`: the header comment and the `paths` filter list exactly the two apm.yml files the plan names.
- `tests/scripts/test_release_docs.py`: the section-order test only accepts `Correction, YYYY-MM-DD` headings after the skeleton, so the new section must use that heading. The existing per-package test needs `packages/kmaudit/VERSION` in some correction. The plan keeps the 2026-11-14 correction unchanged, so that test still passes.
- `packages/kmaudit/` has `apm/apm.yml` and no VERSION file. There is no root `apm/` folder.
- Grepped `.okf/` and `docs/` for `kmaudit/VERSION`, `apm/apm.yml` and `kmaudit guard`.
- Problems, Goals and Outcomes against the prose: one problem, one goal, one behaviour outcome that can ship alone, `needs: none`. These match, except for the `touches` gap in p1.

## Findings

- p1: the plan misses `.okf/decisions/index.md`, whose note on ADR 0012 repeats the stale claim, and `touches` also leaves out the test file that `checked by` implies.

## Notes

- ADR 0043 says `kmaudit guard` "stays in the CLI" in its first 2026-11-15 amendment. The amendment right after it, "the CLI slims down", says guard is gone, and ADR 0040 and audit-pipeline.md agree. Amendments are read in order and the later one wins in plain words, so this is fine and does not belong in this plan.
- ADR 0044 line 41 ("the version still comes from `apm/apm.yml`") is corrected by its own 2026-11-15 amendment that points to ADR 0045. The architecture overview already names both apm.yml files. No `docs/` page has a stale claim.
- ADRs 0001, 0013 and 0014 still call `apm/apm.yml` kmctl's package and version source, with no correction for ADR 0045. That claim is about kmctl, not kmaudit, and sits outside this ticket's title. The operator may want a follow-up ticket, but it does not block this plan.
- The row checks the *last* section of ADR 0012. If another ticket adds a correction to ADR 0012 before this one merges, the row breaks. No such ticket is open now.
