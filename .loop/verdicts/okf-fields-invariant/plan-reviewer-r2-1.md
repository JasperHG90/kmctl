---
type: verdict
title: 'Verdict: okf-fields-invariant plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of okf-fields-invariant: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T12:28:29+00:00'
slug: okf-fields-invariant
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

p1 is resolved: the plan now pins I4's read side with a second test against the same allowed-key list. A new risk, p2: the read test relies on an ast scan that has to tell front matter mappings from other dicts, and the plan does not say how. In today's code that can't be done by syntax alone, because front matter flows through parameters and nested values under ordinary names. Without a stated rule the test either fails on plugin.py's JSON dicts or quietly misses reads. The plan needs a revision, not a rethink.

## Checked

- Plan intent against the round 1 draft. The write test is unchanged and still passes on today's code, as checked in round 1.
- Read sites: grep of .get( and [" across src/kmctl/. Front matter reads are in handoffs.py, review_due.py, supersede.py and concepts.py, in the three shapes listed in p2. Non-front-matter .get calls are in plugin.py (claude JSON output), checks.py:285 and the os.environ.get call.
- okf.py's front_matter returns dict[str, Any], so type hints do not mark front matter either. _last_verified and _sources take meta: dict.
- The allowed list in the plan names generated.by/at and verified[].at, but not sources[].resource, which the code reads.
- Link half: the plan now covers reference definitions too (_REF_DEF), which closes the round 1 note. No risk there.
- The risk section says none. Nothing in it needs a spike or an operator acceptance.

## Findings

- p1 (resolved): the read side of I4 now has its own test.
- p2 (open): the ast read scan has no rule for picking out front matter mappings, and the code's current shapes defeat a purely syntactic one; sources[].resource is also missing from the allowed list. State the rule (a single accessor is the most reliable) or spike the scan against current src/kmctl/.

## Notes

The eval still has no rows. The Done-when line gives the rows: the write test fails on an injected key, the read test fails on an injected read in each of the three shapes, and both link forms are not reported.
