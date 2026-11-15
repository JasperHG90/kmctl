---
type: verdict
title: 'Verdict: apm-per-package reviewer round 1'
description: 'reviewer verdict for round 1 of apm-per-package: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-15T07:18:19+00:00'
slug: apm-per-package
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The move is complete and correct. kmctl's APM package lives in packages/kmctl/apm, kmaudit's version in packages/kmaudit/apm/apm.yml, and no apm/ or packages/kmaudit/VERSION is left. Builds, releases, the consumer entry, doctor, plugin patch, uninstall, the starter and the repository's own tooling all follow, and consumers on releases up to v0.12.2 (path: apm) are still recognised. I re-ran the gates and they are green. One stale docstring is the only finding, and it does not block.

## Checked

- `loopctl gate stamp` in the worktree: lint, format, tests, integration and eval rows r1 to r7 all pass. Stamp: green, cb9d5e473ac4e0ced84d78a279953713c89f8d0432eea9e9cda9c867f2672b80.
- Read the whole diff outside the renamed .apm files: plugin.py, doctor.py, antigravity.py, opencode.py, kinds.py, hatch_build.py, both pyprojects, release.py, check_wheel.py, sync_antigravity_rules.py, both release workflows, the triage workflow, .pre-commit-config.yaml, starter/apm.yml.jinja, action/agent.py, README, the three docs pages, cli-version-floor and the release skill, the manifesto, summary, overview, audit-pipeline, log, ADR 0044's amendment and the new ADR 0045.
- Old consumers: kmctl_package and _names_old_package match either path through PACKAGE_PATHS. kmctl_files folds sub-packages under the found package's own virtual_path, so a mixed lock does not fold the other path in (a test covers this). doctor._manifest_targets accepts either path. uninstall_name uses the entry's own path. pin.py goes through kmctl_package. _old_entry keeps the ADR 0013 string form on ROOT_PACKAGE_PATH, which is right for that layout.
- new_entry at the tree's 0.12.2 writes path apm with ref v0.12.2, which is right for the real v0.12.2 tag. Tests patch cli_version on both sides of the cutoff, including rc and dev builds. doctor's _update_fix gives the whole entry, and test_old_release_entry_gets_the_whole_new_entry asserts the exact fix line (path packages/kmctl/apm, ref v0.13.0) for a {path: apm, ref: v0.12.2} project.
- release-tag's first run after the move: manifest_version falls back to apm/apm.yml when the moved file is missing. current() deliberately does not fall back. The workflow test runs the before-read bash against a pre-move tree and gets "raised". The merge of agent-audit into main adds the moved apm.yml at an unchanged version, which gives "unchanged". kmaudit's new apm.yml starts at a .dev version, which skips. release_notes.py's ownership rule still puts packages/kmctl/apm under kmctl.
- Starter: copier's validator forces kmctl_ref to be a release tag, so the int parse in apm.yml.jinja cannot fail on a branch name. The cutoff matches justfile.jinja's. test_render_apm_entry_path checks each ref against plugin.package_path, so a cutoff that drifts from LAST_ROOT_RELEASE fails it. The bootstrap integration test bumps the tree past the cutoff and asserts the entry path, the lock's virtual paths for the package and both sub-packages, and that doctor passes.
- Pre-commit: the files: pattern now names packages/kmctl/apm/(claude|antigravity)/.apm/instructions/. The test checks both moved rule paths match and that the old apm/ path and a skill path do not. The sync script's SOURCE and TARGET are asserted.
- Eval rows: r1 (layout test asserts no apm/ and no VERSION; a wheel-build test checks both wheel versions against their apm.yml and kmctl's _skills, _agents and _rules), r2 (release.py fallback, the moved manifest is preferred when both exist, kmaudit set writes apm.yml, and the workflows stage and trigger on the moved paths with no old path named), r3, r4, r5 (cutoff_matches_tags now checks all three layout markers per tag) and r6/r7 each assert their fails_when. None is skipped or constant.
- Docs: README, both how-tos, commands.md and cli-version-floor each give path packages/kmctl/apm, say to write path apm for v0.12.2 and older, and say an upgrade across the cutoff changes the path. The uninstall name follows the path. ADR 0045 matches the code. Older ADRs keep their prose and move only their sources, as the plan says.
- Builder notes (1) to (5) all hold. The redundant sdist force-include is harmless, and a layout test keeps it inside the package.

## Findings

- f1: The `_names_old_package` docstring still points at `write_manifest`, which no longer exists. The change rewrote the line just above it. Under the pre-existing-issues rule it should be fixed while the docstring is open: say what actually happens to a `{git, path}` entry when the lock shows no old layout, or drop the clause. A plain docstring fix, so it does not block.

## Notes

The cutoff v0.12.2 is still hard-coded in two starter templates as well as in LAST_ROOT_RELEASE. That was already true of justfile.jinja, and the render tests catch drift, so I raise no finding.
