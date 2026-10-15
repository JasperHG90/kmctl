---
type: verdict
title: 'Verdict: handoffs-list plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of handoffs-list: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T08:22:44+00:00'
slug: handoffs-list
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach is sound and small: read `.okf/handoffs/`, drop those past `stale_after`, sort by `generated.at`. One gap in the contract would break the downstream ticket: the output names no path or id for each handoff, so `/continue` cannot load what the user picks. Add the path (or id) to each entry and say `--json` prints `[]` when there are none, then this passes.

## Checked

- The plan's risk section says none; no spikes exist for this slug, and the eval has no rows.
- ADR 0008 and 0009: /continue lists the live handoffs newest first and loads the chosen ones; expired ones go to review due.
- The consumers: briefing.md uses counts and the newest title only (covered). handoff-and-continue-skills.md reads `kmctl handoffs --json`, offers a multi-select and loads the chosen ones, which needs a path or id per entry.
- review-due.md lists expired handoffs; this plan lists the rest, with a missing stale_after counted as live.
- The repo: src/kmctl/__init__.py holds only the Typer app; no `.okf/handoffs/` exists yet, so fixtures will be hand-written. Nothing the plan names is missing from the code.

## Findings

- p1: each entry needs a path or id, and the empty `--json` case needs a defined shape, so `/continue` can load what the user picks and parse the no-handoffs case.

## Notes

- Not findings, for the builder: skip the section's `index.md` when reading `.okf/handoffs/`. `generated.at` may be a date or a datetime (OKF allows both), so a sort on dates alone ties handoffs written on the same day. Use one rule for "stale_after has passed" here and in review-due so a handoff is never in both lists or in neither.
- Cross-ticket: if a `--key` update (handoff-and-continue-skills) leaves `generated.at` and `stale_after` unchanged, an updated handoff keeps its old place in the order and can expire early. That ticket should decide whether to refresh them.
