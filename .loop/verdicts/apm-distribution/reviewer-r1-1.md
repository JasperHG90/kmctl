---
type: verdict
title: 'Verdict: apm-distribution reviewer round 1'
description: 'reviewer verdict for round 1 of apm-distribution: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-16T11:03:57+00:00'
slug: apm-distribution
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan says: apm/apm.yml depends on exactly `{git: parent, path: plugin}` and okf-skills at a full commit, plugin/ has no apm.yml, release.py `set` writes the manifest and both apm.yml copies and moves the APM page's pins, `current` refuses a missing or differing copy, release.yml stages the new files, and ADR 0013, the manifesto, the architecture overview and the docs agree. Nothing here breaks the 0.2.0 release. Two non-blocking findings.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests, integration and r1 to r5 all pass; "stamp green: 4c55c9443a5da9c8e66105d0eb378883538606f5c5aac94090757014560ef2e3".
- `uv run pytest -q`: 469 passed, 12 deselected. `ruff check`: all checks passed; `ruff format --check`: 88 files already formatted.
- r1: the tests assert name == kmctl, a non-empty version, deps keys == ["apm"], exactly two entries with the plugin entry equal to `{git: parent, path: plugin}` and okf matching a 40-hex pin, and no apm.yml under plugin/. Each fails_when clause is covered.
- r2: the set test checks the manifest and both apm.yml at 0.2.0 and that only the version line changed; current is tested refusing a differing copy (both files, parametrized) and a missing apm/apm.yml.
- r3: the integration test serves this tree over git smart HTTP, installs with apm-cli 0.33.0, compares all 7 skills file by file and the agent byte for byte, finds `kmctl briefing` in SessionStart in settings.json, requires an okf skill, checks no path names any of the 16 dev items, and checks the lock for jasperhg90/skills.
- r4: schema and skeleton validation of ADR 0013, the named phrases, the manifesto Parts, CLI-before-apm order, no -g, private/GitHub token, the link, and set moving both page pins.
- The "-g refuses git: parent" claim: confirmed in apm_cli/install/package_resolution.py (GIT_PARENT_USER_SCOPE_ERROR at user scope).
- release-tag.yml with an empty OLD: `release.py compare "" 0.2.0` prints raised, so the edge the builder raised cannot fail the first release.
- `_APM_PIN` regex leaves apm.yml and longer paths alone; set refuses before writing anything if a pin or version line is missing.

## Findings

- f1 (hardening, non-blocking): the before-commit `current || true` now swallows apm.yml refusals too and turns them into "raised". Reading only the manifest for OLD (for example a `--manifest-only` flag or a direct json read) keeps the lowered-version guard. Not needed for 0.2.0.
- f2 (docs, non-blocking): the APM page shows v0.2.0 before that tag exists; the release PR fixes it, but a reader on main in between gets a failing command. Also reword step 3 to "prints the briefing".

## Notes

The r3 eval row does not run the hook with the CLI installed (a plan "done when" item); spike 5 covered it, and the row as written is met.
