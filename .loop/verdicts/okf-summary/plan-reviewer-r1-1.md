---
type: verdict
title: 'Verdict: okf-summary plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of okf-summary: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-18T19:44:39+00:00'
slug: okf-summary
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

Both listed risks are settled by spike evidence that answers them. The plan can work. Two gaps need a revision before building: the `checked` field that `ack` writes isn't covered by invariant I4, and the existing `unverified` rule keeps the summary in review due, which contradicts the outcome that an edit or ack "clears it". Neither calls for a rethink, and the ticket doesn't need another split.

## Checked

- Risk 1 (commit-order freshness), spike okf-summary/1. I read README, stdout and run.json: exit 0, 10 of 10 cases pass. These include a concept in the same commit as the summary, a later summary commit, uncommitted edits (tracked and untracked), a verify stamp before and after the summary, non-concepts, and an ack that writes `checked:`. It runs in 32 to 54 ms on this repo. This answers the risk.
- Risk 2 (briefing budget), spike okf-summary/2: the worst case is 488 tokens with "summary current" and 493 with "summary behind", once the Diataxis list repeated in the Verbs line is dropped. This answers the risk.
- The vendored okf validator, tests/vendor/okf/okf_validate.py, check_concept: any non-empty `type` passes. Only index.md and log.md are reserved, and any other .md, root-level included, is a concept, just as manifesto.md is today. §11 forbids rejecting unknown keys, so `type: summary` and a `checked` key pass strict validation. checks.check_okf already requires the root index to list root concepts, and the plan has init link the summary from index.md.
- I read kinds.py (DocumentKind, `_REVIEWED` fields), okf.ALLOWED_FIELDS and `field`, manifesto I4, ADR 0009, tests/test_okf_fields.py, and review_due (`_concepts`, the unverified reason).
- The CI workflows check out with fetch-depth 0, and action/knowledge-ci.sh fetches full history when the clone is shallow. So the shallow-clone skip won't silence the stale-summary report in CI.

## Findings

- p1: `ack`'s `checked` field is a new OKF extension field, and invariant I4 / ADR 0009 require an ADR to name it, plus updates to ALLOWED_FIELDS, the manifesto's I4 wording and test_okf_fields. The plan doesn't list any of these.
- p2: the summary is a concept, so review due lists it as `unverified` forever unless a person verifies it. "An edit or ack clears it" holds only for the new reason. The plan must choose an exemption or narrow the outcome.
