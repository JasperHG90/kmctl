---
type: verdict
title: 'Verdict: repo-uses-apm plan-reviewer round 3'
description: 'plan-reviewer verdict for round 3 of repo-uses-apm: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T19:09:21+00:00'
slug: repo-uses-apm
pass: plan-reviewer
round: 3
body_schema: verdict/1
---

## Summary

Both round 2 findings are resolved, and no new risk could break the plan. The build cannot pass until PR 139 merges, which is what the plan intends.

## Checked

- `gh pr view 139 -R JasperHG90/skills`: still OPEN, head 2c1b41c, no merge commit. At that head, `rules/python-testing.instructions.md` has the `## Test tiers` heading and the `measure-before-marking`, `run-your-own-test` and `every-tier-runs-somewhere` constraints at the same lines as the local file. Upstream `main` has none of them, so r5 fails on any pin from before the merge.
- Pinning to the PR head instead of the merge commit would pass r5. r1's fails_when rules that out ("does not include the merge"), so the two rows together close the gap.
- tests/test_rules.py:32 `_aim_managed` reads `aim.toml` `source_path` names. Mapping `apm.yml` `<name>.instructions.md` entries to the installed `<name>.md` gives the same set, and pyproject.toml:37 is the only other mention. r6 covers both.
- Each row maps to a done-when item. r2: paths, scoping, bodies and skills. r5: python-testing text. r6: test_rules.py. r3: aim gone and AGENTS.md text unchanged. r4: gates. r1: the apm.yml and lock file from the intent.

## Findings

- p1 (resolved): r5 and r1 now make the PR 139 merge a hard precondition.
- p2 (resolved): test_rules.py and pyproject.toml are in scope, and r6 checks them.

## Notes

The `-k managed_from_apm` filter in r6 deselects test_rules.py's other tests, but r4 runs them all, so "or fails" is still covered. That is a detail for the build, not a plan risk. The ticket does not need splitting.
