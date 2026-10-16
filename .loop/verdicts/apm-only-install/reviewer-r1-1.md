---
type: verdict
title: 'Verdict: apm-only-install reviewer round 1'
description: 'reviewer verdict for round 1 of apm-only-install: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-16T21:14:52+00:00'
slug: apm-only-install
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan says. plugin/ and the marketplace file are gone. The package under apm/.apm holds the 7 skills and the agent unchanged and the 4 rules as instructions with the old globs and bodies. apm/apm.yml is the one version source. `kmctl plugin install --harness claude` writes the apm.yml entry, runs the pinned APM, migrates both kinds of old install in the planned order, writes one SessionStart hook and declares okf's MCP server. Init no longer writes rules. The gates and all 13 eval rows pass on my own stamp. Two non-blocking findings: one wrong ordering in the architecture overview, and one hardening gap when --source changes between installs.

## Checked

- Re-ran `loopctl gate stamp` from the worktree, with HOME, CLAUDE_CONFIG_DIR and XDG_DATA_HOME pointed at scratch folders: "stamp green: 12172dbd88f1f4381a6b7bd0197416b7da9bcd5a9c831a51c851382c5d6e62a9". lint, format, tests (528 passed) and integration (2 passed) all passed, as did rows r1 to r12 including r6b. The scratch config folders were empty afterwards. Because HOME was redirected, git had no identity, so loopctl reported "state commit deferred" for the stamp's state commit.
- Read src/kmctl/plugin.py in full and the diffs of __init__.py, scaffold.py, briefing.py, release.py, check_wheel.py, smoke_wheel.py, pyproject.toml, the workflows, action.yml and knowledge-audit.sh.
- HOOK_COMMAND, HOOK_DESCRIPTION and timeout are byte-equal to main's plugin/hooks/hooks.json, so I1's behaviour is kept. The tests run the written command with kmctl missing and with kmctl failing, and both exit 0.
- Rows against fails_when:
  - r1 hashes the old rule bodies and compares applyTo with the old globs.
  - r2 runs set 9.8.7, builds the wheel and checks its name and every skill file.
  - r3 covers keys and hooks kept, one entry after two installs, in-place replacement of an old entry with a duplicate removed, and a missing file created.
  - r4 checks the exact APM argv, cwd and apm.yml contents at call time, and that unknown harnesses run nothing.
  - r5 checks that a skip names .claude/skills/audit and not the others, and names --force.
  - r6 checks the claude uninstall, prune and marketplace remove order, that they run after apm install, and the scope. It also checks that apm uninstall runs before the rewrite (the fake logs apm.yml at call time) and that a missing claude skips with a note.
  - r6b covers the sha against the apm.yml pin, a changed pin replacing the entry, the launcher run from a subfolder, and an existing okf server under another name.
  - r7 checks -g, CLAUDE_CONFIG_DIR and the default ~/.claude.
  - r8 checks the status problems and their fixes, and that init writes nothing under .claude/.
  - r9 runs the real apm-cli 0.33.0 against a served tree and checks bytes, paths:, okf skills, one hook, no dev items, a clean status, and an untouched real config folder.
  - None of these tests asserts a constant or mocks away the logic under test.
- Docs and knowledge: ADR 0014 follows the decision skeleton. ADRs 0003 and 0013 are deprecated with Corrections, and 0001, 0011 and 0012 carry Corrections. The manifesto, overview, commands reference, both how-tos, README, tutorial and explanations describe the new route. The remaining `plugin/` mentions are in files the plan moves unchanged (the agent's example JSON, eval results) or in historical ADR text.

## Findings

- f1 (docs, non-blocking): .okf/architecture/overview.md:146 orders the old-plugin removal before the APM install. The code, ADR 0014 and docs/reference/commands.md all put it after, so a failed install keeps the old plugin. Reword the cell to match the real order.
- f2 (hardening, non-blocking): src/kmctl/plugin.py:537. An entry written with one --source is not replaced when the next install uses a different source that does not name JasperHG90/Knowledge-management. apm.yml then holds two kmctl packages. This is rare, since it needs a fork or local-server install first, but nothing warns.

## Notes

- At user scope, skipped_skills resolves lock deployed_files against HOME and compares them with CLAUDE_CONFIG_DIR/skills. No test covers a user-scope skip, so I could not confirm the paths it names there. The fix line is still correct either way.
- merge_hook runs after apm install. A settings.json whose "hooks" is JSON null passes preflight and then fails after APM has installed. That is an edge case, and a re-run after fixing the file recovers.
