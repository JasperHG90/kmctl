---
type: verdict
title: 'Verdict: review-due-commit-order plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of review-due-commit-order: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-19T15:08:23+00:00'
slug: review-due-commit-order
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

No open risk could break the plan. Risk 1 is settled by a spike, and the operator accepted risk 2.

## Checked

- Risk 1 (wrong verification commit, or too slow): settled by spike:review-due-commit-order/2. All 33 rule cases passed (squash, rebase+ff and merge-commit landings, issue #18, re-verify with and without --stale-after, uncommitted verify, docs pages with and without verified). The batched walk costs 0.359 s in the worst case and comes out net negative once the git log -1 calls go. The spike says plainly that the batched walk's choice of V was not tested and that a union pathspec dropped 33 versions (merges and renames). The plan answers this by requiring a test that the batched walk picks the same V as a per-file log. If that test cannot be made to pass, the per-file walk still works: it only runs for verified files (none today), so it is a slower fallback, not a broken plan.
- Risk 2 (a verify-then-edit squashed into one commit goes unseen): the operator accepted it (accepted_risks, 2026-10-19T15:07:13Z).
- src/kmctl/review_due.py compares `git log -1 --format=%cI` with verified[].at, for concepts and for docs pages, as the plan says.
- Shallow clones and non-git trees already skip history through `_history_skipped`, and the action and CI fetch full history, so the new walk creates no shallow-clone failure.
- kmctl verify changes only `verified` and `stale_after` (src/kmctl/verify.py), which matches the fields the edited-after rule ignores. `kmctl check --fix` rewrites only indexes, so it will not raise a false `edited after verification`.
- ADRs 0006, 0023 and 0027 and the docs-layout instruction file exist.
- Scope fits one ticket: one module, two closely linked reasons, and their docs.

## Findings

None.
