---
type: verdict
title: 'Verdict: okf-fields-invariant plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of okf-fields-invariant: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T12:26:39+00:00'
slug: okf-fields-invariant
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The plan works as written on both halves. Every key kmctl writes today is a spec
field or handoff_key, and the link fix is a small change to one regex. One scope
gap: I4 covers what kmctl reads as well as what it writes, and the test only pins
writes. Marking I4 enforced on that test would overstate it, which is what
.claude/rules/manifesto-invariants.md guards against. This is a revision, not a
rethink.

## Checked

- The plan's risk section says "none". I found no risk that breaks the approach.
- Keys written: concepts.py `_front_matter` writes type, title, description,
  tags, generated (by, at), status (decisions), stale_after (handoffs) and
  handoff_key (with --key). scaffold.py writes the same family on the manifesto
  plus okf_version on .okf/index.md, which SPEC §8 and §12 allow. supersede.py
  only sets status: deprecated. docs.py writes no front matter, so `new doc`
  passes trivially. All of these are in SPEC §4.1, §5 or §12, or in ADR 0009, so
  the test can pass today without code changes.
- Keys read: handoffs.py, review_due.py, supersede.py and concepts.py read
  stale_after, generated.at, title, description, verified, sources, status and
  handoff_key. All of these are allowed today, but no planned test pins them.
- Link half: checks.py `_TARGET` is `(<[^>\n]*>|[^)\s]+)`. For `[x](<a>b.md>)`
  the bracket branch fails and the bare branch matches `<a>b.md>`, so `_target`
  strips it to `a>b.md` and reports it broken. Stopping the bare branch from
  starting with `<`, and keeping `<` out of the bracket branch, matches
  CommonMark. `_REF_DEF` has the same shape and should get the same change. That
  is a build detail.

## Findings

- p1: I4's read side is not pinned by the planned test, so marking it enforced
  overstates what the test checks. Either narrow I4's text to what kmctl writes,
  or extend the test (or add a second one) to cover the keys kmctl reads.

## Notes

The eval has no rows yet. The plan's "Done when" line gives the two rows to
write: the I4 test fails on an injected unknown key, and `[x](<a>b.md>)` is not
reported.
