---
type: verdict
title: 'Verdict: opencode-harness-reviewer-f6 reviewer round 1'
description: 'reviewer verdict for round 1 of opencode-harness-reviewer-f6: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-18T05:42:06+00:00'
slug: opencode-harness-reviewer-f6
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks for. At `--scope user`, `unpatch` returns before any delete and builds one note from the Antigravity folder and `opencode.undo_paths`. Project scope runs the same path as before, and `undo` now deletes what `undo_paths` names. The gates are green. Two small non-blocking findings remain: a stale line in the architecture overview and a weak docs test.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests, integration and eval rows r1 to r4 all pass. It printed `stamp green: 42215e19883ecd61d3f0ea7526292123654cfa6d75a376534b338738ed90f2dd`.
- I ran the plan's measurement script on the worktree. It printed `exit 0 deleted 0 changed 0`.
- I read the `undo` refactor in `src/kmctl/opencode.py` line by line. `undo_paths` adds opencode.json only when `instructions` is a list that holds `INSTRUCTIONS`, so the `_instructions` call in `undo` cannot raise. An unreadable opencode.json is still skipped while the agents, rules and plugin still go, as before. Folder cleanup is unchanged.
- In `src/kmctl/plugin.py`, the user-scope branch deletes nothing and adds a note only when something is found. The CLI still prints `nothing to undo` when there are no notes, and `Next: kmctl doctor --scope user` after that.
- r1: both `undo_user_scope` tests compare the full file tree before and after. They check exit 0 through `_patch`, every OpenCode path or the plugin folder in the note, and the `kmctl plugin patch --undo` and `without --scope user` text.
- r2: the existing project-scope undo tests (`test_undo_leaves_no_kmctl_file`, `test_undo_deletes_only_the_plugin_folder` and others) still run under `-k undo`. The new `test_undo_user_scope_with_nothing_here_says_nothing_to_undo` checks for no `note:` and exit 0. `test_undo_paths_name_what_undo_removes` checks that the two functions agree.
- r3: I read the new help, epilog and reference text myself (judgment). They say that user scope leaves the repository's files and names them. The test is weak (f2).
- Consistency: README, the two how-to pages and ADR 0024 describe project-scope removal and stay true. The overview row does not (f1).

## Findings

- f1: `.okf/architecture/overview.md` line 180 ends with "`--undo` deletes the plugin folder and the OpenCode files". Add "at project scope", or say that user scope names them and leaves them.
- f2: `test_undo_docs_say_user_scope_leaves_project_files` should check a phrase that only the new sentence holds, for example "deletes nothing in this repository" in the reference and "names them" in the help.

## Notes

The new sentence in `docs/reference/commands.md` line 488 is joined to the previous line without a rewrap. That is cosmetic.
