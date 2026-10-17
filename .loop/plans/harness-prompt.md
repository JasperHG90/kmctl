---
type: plan
title: 'Plan: harness-prompt'
description: kmctl plugin install and update ask which harnesses to install for when --harness is missing and a person is at the terminal.
tags:
- plan
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T05:54:45+00:00'
slug: harness-prompt
epic: null
depends_on: []
priority: null
---

# harness-prompt

<!-- This template was registered in planning. To capture an idea as a stub
instead (intent for later, promoted by the operator), write the plan with
`status: draft` in its front matter before running loopctl ticket register.
A hand-written plan's front matter needs type: plan, title, description and
slug; loopctl ticket register fills in generated. Optional: epic, depends_on,
priority, status, strictness and blocking. -->

Relayed from: none

## Intent

`kmctl plugin install` and `kmctl plugin update` ask which harnesses to install
for when `--harness` is not given and a person is at the terminal. The
interface has three audiences (`.claude/rules/interface-audience.md`): a
person at the terminal gets the question; a script, CI job or agent never
gets a prompt; and the logic in `src/kmctl/plugin.py` stays free of I/O.

- The question lists each harness in `HARNESSES` with a number and a short
  label, and takes numbers or names as a comma list. It goes to stderr, so
  stdout carries only the result. An empty answer takes the default. An
  answer it can't read gets asked again, naming the accepted values.
- The default for install is claude. For update it is the harnesses
  `harnesses_found` in `src/kmctl/doctor.py` finds installed at that scope,
  or claude when it finds none.
- Without `--harness`, when stdin is not a terminal or `--json` is given,
  the command refuses (exit 1) and names `--harness` with the accepted
  values instead of guessing. Before this change, a missing `--harness`
  meant claude.
- `--harness` works as before and never prompts. The help text, the epilog,
  `docs/reference/commands.md` and the install how-tos say all this.

It worked when, in `tests/test_plugin.py`, a simulated terminal session
without `--harness` gets the question and installs what the answer names;
update's default is the installed harnesses; and a run that isn't at a
terminal, or passes `--json`, refuses without prompting.

## Could invalidate this plan

- The refusal without a terminal breaks a caller in this repository that
  leaves out `--harness` (the GitHub Action, the justfile, an integration
  test or a doc command). It does not (spike:harness-prompt/1): no script
  runs kmctl plugin, and the one test that runs `kmctl plugin update` bare
  relies on the old claude default, which this ticket replaces.
