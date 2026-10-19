---
type: verdict
title: 'Verdict: doctor-correct-setups reviewer round 1'
description: 'reviewer verdict for round 1 of doctor-correct-setups: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-19T15:17:11+00:00'
slug: doctor-correct-setups
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan says. Doctor now has a third outcome, `warn`, that fails nothing. A missing `claude`, `agy` or `opencode` warns. A folder missing from the agy CLI's trust list warns, and the warning says doctor does not check trust given in the Antigravity IDE. At project scope, `claude.old-plugin` also reads the user `settings.json` and gives a fix for each file. The docs, the epilog, the `--help` text and the docstrings match the code. The gates are green.

## Checked

- Gates: I ran `loopctl gate stamp` from the worktree myself. lint, format, tests and integration all passed, and so did eval rows r1 to r5. Result: `stamp green: 8597aa4f7d4291a1fa65a12fc54304ecaaf9044a396884910d30ac845ea04854`.
- Code: I read the whole diff and the parts of `src/kmctl/doctor.py` around it. `Check.ok` is now a property, `status != "fail"`. I found no other code that builds a `Check` from its fields in order, and only `doctor_cmd` reads `result.ok`. In `render`, a warning prints as `warn ID: DETAIL; FIX`. Neither warning detail contains `;`. `_tool` still fails `dep.uv` and `dep.git`, which serve all harnesses. `_old_plugin_fix` sends `kmctl@kmctl` in the user file at project scope to the three claude commands. Those are the same steps `remove_old_plugin` in `src/kmctl/plugin.py` runs at user scope. okf's fix uses the scope of the file that enables it. When the repository is HOME, the project file and the user file are the same file; `dict.fromkeys` removes the duplicate and the scope comes out as `user`, which is right. `_kmctl_mark` and `harnesses_found` still call `_settings_files`, so a plugin in the user file does not mark the claude harness in the project.
- r1: `test_missing_harness_cli_warns` takes `claude` and `agy` off PATH. It asserts exit 0, both `warn` lines with their fixes, and that no `fail ` line appears.
- r2: `test_antigravity_trust_warns_and_names_the_ide` asserts exit 0, a `warn antigravity.trust` line, the text `Antigravity IDE`, and the trust fix.
- r3: `test_old_plugin_found_in_user_settings_at_project_scope` asserts exit 1, the user file's full path in the line, and that the line ends with `claude plugin uninstall okf@scaccogatto --scope user`. Two more tests cover `kmctl@kmctl` in the user file, and a plugin in both the project and the user file.
- r4: `test_json_status_field` asserts that every check has a status, that a warning has `status` `warn` with `ok` true, that a passed check's fix is null, and that a failure has `status` `fail` with `ok` false. `test_json_shape_and_ids` now expects the `status` key.
- r5: `test_user_scope_plugin_does_not_mark_project_harness` asserts that `harnesses_found` returns `[]` and that `_kmctl_mark` is false at project scope. If `_settings_files` also read the user file, this test would fail.
- r6 (judgment): `docs/reference/commands.md` covers the output shapes, the `status` field in `--json`, the exit codes, and the `dep.*`, `antigravity.trust` and `claude.old-plugin` rows. The doctor epilog and the `--json` help text match. The how-to example's `warn dep.agy` line matches the text the code builds, which the r1 test asserts. A grep found no doc or help text that still says a missing harness CLI fails. On home folders: the `setup` fixture in `tests/test_doctor.py`, the one in `tests/test_opencode.py`, and `tests/conftest.py` all point HOME and CLAUDE_CONFIG_DIR at scratch folders. The integration tests that read `os.environ["HOME"]` run after those fixtures. So no doctor test reads the real `~/.claude` or `~/.gemini`. This matters here because this machine's real user settings enable `okf@scaccogatto`, and with the new check the starter integration test's `assert report["ok"]` would fail if it read them. It passed.

## Findings

None.

## Notes

`README.md` still says "each `fail` line names its fix". That is still true, and warn lines carry a fix too, so I am not raising it.
