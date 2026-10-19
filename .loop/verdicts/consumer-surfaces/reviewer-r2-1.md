---
type: verdict
title: 'Verdict: consumer-surfaces reviewer round 2'
description: 'reviewer verdict for round 2 of consumer-surfaces: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-19T15:43:08+00:00'
slug: consumer-surfaces
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

All three round 1 findings are fixed. `read_manifest` now raises `PluginError` on a decode error, and `_manifest_targets` already catches that. `read_lock` returns None. The overview row names each harness's rules folder. The package rules now name each other by name, and the Antigravity copies match their sources. I ran `loopctl gate stamp` from the worktree and it came back green: lint, format, tests, integration and rows r1 to r5 all pass, stamp 8b574b696399fc1d61a186b22f12ab880d07c2d10f63cf7faa7c7bf0dab19e05, which matches the round's binding. One small non-blocking finding is left: a skill still uses the old `.claude/rules/` path as an example.

## Checked

- The f1 fix in plugin.py, and its callers: `_manifest_targets` in doctor.py catches `PluginError`, and `harnesses_found` gets None from `read_lock`. The new tests in tests/test_plugin.py and tests/test_init.py write `\xff\xfe` bytes and assert the refusal, the no-lock result, and that init exits 0 with all three folders in the block. Without the fix, those tests would fail.
- Probes on scratch repos, each running `kmctl init`: a non-UTF-8 `.claude/settings.json`, a settings.json with bad JSON, a list as settings.json and as apm.yml, and a folder named apm.lock.yaml next to `targets: 5`. Each exited 0 and wrote the all-three-folders line.
- f2: the overview's briefing row now names `.claude/rules/`, `.agents/rules/` and `.opencode/rules/` as each harness's folders. The new diagram edge from scaffold to doctor matches the new import.
- f3: grep finds no `.claude/` under `apm/*/.apm/instructions/`. The test_apm_package.py hashes changed with a comment that names ADR 0011's correction. The stale-copy test passes, and the ADR 0011 correction and log.md line describe the change accurately.
- The rest of the change, read again: the block and `RULES_FOLDERS` in scaffold.py, the briefing line, the `_HOOK_INSTALL` regex in release.py and its count guard, release.yml staging hooks.json, the sync script's docstring, and hooks.json matching `hook_entry()` at v0.10.0. Rows r1 to r5 still assert their fails_when, as I found in round 1. r6 (judgment): the ADR 0011 and 0020 corrections, the diagrams rule and commands.md still match the code.

## Findings

- f1: resolved in src/kmctl/plugin.py `read_manifest` and `read_lock`, with tests.
- f2: resolved in .okf/architecture/overview.md, the briefing row.
- f3: resolved in the okf-bundle and docs-layout rule sources and their Antigravity copies.
- f4: apm/.apm/skills/decision-log-review/SKILL.md:24 says "for example `.claude/rules/okf-bundle.md`". The package installs this skill for every harness, so in an Antigravity-only repository it names a path that does not exist, the same fault f3 fixed in the rules. This was there before the change, and the fix is one phrase, such as "the `okf-bundle` rule". Not blocking.

## Notes

The changes are still uncommitted in the worktree. The stamp binds the tree as it is now.
