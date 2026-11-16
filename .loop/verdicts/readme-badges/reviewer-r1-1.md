---
type: verdict
title: 'Verdict: readme-badges reviewer round 1'
description: 'reviewer verdict for round 1 of readme-badges: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-16T09:27:32+00:00'
slug: readme-badges
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan says. All three READMEs open with CI (ci.yml on main), licence and Python badges. Each package README and each root Packages entry has its lifecycle badge (kmctl stable, kmaudit beta) and a release badge filtered to its own tags (`filter=v*` for kmctl, `filter=kmaudit-v*` for kmaudit). kmaudit is called beta in its README, in its command reference, in the root entry and through the `Development Status :: 4 - Beta` classifier. kmctl gets `5 - Production/Stable`. The new tests check every fails_when clause in both eval rows.

## Checked

- Read the staged diff (README.md, both package READMEs, docs/reference/kmaudit-commands.md, both pyprojects, tests/test_readmes.py) against the plan's intent and the outcomes O1 and O2.
- `loopctl gate stamp` from the worktree: lint, format, tests, integration, eval-row r1 and eval-row r2 all pass; stamp green ef665f8d8537310a37a44691af95f972a45b6fe513ad09924c1767143efe4002.
- Rows r1 and r2: I made mutated copies of the READMEs, docs and pyprojects in a scratch folder and ran tests/test_readmes.py against each copy. Every mutation turned exactly its own test red: CI badge on another branch, CI badge on another workflow, a missing licence badge, kmctl's release filter widened to `*`, the root kmaudit entry filtering to `v*`, kmaudit's lifecycle badge flipped to stable, the root entry's beta sentence removed, the beta line dropped from the command reference, and the kmaudit classifier changed to Alpha. `-k badge` selects the three badge tests, so r1 runs what it claims to.
- The release filters are compared as exact query parts, so `filter=v*` cannot match `filter=kmaudit-v*`. The operator's live fetch showed each badge resolving to its own package's tag.
- `kmctl check` passes (docs front matter, indexes, links). The relative links in the new badges (LICENSE, pyproject.toml) resolve in each package folder, and the existing link test checks them.
- Readability: the root entry reads "kmaudit [badges] is in beta. It checks what...". The beta sentence in kmaudit's README and in its command reference is short and says what may change and where changes are announced. The root README stays under its 80-line limit, which the existing test enforces.

## Findings

None.

## Notes

The relative badge links (LICENSE, pyproject.toml) will not resolve when PyPI renders the package READMEs. The package READMEs already link relatively throughout, so this is not new.
