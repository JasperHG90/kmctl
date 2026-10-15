---
type: verdict
title: 'Verdict: audit-hermes-hardening plan-reviewer round 3'
description: 'plan-reviewer verdict for round 3 of audit-hermes-hardening: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T15:58:58+00:00'
slug: audit-hermes-hardening
pass: plan-reviewer
round: 3
body_schema: verdict/1
---

## Summary

Both round 1 findings are resolved. p1: the timeout is now one total budget, with each batch given the time left and a named failure before the step's 40 minute limit; r5 tests it. p2: batches are grouped by kind with only that kind's review skill, and r1 pins 12/8/5 concepts to 4 runs. I found no new risk that could break the plan. Pass.

## Checked

- action/knowledge-audit.sh on main: one `timeout --kill-after=30s "$limit" hermes ... -z "$(cat prompt)"` call, and the unset line without HERMES_MANAGED_DIR. The prompt is built once from the whole filtered due list, so splitting by kind and batch is a local change to that one block and the run after it.
- action/audit-report.py reads the last fenced json block and checks each finding. An empty list is valid, so a batch that answers with `[]` passes, and only a missing or malformed block fails, matching the plan's "no usable findings". Writing the merged list as one block keeps its contract.
- Budget: the default 30m plus the 30s kill-after ends well before timeout-minutes 40. Working out "time left" means turning the KMCTL_AUDIT_TIMEOUT string (as `timeout` takes it, such as 30m or 2s) into seconds. That is build detail.
- Existing tests that r4 keeps: test_read_only_time_limit expects "time limit" in stderr and a stop within 20s on a 2s budget; test_prompt_and_findings expects the audit skill, auditor text and decision-log-review skill in the prompt and practices-review absent. Both still fit a one-batch, decisions-only fixture under the new design, as long as the budget message keeps the words "time limit".
- Rows against done-when: r1 is the 25-concept batching item, r5 the total-budget item, r2 the batch-without-findings item, r3 the HERMES_MANAGED_DIR item, and r4 "the other audit tests pass". Each done-when item has a row and each row has an item.
- No spikes exist for this ticket. The plan lists no risks, and after p1 and p2 none is left that needs one.

## Findings

- p1: resolved. The total budget, the docs it keeps true, and row r5 answer it.
- p2: resolved. Grouping by kind, per-kind review skills, and r1's 12/8/5 fixture answer it.

## Notes

- The budget-exhausted message should keep "time limit" in its wording, or test_read_only_time_limit (under r4) has to change with it.
