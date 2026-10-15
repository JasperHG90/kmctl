---
type: verdict
title: 'Verdict: handoff-and-continue-skills plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of handoff-and-continue-skills: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T08:19:59+00:00'
slug: handoff-and-continue-skills
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach works. The spike settles the one listed risk: a skill can read
the session id from `CLAUDE_CODE_SESSION_ID` in Bash, the same id hooks get.
Two things need a revision before building. The new key field conflicts with
invariant I4, and the update behaviour has no test in Done-when. Neither
calls for a rethink, and two risks are not enough to split the ticket.

## Checked

- Spike handoff-and-continue-skills/1: README outcome, stdout (a UUID env var
  and both docs rows found), run.json (exit 0), check.sh. The evidence answers
  the risk. The limit it notes (a literal `${CLAUDE_SESSION_ID}` in non-local
  skills) does not matter here, because the Bash env var works on its own.
- ADR 0006, ADR 0007, ADR 0008, manifesto I4 and the parts list, and the plans
  for new-concept-verbs (which hands updating to this ticket) and review-due
  (which lists expired handoffs).
- The pinned okf_validate.py 0.10.1 from the local plugin cache. It does not
  reject unknown front-matter keys on concepts, and it accepts a date-only
  `stale_after`.
- The repo is greenfield (only src/kmctl/__init__.py), so no existing code is
  contradicted.

## Findings

- p1: the session-id key field conflicts with manifesto I4 and ADR 0006,
  and the plan does not settle that.
- p2: Done-when and the eval leave out the `--key` update behaviour, which is
  the point of the ticket's spike.

## Notes

Handoffs live in the working tree, so /continue in another clone or
worktree sees only committed handoffs. This is worth one sentence in the
skill, but it does not block the plan.
