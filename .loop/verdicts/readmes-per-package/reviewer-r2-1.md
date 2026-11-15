---
type: verdict
title: 'Verdict: readmes-per-package reviewer round 2'
description: 'reviewer verdict for round 2 of readmes-per-package: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-15T19:22:52+00:00'
slug: readmes-per-package
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

This was a narrow round 2 review. f1 is resolved: both strings now point at the install section of kmctl's README, and packages/kmctl/README.md has a `## Install` section at line 19. The fix changed only wording and broke nothing. The gates are green.

## Checked

- packages/kmctl/src/kmctl/__init__.py:1063, the end of the plugin patch help text: "Installing is in the install section of kmctl's README."
- packages/kmctl/src/kmctl/plugin.py:800-801, the PluginError raised when apm.lock.yaml lists no kmctl package: "(the install section of kmctl's README)". The f-string concatenation still reads correctly.
- Searched the package sources for the old wording. The other hits in kmctl's source (__init__.py:164, init's Next line) already say "the kmctl README's install section", which is correct. No test asserts the changed strings.
- Ran `loopctl gate stamp` in the worktree myself: lint, format, tests and integration pass, eval rows r1 to r5 pass, "stamp green: 0025eda9368e438c1a503ac44d92547d4fc10005ad0bad314a5781f3726e57e5".

## Findings

- f1: resolved at packages/kmctl/src/kmctl/__init__.py:1063 and packages/kmctl/src/kmctl/plugin.py:800-801. Both now name kmctl's README, which has the install section.

## Notes

.okf/decisions/0021-apm-installs-kmctl-s-package-kmctl-plugin-patch-adds-the-rest.md:54 still says "The README's install section". This change did not touch that line, and a narrow round does not cover it. An operator may want to change it to name kmctl's README in a follow-up.
