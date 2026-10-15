---
type: verdict
title: 'Verdict: okf-fields-invariant plan-reviewer round 3'
description: 'plan-reviewer verdict for round 3 of okf-fields-invariant: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T12:30:55+00:00'
slug: okf-fields-invariant
pass: plan-reviewer
round: 3
body_schema: verdict/1
---

## Summary

p2 is resolved. The single accessor gives the scan something it can find by name, and the allowed list now covers every key the code reads today. I found no new risk that would break the plan. Pass.

## Checked

- Read sites today: review_due.py:164-182 (meta.get stale_after, title; _last_verified and _sources take meta as a parameter), handoffs.py:52-72 (meta.get stale_after, generated, title, description), supersede.py:101 (status), concepts.py:130 (handoff_key). Every key is in the plan's list: stale_after, generated.at, title, description, verified[].at, sources[].resource, status, handoff_key.
- okf.front_matter (okf.py:14) is the one entry point for front matter, so "a front_matter(...) result" is a sound root for the scan.
- Link half: unchanged since round 2. No risk.

## Findings

- p1 (resolved): the read side of I4 has its own test.
- p2 (resolved): reads go through okf.field(), the scan finds it by name, and sources[].resource is in the allowed list.

## Notes

For the builder, not blocking:


- The scan rule bans reads on a name bound directly from front_matter(...). Today meta is also passed to helpers (review_due.py:179, :182) and packed into a tuple and unpacked again (handoffs.py:61, :72). A later `.get` on those names would get past the scan. The simplest tight rule: a name bound from front_matter(...) may only be passed as the first argument to field(). Under that rule the helpers and the tuple read their fields first. It is a small tightening and it does not change the plan.
- field() has to keep today's tolerance. verified can be a single mapping rather than a list (review_due.py:117), and sources entries can be bare strings rather than mappings (review_due.py:129). If field(meta, "verified[].at") and field(meta, "sources[].resource") drop those forms, review-due changes behaviour.
- The eval still has no rows. The Done-when line gives them: the write test fails on an injected key, the read test fails on an injected .get, subscript and unknown field() key, and both link forms are not reported.
