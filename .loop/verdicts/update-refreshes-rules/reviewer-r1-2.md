---
type: verdict
title: 'Verdict: update-refreshes-rules reviewer round 1'
description: 'reviewer verdict for round 1 of update-refreshes-rules: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-16T11:06:41+00:00'
slug: update-refreshes-rules
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. `kmctl update` is the init command registered a second time, with the same options and JSON output. init replaces each of the four shipped rules when its bytes differ from the packaged copy, skips one that matches without rewriting it, and never looks at other files in `.claude/rules/`. Unsafe rule symlinks are left alone with a warning, the same way CLAUDE.md and AGENTS.md are. The gates and all four row tests pass. I found two small issues, f1 and f2, both non-blocking. f1 is stale text in the architecture overview, and a text fix cannot ship a defect. f2 is a crash that only happens when a folder sits at a rule path, which is rare. Its fix is a few lines and a test, the same skip-with-warning `_write_block` already uses, so I trust a plain fix without a second review.

## Checked

- Ran `loopctl gate stamp` in the worktree. Output: "pass gate lint, format, tests, integration; pass eval-row r1, r2, r3, r4; stamp green: 81979f12a34cc67e69f63b489c2f91d46bad6dbe8d9ed7a380a6619f5a66de8c".
- Read the full diff of src/kmctl/__init__.py, src/kmctl/scaffold.py, tests/test_cli.py, tests/test_init.py, ADR 0011, .okf/log.md, README.md, docs/reference/commands.md and the tutorial.
- Row r1: `test_init_overwrites_edited_rule` edits okf-bundle.md after init, then asserts the file equals `src/kmctl/repo_rules/okf-bundle.md` and that `updated` lists it and `skipped` does not. It would fail if init kept the edit.
- Row r2: `test_init_skips_current_rule` asserts the rule is in `skipped`, is not in `updated` or `created`, and that `st_mtime_ns` did not change. It would fail on a rewrite.
- Row r3: `test_init_leaves_other_rules` runs init twice with a user rule present and asserts the rule is never listed and that its content and mtime did not change.
- Row r4: `test_update_is_init_alias` compares the JSON and file trees of init and update on fresh repos, passes `--path` to update, and checks that `kmctl --help` lists update. I also ran `kmctl update --help` and `kmctl --help` by hand.
- Row r5 (judgment): `kmctl init --help` (epilog and summary), docs/reference/commands.md (table row, the exceptions paragraph, the output line and a new `kmctl update` section), README.md and the tutorial's "What you learned" all say the four rules are replaced and name `kmctl update`. None of them still says rule files are kept. ADR 0011 gets an appended `## Correction, 2026-10-16`, which is what `.claude/rules/okf-bundle.md` asks for when a record changes, plus a log line. The plan allowed either a correction or a supersede. I judge r5 met. The out-of-scope stale text is f1.
- Edge cases I tried by hand: a rule symlink pointing outside the repo (covered by a new test) and a folder at a rule path (f2, reproduced as a traceback).

## Findings

- f1 (docs, not blocking): `.okf/architecture/overview.md:129` says init "keeps every file that exists except for that block and the decision's index entry and log line (ADR 0011)". That is now false for the four rules. The Depicts list at line 221 names every verb but leaves out `kmctl update`. Fix: name the rule replacement and the alias in both places.
- f2 (bug, not blocking): `_write_rules` calls `path.read_bytes()` whenever `path.exists()`. If a folder sits at `.claude/rules/okf-bundle.md`, init dies with an IsADirectoryError traceback. Before this change that path was kept. Fix: when the path exists but is not a file, add it to `skipped` with a warning, as `_write_block` does for an AGENTS.md that is not a file, and add a test. The fix is simple, so I don't need to review it again.
