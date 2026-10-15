---
type: verdict
title: 'Verdict: review-hardening plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of review-hardening: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T11:56:34+00:00'
slug: review-hardening
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

Three of the four fixes hold as planned. The timestamp, non-UTF-8 kept file and percent-decoding, query, angle-bracket and single-quote link fixes rest on code that exists and behaves as the plan says. The grader fix rests on a wrong premise about how skill-creator names run folders (p1). The link fix leaves open whether reference-style links change the index-entry contract (p2). Neither needs a rethink, only a revision. Four small fixes in one ticket do not need splitting.

## Checked

- The plan lists no risks and the eval has no rows, so there were no spikes or acceptances to check.
- scaffold.py:85-98: `index.read_text()` and `log.read_text()` are called with no encoding and nothing catches decode errors, after the other files are written. The fix fits.
- okf.py:40-52: `as_datetime` calls `astimezone(UTC)` with nothing around it. I confirmed that YAML parses `0001-01-01T00:00:00+01:00` to an aware datetime and that `astimezone(UTC)` raises OverflowError. The callers (handoffs.py:61 and :77, review_due.py:118 and :191, has_passed) already handle None, so returning None is safe.
- checks.py: `_ENTRY` and `_LINK` read the targets, and `_entries` and `_links` split off the anchor only. Percent-decoding and dropping the query in both places is local to the code. The `skip_entries` matching in `_links` must use the same normalised target, which is an implementation detail.
- grade.py:16-24 uses a hard-coded FOLDER table keyed by eval_dir.name. I read skill-creator's SKILL.md (lines 167-196) and references/schemas.md (evals.json and eval_metadata.json) in ~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator/ to see how run folders get their names.

## Findings

- p1 (grader keys on a name skill-creator never uses for folders): skill-creator's folder names come from the agent at run time and are tied to evals through eval_metadata.json's eval_id. A `name` field in evals.json does not make fresh runs gradable. Join on eval_metadata.json eval_id to evals.json id instead, with doc_type on each eval, and test with a run folder whose name is not in evals.json.
- p2 (reference-style links in the index check change the entry contract): the plan should say whether `- [x][ref]` is an index entry and update the documented format to match, or keep reference handling to the link check.

## Notes

Running a spike is not needed for either finding. p1 is settled by reading skill-creator's instructions, and p2 is a scope decision.
