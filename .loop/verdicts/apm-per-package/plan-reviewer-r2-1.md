---
type: verdict
title: 'Verdict: apm-per-package plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of apm-per-package: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-15T05:21:11+00:00'
slug: apm-per-package
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

The approach works. APM installs a package from a nested path whose own apm.yml pulls in ./claude and ./antigravity, and the evidence for that is good enough. No finding means the plan must be rethought. Three things need a revision. The plan reuses the Python-code cutoff for the APM path without making sure both moves ship in the same release (p1). The doctor and docs upgrade advice ('set the ref') breaks for a project crossing the cutoff (p2). The touches list leaves out the antigravity sync script, its pre-commit trigger, rule globs, OKF resources and about seventeen test files (p3).

## Checked

- Read the plan, its facts, and its empty eval. No .loop/spikes/apm-per-package folder exists. The Evidence section describes a plain-script run with apm-cli 0.33.0, the pinned version. It installed from `path: packages/kmctl/apm` at a test tag and recorded the virtual paths packages/kmctl/apm, packages/kmctl/apm/claude and packages/kmctl/apm/antigravity. That answers the nested-install risk. apm/apm.yml uses relative `./claude` and `./antigravity`, which is consistent with the result. The starter bootstrap integration test repeats the check at build time. The one weakness is that no output is stored to re-read, only the plan's transcript. I accept it because the same question gets re-run by the gate.
- Read root-release-cutoff's plan. It provides LAST_ROOT_RELEASE in plugin.py as the subdirectory cutoff and a tag test tied to packages/kmctl/pyproject.toml. Tags: v0.12.2 is the latest.
- Grepped `apm/`, `"apm"` and `path: apm` across packages/, scripts/, action/, action.yml, .github/, tests/, starter/, docs/, .claude/, .okf/ and .pre-commit-config.yaml.
- Read plugin.py (PACKAGE_PATH, new_entry, _names_old_package, kmctl_package, kmctl_files, uninstall_name), doctor.py (_manifest_targets, _update_fix, the ref check), hatch_build.py, kmctl's pyproject build sections, release.py's constants, check_wheel.py, sync_antigravity_rules.py and cli-version-floor.md.
- 2.0 facts: one behaviour outcome. It fixes P1 and serves G1, and that matches the prose. P1 combines 'kmctl's package is at the root' and 'kmaudit has no package', but the operator asked for both as one change, so I am not raising it. One outcome means split is not a concern apart from touches (p3).

## Findings

- p1: the shared cutoff assumes both moves ship in the same release, and nothing guards that. It is a premise finding because new_entry, the starter and the docs all rely on it.
- p2: across the cutoff, doctor's update fix and the docs' upgrade steps produce a failing apm install.
- p3: touches leave out the sync script, the pre-commit trigger (which would go quiet with no error), rule globs, OKF resources, ADRs and many tests.

## Notes

The ticket is big but mechanical: one `git mv` plus path updates. I do not think it needs splitting. uninstall_name already builds the name from the entry's path. Whether `apm uninstall` accepts `.../kmctl/packages/kmctl/apm` is a build-time detail that the existing served-repo tests in test_doctor and test_plugin_patch will answer.
