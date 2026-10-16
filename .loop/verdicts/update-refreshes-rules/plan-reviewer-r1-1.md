---
type: verdict
title: 'Verdict: update-refreshes-rules plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of update-refreshes-rules: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-16T10:59:18+00:00'
slug: update-refreshes-rules
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The plan lists no risks, and I found none that could break it.

## Checked

- `_write_rules` (src/kmctl/scaffold.py:163) loops over `RULE_FILES` and skips any path that exists. Swapping that for compare, then rewrite or skip, is a local change. `ScaffoldResult` already has `created`, `skipped` and `updated`, so the `--json` shape stays the same. Only the four `RULE_FILES` names are touched, so r3 holds by construction.
- `init` (src/kmctl/__init__.py:81) is a plain Typer command that calls `scaffold(path)`. Registering the same function a second time as `update` gives the alias without changing its options. The top-level `update` name does not clash with `kmctl plugin update`, which sits in a sub-app.
- ADR 0011 says "An existing file of the same name is kept" in one bullet of a decision that covers more than the rules. An appended correction (the plan allows this) keeps the rest of the decision in force.

## Findings

None.

## Notes

Build-time details, not findings:

- The human output labels every non-agent-file entry in `updated` as "first decision's entry" (src/kmctl/__init__.py:108). Rule files need their own label.
- tests/test_init.py:186 `test_init_rule_files_keep_an_existing_one` asserts the old behaviour and has to be changed or removed.
- This repo's own `.claude/rules/` copies of the four rules are kmctl-specific and differ from `src/kmctl/repo_rules/`. Running `kmctl update` here would replace them. Nothing in CI runs init on this repo, and the operator accepted losing edits, so I note it only.
