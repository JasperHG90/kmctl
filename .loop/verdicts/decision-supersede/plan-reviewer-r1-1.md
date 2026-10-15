---
type: verdict
title: 'Verdict: decision-supersede plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of decision-supersede: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T08:12:38+00:00'
slug: decision-supersede
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach works: a front-matter edit, an appended `## Correction, YYYY-MM-DD` section, a back-link in the new record and an index update together meet the decision-record rule. Two gaps in the contract need an answer before building: who writes the log.md line (p1), and how writing `decision_status` fits invariant I4 (p2). Neither needs a spike, and the ticket does not need splitting.

## Checked

- The plan lists no risks and cites no spikes. The eval has no rows.
- `.claude/rules/okf-bundle.md`: the decision rules (status stable/deprecated, decision_status wording, append-only corrections, a reversal written in both records) agree with the intent. The logging constraint does not appear in the plan.
- `.okf/manifesto.md`: Parts names "supersede a decision" as kmctl bookkeeping. I4 limits kmctl to fields the spec defines.
- The okf 0.10.1 validator: `STATUS_VALUES = {draft, stable, deprecated}`, so `status: deprecated` validates. It has no `decision_status`.
- The okf CHANGELOG: a supersession counts as a lifecycle event that gets a log.md bullet.
- Existing records (ADR 0005, 0006) and `.okf/decisions/index.md`: both records carry `decision_status` and `decided_on`. The index lists entries as one bullet with a description.
- `src/kmctl/`: only the Typer root exists. The dependency new-concept-verbs (and scaffold-init before it) is not built, and the plan says so in `depends_on`.

## Findings

- p1: the plan does not say whether log.md is written, and the okf gate depends on that answer.
- p2: writing `decision_status` conflicts with I4 as worded. An operator acceptance or an I4 rewording settles it.

## Notes

Things to settle while building, not blocking: existing records repeat `- Status: Accepted` in the body. Because the plan never rewrites the body, that line stays stale, and the correction section is what corrects it. Done-when could also require the strict okf validator to pass, as new-concept-verbs does. The plan should also say how the decisions index shows the old entry as superseded.
