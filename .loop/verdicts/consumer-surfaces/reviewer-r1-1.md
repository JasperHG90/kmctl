---
type: verdict
title: 'Verdict: consumer-surfaces reviewer round 1'
description: 'reviewer verdict for round 1 of consumer-surfaces: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-19T15:12:51+00:00'
slug: consumer-surfaces
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks for all four issues. Both hook hints name `@v<version>` and match `hook_entry()`. `release.py set` rewrites them, and release.yml stages hooks.json. The maintainer comment is gone from the Antigravity copies. The diagrams rule no longer asks to be edited. The block names the rules folder of each harness `harnesses_found` reports, or all three when it finds none. The briefing line is shorter than the old one and names no folder. I ran `loopctl gate stamp` from the worktree and it came back green (lint, format, tests, integration, rows r1 to r5; stamp 0189c634...). Three findings remain, none blocking: a decode crash that init can now reach, one stale overview line, and a pre-existing `.claude/rules/` reference in the Antigravity rule bodies.

## Checked

- Read the full diff and the touched code: `scaffold.block` and `_with_block`, and `harnesses_found`, `_manifest_targets`, `_kmctl_mark`, `read_lock` and `read_manifest` in doctor.py and plugin.py. `harnesses_found` only returns names from `HARNESSES`, so the `RULES_FOLDERS` lookup cannot raise a KeyError. doctor.py does not import scaffold, so the new import cannot loop.
- Doctor's `claude.hook` compares the hook against `hook_entry()`. That now depends on the CLI version, which matches what the package of the same release ships, as the plan says.
- release.py: `_HOOK_INSTALL` matches the two hints with or without a tag and handles rc tags. `set` refuses when the count is not two. release.yml's `git diff --exit-code` guard would catch any file that is not staged.
- r1: tests/test_plugin.py::test_install_hint_names_release reads the version from apm/apm.yml. It asserts that hooks.json equals `hook_entry()`, that the install string appears twice, and that the hook run without kmctl on PATH exits 0 and prints the hint. It covers fails_when.
- r2: the test runs `set` twice (0.2.0, then 0.3.0rc1) and asserts both refs each time. It covers fails_when.
- r3: the test globs all eight installed rules, asserts the count, and checks all three needles. It covers fails_when.
- r4: the parametrized update test asserts each folder appears exactly when its harness is installed, including a two-harness case. The init test asserts all three folders with their tools. It covers fails_when.
- r5: the new test asserts the old phrase is gone, no folder is in the line, and the line is no longer than the old one. The budget tests in the same file still pass.
- r6 (judgment): checked by reading. ADR 0011 and ADR 0020 each have a dated 2026-10-19 correction that is accurate. The diagrams rule (Claude source and Antigravity copy) says to add your own rule under another name and explains why. Doctor does compare the deployed file hashes, so the drift claim holds. The block and briefing descriptions in docs/reference/commands.md match the code. README, the explanation page, the briefing docstring and the overview's init row and diagram were updated to match. The OpenCode notice tells the user nothing to edit, so leaving it alone is right. I judge r6 met, apart from the one overview line in f2.
- Probe: `kmctl init` on a scratch repo whose apm.yml is not UTF-8 stops with a traceback partway through (f1).

## Findings

- f1: `harnesses_found` makes apm.yml and apm.lock.yaml parsing reachable from `kmctl init`. Before this change init never read them. `read_manifest` and `read_lock` call `read_text` without catching `UnicodeDecodeError`, so init stops halfway with a traceback. Doctor had the same crash already. The plain fix is to treat a decode error like a YAML error in those two readers. The case is rare and the fix is simple, so it does not block.
- f2: the overview's briefing row still says the rules are in `.claude/rules/`. Change it to the harness's rules folder, as the docstring and commands.md now say.
- f3: the Antigravity rule copies still name `.claude/rules/NAME.md` in their bodies, which is wrong in an Antigravity-only repository. This was there before the change and is outside the plan's scope. Relay it as its own ticket or fix it in the sync script.

## Notes

The changes are uncommitted in the worktree; the stamp binds the tree as it is.
