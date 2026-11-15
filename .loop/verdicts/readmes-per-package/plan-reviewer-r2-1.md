---
type: verdict
title: 'Verdict: readmes-per-package plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of readmes-per-package: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-15T18:47:50+00:00'
slug: readmes-per-package
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

Round 2. All three round-1 findings are resolved, and I found no new risk that could break the plan. Pass.

## Checked

- `owns` in scripts/release_paths.py is a prefix test today. Giving kmaudit the `docs/**/kmaudit-*` paths is a small change. release_notes.py and release-tag both call it, so they follow without edits. The regenerated docs/reference/README.md stays with kmctl, which is harmless.
- AT_REF in test_docs.py matches any `kmctl@REF` URL, so kmaudit's line only matches once it is pinned. That is the case the revision now tests on a copy after `set --package kmaudit`.
- The only files outside .loop that name packages/kmaudit/docs are scripts/release.py (KMAUDIT_DOCS), release.yml:328 and docs/reference/commands.md. All three are in touches.
- kmaudit's source and pyproject never read docs/commands.md at runtime and do not ship it, so moving it changes nothing in the wheel. test_mcp.py:283 reads it through PACKAGE / "docs", and packages/kmaudit/tests is in touches.
- Tests that read the root README: test_docs.py (test_readme_install_and_links, the install-line test), test_no_audit.py:64, test_pin.py:470, test_plugin_patch.py:27, test_opencode.py:50 and test_doctor.py:971. All are under packages/kmctl/tests, which is in touches.
- facts.json matches the prose. There is one behaviour outcome, with touches covering every file the prose says changes. The plan_hash matches the round's binding.

## Findings

- p1: resolved. kmaudit-* docs pages go to kmaudit in release_paths.
- p2: resolved. The install-line test splits kmaudit's lines from kmctl's and runs on a copy after `set --package kmaudit`. README tests read packages/kmctl/README.md.
- p3: resolved. docs/reference/commands.md and scripts/release_paths.py are in touches.

## Notes

For the build, not findings:

- test_readme_install_and_links checks that every docs/ page is linked from the README by its root-relative path. In packages/kmctl/README.md the links will be `../../docs/...`, and kmctl's README probably should not have to link kmaudit-commands.md. Rewrite the test to match.
- DOC_LINES = 6 assumes every kmctl install line moves out of the root README. If the short root README keeps one, the count changes.
- .claude/rules/docs-layout.md says docs/ is for people who use kmctl. Once kmaudit's page is there, that wording is a little stale.
- action.yml sits at the root, so a Marketplace listing, if there is one, will show the short root README.

The ticket is small enough that it does not need splitting.
