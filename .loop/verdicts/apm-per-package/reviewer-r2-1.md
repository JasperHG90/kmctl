---
type: verdict
title: 'Verdict: apm-per-package reviewer round 2'
description: 'reviewer verdict for round 2 of apm-per-package: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-15T07:28:20+00:00'
slug: apm-per-package
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

The round 1 finding is fixed. The docstring of `_names_old_package` no longer names `write_manifest`, and its new clause matches the code. Only the docstring changed, the function body is the same, and the gates are green on this tree.

## Checked

- `loopctl gate stamp` in the worktree: lint, format, tests, integration and eval rows r1 to r7 all pass. Stamp: green, c0886e39689c0c486f8a1007cd3cac088664bb7d43a1576e438488324ca25006, which matches this round's fingerprint.
- Read `_names_old_package` (plugin.py:379-397), its only caller `_old_entry` (plugin.py:718-727) and `_old_entry`'s only caller `patch` (around plugin.py:787). A `{git, path}` entry with no old layout in the lock makes the function return False. `_old_entry` skips that entry, and `patch` never writes apm.yml. So "otherwise the entry already names kmctl's package and is left as it is" is true.
- `grep -rn write_manifest` across packages/, scripts/, docs/ and .okf/ finds nothing.

## Findings

- f1 (resolved): plugin.py:382-386 now ends "otherwise the entry already names kmctl's package and is left as it is", which matches the False return and the caller chain above.
