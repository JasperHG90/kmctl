---
type: verdict
title: 'Verdict: new-concept-freshness plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of new-concept-freshness: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T17:22:46+00:00'
slug: new-concept-freshness
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

No open risk could break the plan. Both round 1 findings are settled in the contract, and each row matches a done-when item.

## Checked

- p1: `_resolve` (src/kmctl/review_due.py:90) checks candidates against git's tracked set, so the build has to pull the candidate order out into something both callers share, with an on-disk check for `kmctl new` and the tracked check for `review due`. That is a small refactor, not a risk. It also has to keep the "must be under the repository root" check that `_resolve` gets from `relative_to(root)`. One consequence is fine: a source that exists but has not been committed yet shows in `review due` as the notice "source not resolved" until it is committed. That is a notice, not a wrong reason.
- p2: the handoff refusal sits next to the existing `--key` guard (concepts.py:205). `--stale-after` on a handoff that `--key` updates goes through `_front_matter` again, so the new value replaces the old one, which matches the plan.
- Fields: `sources`, `sources[].resource` and `stale_after` are already in ALLOWED_FIELDS (okf.py:54-58), so the I4 test (r4) needs no ADR.
- Rows against done-when: r1 covers the duration forms, the date form, every kind and the handoff default being replaced. r2 covers past and unparseable values. r3 covers source order and mapping shape, untracked files accepted, missing paths refused, handoffs refused, and the source-changed reason after verify and commit. r4 covers the strict validator and I4. r5 covers the block, plus the help and reference page the intent lists. r6 runs the full suite.
- "Could invalidate: none" holds. I found no unlisted risk. The ticket is one ticket's worth of work.

## Findings

- p1: resolved. A source must exist on disk, found by `_resolve`'s order; git is not needed.
- p2: resolved. `kmctl new handoff` refuses `--source`.

## Notes

No spike needed. Small details are left to the build: what a bare date means (midnight UTC, so today's date counts as past), clamping month ends, and `0d`.
