---
type: verdict
title: 'Verdict: adapt-copied-rules plan-reviewer round 3'
description: 'plan-reviewer verdict for round 3 of adapt-copied-rules: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T06:07:33+00:00'
slug: adapt-copied-rules
pass: plan-reviewer
round: 3
body_schema: verdict/1
---

## Summary

Round 2's p3 is resolved. The planned-location list now covers every section the manifesto names and the root `action.yml`, and the done check says how to treat a cited page that does not exist yet: drop it. No open risk could break the plan. The scope stays one ticket.

## Checked

- Read the revised plan and my round 2 verdict. The eval has no rows; there are no spikes; the plan lists no risks.
- Confirmed the aim-managed set from `aim.toml` (13 rules), which leaves the 12 non-aim rules the plan names.
- Re-listed the backticked paths in the 8 rules the plan keeps. Each one now either exists (`.okf/`, `.okf/manifesto.md`, `.okf/index.md`, `.loop/`, `README.md`), sits under a planned location (`.okf/architecture/`, `.okf/proposals/`, `.okf/prototypes/<name>/`, `docs/README.md`), or is a specific page that does not exist yet (`.okf/architecture/cli-and-plugin.md`, `.okf/architecture/loop-state.md`, `.okf/practices/*.md`, `.okf/proposals/v2-build-plan.md`, `scripts/check_okf.py`). The plan says that last group is dropped, which none of the kept rules depend on to keep their subject.
- Checked v1/v2 mentions in the kept rules. All are loop-harness history in WHY lines or section descriptions, so removing them does not empty any rule.
- Links between rules after the deletions (okf-bundle to manifesto-invariants.md, data-management to artifact-outputs.md) are caught by the path clause, as intended.

## Findings

- p1 (resolved): planned folders stay allowed in globs and paths.
- p2 (resolved): loopctl may be named as this repository's ticket tool.
- p3 (resolved): the manifesto's .okf/ sections and the root action.yml are planned locations; a cited page that does not exist yet is dropped.

## Notes

Section names like `decisions/` or `index.md` written relative to `.okf/` in okf-bundle are relative paths; the builder can resolve them against `.okf/`. That is a build detail, not a plan risk.
