---
type: verdict
title: 'Verdict: review-hardening plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of review-hardening: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T11:57:41+00:00'
slug: review-hardening
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

Both round 1 findings are resolved and I found no new risk that could break the plan. The grader now joins on the same key skill-creator's own tooling uses, and the link changes alter how a target is read, not what counts as an index entry. Four small fixes in one ticket still do not need a split.

## Checked

- The plan lists no risks and the eval has no rows, so there were no spikes or acceptances to check.
- skill-creator SKILL.md lines 167-197: each eval directory gets a free name and an eval_metadata.json with eval_id and eval_name. scripts/aggregate_benchmark.py lines 86-98 reads eval_id from eval_metadata.json the same way, so a join on eval_id matches skill-creator's own reading of a run.
- grade.py still has the hard-coded FOLDER table and evals.json ids run 1 to 4, so the planned join and a doc_type per eval fit the current files.
- checks.py: `_ENTRY` matches an inline first link on a list item, and `_LINK` is the link check's pattern. Keeping reference-style definitions to the link check leaves `_ENTRY` and the module docstring's index format alone, as the plan now says.

## Findings

- p1 (grader keyed on folder names): resolved. The plan joins eval_metadata.json eval_id to evals.json id, reports and skips a folder without metadata, and tests on folder names evals.json does not hold.
- p2 (reference-style links in the index check): resolved. Reference definitions go to the link check only; an index entry stays a list item whose first link is inline.

## Notes

The SKILL.md example shows `"eval_id": 0` and `eval-0/` folders while this evals.json counts from 1, so a run agent could write an eval_id that is off by one. That would grade a run against the wrong type, not crash. It is cheap to guard when building (report an eval_id that evals.json does not hold, or compare eval_metadata.json's prompt with the eval's), and is not a reason to revise the plan.
