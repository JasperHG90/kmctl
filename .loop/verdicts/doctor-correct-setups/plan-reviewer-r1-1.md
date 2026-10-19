---
type: verdict
title: 'Verdict: doctor-correct-setups plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of doctor-correct-setups: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-19T14:32:51+00:00'
slug: doctor-correct-setups
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

Pass. The plan lists no risks, and none of the claims it rests on fails against the repo.

## Checked

- `src/kmctl/doctor.py`: `_tool` fails `dep.claude`, `dep.agy` and `dep.opencode` when the tool is not on PATH. `_antigravity_trust` reads only `~/.gemini/antigravity-cli/settings.json` and returns None when agy is missing. `_settings_files` at project scope reads only the project's `settings.json` and `settings.local.json`. `_claude_old_plugin` already picks a fix per file. All of this is as the plan says.
- `settings_path(cwd, "user")` goes through `claude_config_dir()`, so it honours `$CLAUDE_CONFIG_DIR`. `remove_old_plugin` in `plugin.py` is the user-scope uninstall/prune/marketplace-remove sequence the plan quotes.
- `_kmctl_mark` calls `_old_plugins`. So the user file has to be added in `_claude_old_plugin` (or behind a separate helper), not by widening `_settings_files`, or a user-scope `kmctl@kmctl` would mark claude as a project harness. The plan already says `_kmctl_mark` and `harnesses_found` do not change, so this is a build detail, not a risk.
- Only `doctor_cmd` in `src/kmctl/__init__.py` consumes `DoctorResult.ok` and `Check.ok`. Nothing in `action/` or `.github/` reads doctor's output. Keeping `ok` true for a warning keeps the `failed <= UNPASSABLE` reading in `tests/test_starter.py` working.
- The test fixtures in `tests/conftest.py`, `tests/test_antigravity.py` and `tests/test_opencode.py` already point HOME and `CLAUDE_CONFIG_DIR` at scratch. Reading the user settings file at project scope will not pick up this machine's `~/.claude/settings.json`, which does enable `okf@scaccogatto`, in existing doctor tests.
- spike:starter-reviewer-gitignore/3's unpassable set is exactly the four checks this plan turns into warnings, so a correct starter's `just check` should exit 0 after the change.

## Findings

None.

## Notes

The plan settles the Antigravity trust question by picking one of the issue's options and flagging it for the operator. That is a choice, not a risk to the plan.
