---
type: verdict
title: 'Verdict: apm-per-package plan-reviewer round 3'
description: 'plan-reviewer verdict for round 3 of apm-per-package: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-15T05:36:30+00:00'
slug: apm-per-package
pass: plan-reviewer
round: 3
body_schema: verdict/1
---

## Summary

All three round-2 findings are resolved, and I found no new risk that could break the plan. Pass.

## Checked

- p1: read test_cutoff_matches_tags and subdirectory_fragment in the root-release-cutoff worktree. Extending the per-tag check from packages/kmctl/pyproject.toml to packages/kmctl/apm/apm.yml vs apm/apm.yml is a small change to that test. The starter bootstrap test bumps the served tree to a test-only release after v0.12.2 (`tree_repo(..., bump=True)`), so the integration check in "checked by" can run before any real release after the cutoff exists.
- p2: the only ref advice in code is `_update_fix`. `new_entry` writes PACKAGE_PATH. The starter justfile already picks kmctl_src from kmctl_ref with a version compare, and the plan mirrors that for apm.yml.jinja.
- p3: re-grepped apm/ across the tracked tree. Everything that resolves the path at runtime, build time or hook time is in touches.
- release-tag fallback: `manifest` runs against a worktree of `github.event.before`. kmctl needs the apm/apm.yml fallback, as the plan says. kmaudit needs none: packages/kmaudit/VERSION has never been on main and holds 0.1.0.dev0, and no kmaudit-v* tag exists. An empty OLD there counts as a first release, which is correct.
- 2.0 facts: one behaviour outcome that fixes P1 and serves G1, with no needs. Touches now match the prose. The checked-by list covers each consequence the prose names.

## Findings

- p1: resolved. The plan says both moves ship in one release, and the extended tag test enforces it.
- p2: resolved. Doctor's fix, the docs and the starter give the whole entry, and a doctor test covers it.
- p3: resolved. Touches cover every site that resolves the path.

## Notes

As round 2 said, whether `apm uninstall` accepts the longer `.../kmctl/packages/kmctl/apm` name is a build-time detail for the served-repo tests in test_doctor and test_plugin_patch. The ticket is large but mechanical, so no split is needed.
