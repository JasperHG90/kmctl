---
type: verdict
title: 'Verdict: audit-hermes-hardening plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of audit-hermes-hardening: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T15:57:28+00:00'
slug: audit-hermes-hardening
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach works. One Hermes run per batch keeps each argument far below the 128 KiB per-argument limit. Merging the batch blocks into one list before audit-report.py keeps that script's contract. Clearing HERMES_MANAGED_DIR is a one-word change. Two things are open, both fixable by revising the plan. First, the plan does not say how per-batch timeouts add up against the step's 40 minute timeout-minutes (p1), and its 'Could invalidate this plan: none' misses this. Second, it does not say whether batches stay grouped by kind (p2). Fail, not reject.

## Checked

- action/knowledge-audit.sh on main: one `timeout --kill-after=30s "$limit" hermes ... -z "$(cat prompt)"` call, a 30m default, and the unset line, which lacks HERMES_MANAGED_DIR. The prompt embeds the whole filtered due list plus the audit skill, the auditor text and the review skills the list needs.
- .github/workflows/knowledge-audit.yml: the audit step has timeout-minutes 40 and KMCTL_AUDIT_TIMEOUT 30m. action.yml and the how-to describe the 30-minute limit as a single limit with timeout-minutes as a second limit.
- action/audit-report.py reads the last fenced json block of one reply and validates it. If the script pulls each batch's block out (reusing the same checks, so it can name the failing batch) and writes the merged list as one block, the script needs no change and its contract holds. That is build detail, not a plan risk.
- Cross-batch context: the audit skill already sends each batch to a separate auditor agent with no shared context, so separate Hermes sessions per batch match its design. The decision-log review finds a later or superseding record by searching, and the kmctl_read tools reach the whole repository from every batch. Ten per batch is still right; nothing is lost that the skill relied on.
- No spikes exist for this ticket, and the plan lists no risks to check.

## Findings

- p1: per-batch timeouts can add up past the step's timeout-minutes. GitHub then kills the step with no message and every finished batch's findings are lost. The plan must define the timeout budget (a total budget, or per batch with a total cap that ends before 40 minutes), say which docs change, and add a row for it.
- p2: the plan does not say whether batches stay grouped by kind, as audit skill step 2 says. That decides which review skills each prompt carries and how many runs r1 should expect. State the rule and pin r1's fixture.

## Notes

- All or nothing across batches means more runs give a flaky endpoint more chances to fail the whole audit. The plan chooses this on purpose (matching today's single run), and that is a fair choice. Posting partial results would be a separate ticket.
