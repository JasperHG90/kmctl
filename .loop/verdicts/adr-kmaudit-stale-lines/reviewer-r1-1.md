---
type: verdict
title: 'Verdict: adr-kmaudit-stale-lines reviewer round 1'
description: 'reviewer verdict for round 1 of adr-kmaudit-stale-lines: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-16T07:09:41+00:00'
slug: adr-kmaudit-stale-lines
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The five corrections and the two index notes match the repo as it is today. Each correction is dated, links ADR 0045, names `packages/kmctl/apm/apm.yml`, and leaves the earlier text as the record. ADR 0012's correction names both apm.yml files and both paths that release-tag.yml watches. The new tests fail when the behaviour they guard breaks. The gates are green.

## Checked

- Gates: `loopctl gate stamp` from the worktree gave lint, format, tests, integration, eval-row r1 and eval-row r2 all pass, ending "stamp green: 61724f2e037b96ca8b3163f0e2a474cfce334a56dc8691d947f81c1958e723a9". `prek run --files` over the changed bundle files passed `kmctl check --fix` and `okf validate --strict` and left the tree unchanged.
- Facts against the repo: `apm/` and `packages/kmaudit/VERSION` are gone. `packages/kmctl/apm` holds apm.yml, claude/ and antigravity/, and each sub-package has the four rules under `.apm/instructions/`. `packages/kmaudit/apm/apm.yml` carries `version: 0.1.0`. release-tag.yml's `paths` filter is exactly the two apm.yml files, with a matrix of kmctl and kmaudit, so "once per package" holds. `kmctl.plugin` has LAST_ROOT_RELEASE = "v0.12.2", PACKAGE_PATH = "packages/kmctl/apm" and ROOT_PACKAGE_PATH = "apm", which backs the "releases up to v0.12.2 still have the package at apm/" lines and ADR 0014's `path: packages/kmctl/apm` line. Every claim also agrees with ADR 0045's Decision.
- The corrected text: each new correction quotes the earlier section correctly. That covers ADR 0001's 2026-10-16 correction, ADR 0011's last 2026-10-19 correction, ADR 0012's 2026-11-14 correction (which names `apm/apm.yml` and `packages/kmaudit/VERSION` as release-tag's trigger), ADR 0014's Decision and ADR 0020's Decision.
- Row r1: `test_decision_names_kmctl_s_apm_package_since_adr_0045` needs a `## Correction, ` section that holds both the backticked path and the ADR 0045 link. `test_decision_0012_names_both_version_sources_since_adr_0045` reads the paths filter from the workflow, checks that kmaudit's apm.yml is in it (so an empty parse cannot pass by default), and needs each watched path in a correction that links 0045. I mutated a scratch copy: a broken 0045 link in ADR 0020 failed the parametrized test, and taking kmaudit's apm.yml out of ADR 0012 failed the 0012 test.
- Row r2: `test_index_note_names_no_path_adr_0045_removed` cuts out the note for each of the two index entries and rejects a bare `apm/apm.yml` and `in apm/`. Putting "in apm/" back into the 0014 note in the scratch copy failed it. The whole file passes, including `test_the_bundle_passes_kmctl_check`.

## Findings

None.

## Notes

ADR 0014's front-matter description still says "the APM package in apm/". That fits the plan's rule that earlier sections stay as the record, and the index note, which readers scan, is now corrected.
