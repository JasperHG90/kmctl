---
type: verdict
title: 'Verdict: repo-rename plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of repo-rename: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T18:50:59+00:00'
slug: repo-rename
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach works. Spike repo-rename/1 shows APM 0.33.0 locks the package as `kmctl` at `virtual_path: apm` from the new URL, and `kmctl_package` matches on exactly those two fields. Old installs are recognised by `_old_layout`, `_names_old_package` and `OLD_PACKAGE`, and the plan keeps all three. Two scope gaps would still break the release or leave the docs wrong. First, the release script's APM pin is the old-installs example, so renaming the pattern either blocks `release set` or rewrites history (p1). Second, the old-name exception list is too narrow for docs and tests that describe v0.3.0 installs (p2). Both can be fixed by revising the plan.

## Checked

- The spike README, run.json (exit 0) and stdout. The lock lines `kmctl jasperhg90/kmctl apm` and the sub-packages from the same repo_url settle the plan's listed risk.
- src/kmctl/plugin.py: `kmctl_package` matches name and virtual_path only. `kmctl_files` compares sub-package repo_url with the package's own, so it is unaffected. `_old_layout` and `_names_old_package` match the old name in lowercase. `_old_entry` falls back to OLD_PACKAGE. `uninstall_name` builds the name from the entry's own URL, so an old `{git: ...}` entry still gets its old uninstall name.
- src/kmctl/doctor.py:178 matches apm.yml entries by `path` only, so it does not depend on the URL.
- scripts/release.py: `_INSTALL`, `_USES` and `_APM_PIN`; `pin_apm_doc`, and the count==0 refusal in `set_version`. tests/test_apm_package.py:440 asserts that every APM pin in the page moves.
- The `git grep` hit list, and the four kmctl-starter hits.
- apm/apm.yml is at version 0.3.0, so `{git: ...}` entries exist only from unreleased main. A released user with an old URL has only the string form or the v0.3.0 layout, and the plan covers both.

## Findings

- p1: renaming release.py's `_APM_PIN` either makes `release set` refuse, because the doc's only pin is the old-install example, or rewrites that historical example to the new version. Decide what the APM_DOC pin is for.
- p2: the outcome and r1 forbid the old name in docs and tests that must keep it to describe v0.3.0 installs correctly. List those exceptions in the plan and in r1.

## Notes

GitHub Action `uses: JasperHG90/Knowledge-management@...` lines in consumers' workflows rely on GitHub's redirect. The ADRs are left alone on purpose, which is the right call. The hooks.json files are generated from HOOK_COMMAND and are already in scope. In kmctl-starter, the template's default `kmctl_ref` and apm.yml `path: apm` entry against a v0.3.0 tag (which has no apm/ layout) may be a separate, existing problem. The rename does not affect it.
