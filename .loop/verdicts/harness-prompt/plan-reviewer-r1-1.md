---
type: verdict
title: 'Verdict: harness-prompt plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of harness-prompt: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T05:56:47+00:00'
slug: harness-prompt
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

No open risk could break this plan. The one listed risk, that refusing without a terminal breaks a caller in this repository, is settled by spike harness-prompt/1, and a second check for callers the spike's grep could miss found none. The code the plan names exists and behaves as the plan assumes.

## Checked

- Spike harness-prompt/1: README outcome, stdout and the command. It greps for the text "kmctl plugin install|update" without --harness, and fails if a hit is in action.yml, action/, .github/ or the justfile. Exit 0. It answers the risk for scripts and docs.
- The spike's grep would miss tests that call the CLI as `_kmctl("plugin", "install", ...)`. I grepped tests/ for those calls. Only tests/test_plugin.py:365 (`_kmctl("plugin", "update")`) leaves out --harness, and the plan already names it as changing. Every other call passes --harness.
- action.yml, action/, .github/ and justfile never run kmctl plugin. The release workflow only edits the install docs.
- Messages agents read: doctor's fixes (src/kmctl/doctor.py:134, 139) already include `--harness`. briefing.py and apm/ hold no bare install or update command. A bare call from an agent gets the refusal, which names --harness, so an agent can recover on its own.
- src/kmctl/__init__.py: plugin_install and plugin_update both default `harness` to "claude" and send it to `_install`, which calls `parse_harnesses` twice. Changing the default to None, then prompting or refusing there, fits this structure. kmctl.doctor is already imported, so calling `harnesses_found(cwd, scope)` adds no import cycle. `harnesses_found` returns names in `HARNESSES` order and leaves out antigravity at user scope, which matches the planned update default.
- `parse_harnesses` raises PluginError and does no I/O, so the prompt can stay in the command layer as the plan requires.

## Findings

None.

## Notes

The eval has no rows yet. The plan's "It worked when" sentence covers the three behaviours that should become rows: the prompt in a simulated terminal, update defaulting to the installed harnesses, and the refusal without a terminal or with --json. CliRunner's stdin is not a TTY, so the terminal test has to fake isatty. That is a build detail, not a plan risk.
