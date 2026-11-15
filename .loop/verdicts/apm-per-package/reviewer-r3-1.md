---
type: verdict
title: 'Verdict: apm-per-package reviewer round 3'
description: 'reviewer verdict for round 3 of apm-per-package: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-15T07:48:20+00:00'
slug: apm-per-package
pass: reviewer
round: 3
body_schema: verdict/1
---

## Summary

The content of this tree is the same as round 2's. The builder only staged it. The index tree is d63dc634, the same tree object that refs/loop/apm-per-package/r2 and r3 point to. The working tree has no unstaged changes and no untracked files. The f1 fix is still there, and the gates are green on this tree.

## Checked

- `git write-tree` on the worktree's index gives d63dc634e4c6177e4727c73e98b08e7f32b9ba12. That equals refs/loop/apm-per-package/r2 and r3. `git diff --cached d63dc634` and `git diff d63dc634` (excluding .loop) are both empty. `git ls-files --others --exclude-standard` lists nothing. Since the content is byte-for-byte what round 2 reviewed, the fingerprint change comes from staging alone.
- f1: plugin.py:379-397 still ends its docstring with "otherwise the entry already names kmctl's package and is left as it is". `grep -rn write_manifest` across packages, scripts, docs and .okf finds nothing.
- `loopctl gate stamp`, first run: red. The only failures were three integration tests (test_opencode consumer install, test_pin real uvx, test_plugin_patch real apm install), each from a network timeout reaching github.com or pypi.org. I checked both hosts with curl (both 200 after that) and ran the stamp again.
- `loopctl gate stamp`, second run: lint, format, tests, integration and eval rows r1 to r7 all pass. "stamp green: 4b8d22081d875919721cb2c9ad9083f9b460733f552a3056c9118cfb6b9f18cf", which matches this round's fingerprint.

## Findings

- f1 (resolved): fixed in round 2 at plugin.py:382-386, and the fix is unchanged in this tree.

## Notes

The first stamp's red result was the network, not the code. The same three tests passed on the second run with no change to the tree.
