---
type: verdict
title: 'Verdict: root-release-cutoff reviewer round 1'
description: 'reviewer verdict for round 1 of root-release-cutoff: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-15T05:43:11+00:00'
slug: root-release-cutoff
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The cutoff moves to v0.12.2 at every site the plan names, and all of them go through one rule. `kmctl.plugin` holds `LAST_ROOT_RELEASE`, `tag_version` and `subdirectory_fragment`. `pin.uvx_source` and `HOOK_INSTALL` (via `hook_install`) call them. The starter compares against `[0, 12, 2]`. `release.py set` writes the fragment only after the cutoff and strips it when it re-pins at or below it. A test holds the two copies of the cutoff equal, and an integration test ties the cutoff to the clone's tags. Nothing blocks.

## Checked

- Gates: `loopctl gate stamp` in the worktree ran green: lint, format, tests, integration and eval rows r1 to r6 all pass, stamp 57438d47e7ac90f224d72ad6b9fc749f59f3cbff583805867aa5bb1a4743b599. `kmctl check` reports all checks passed.
- The v0.12.2 tag tree has `src/` and no `packages/`. Its apm.yml version, both hooks.json hints (`@v0.12.2`, no fragment) and copier default match what `set 0.12.2` wrote on this branch.
- Boundaries: v0.12.2rc1 gets no fragment in all three implementations. In plugin it sorts below v0.12.2. In the starter the rc suffix is stripped, giving [0,12,2], which is not greater than the cutoff. In release.py, packaging's Version puts 0.12.2rc1 below 0.12.2. v0.12.3rc1 gets the fragment in all three. Refs that are not release tags (a branch, `$tag` in the release notes template, a dev version in the hook hint) get the fragment, as the plan says.
- r1: the parametrised test_pin and test_plugin cases cover v0.12.1 and v0.12.2 (empty) and v0.12.3rc1 and v0.13.0 (fragment). test_install_hint_names_release still compares hooks.json with hook_entry via hook_install, and test_hook_install_is_this_release_s ties HOOK_INSTALL to the helper.
- r2: the starter test renders through copier and asserts the exact kmctl_src line for each ref.
- r3: a new test runs `set 0.13.0` and then `set` at 0.12.2, 0.12.2rc1 and 0.12.1, and asserts no fragment on the four install lines or the hooks. The existing test asserts exactly one fragment after repeated sets above the cutoff. test_release_py_cutoff_is_plugin_s compares the two constants.
- r4: test_cutoff_matches_tags checks `git cat-file -e TAG:packages/kmctl/pyproject.toml` against `tag > LAST_ROOT_RELEASE` for each release tag, and fails if the clone has no tags. With the old v0.12.1 cutoff it would flag v0.12.2, so it catches the defect this ticket fixes.
- r5: the test_docs regex now keeps the ref's trailing full stop out of the match and compares each line's fragment with subdirectory_fragment(ref), so it fails both ways.
- Consistency: ADRs 0026, 0043 and 0044, the overview, the decisions index, the README and the three docs pages all say v0.12.2. ADR 0044's old caveat (that main's install lines name a tag that cannot build) is replaced by a true note. No v0.12.1 cutoff wording is left in tracked code or docs; a grep turns up only `generated.by` stamps and test cases below the cutoff.

## Findings

None.

## Notes

A small wording point in docs/how-to/install-kmctl-with-apm.md: "add `#subdirectory=packages/kmctl` to the line above to install one" leaves it implied that you also change the tag. It is clear enough as written.
