---
type: plan
title: 'Plan: handoff-and-continue-skills'
description: "The plugin gains /handoff, which writes a handoff concept to .okf/handoffs/ through kmctl, and /continue, which offers the live handoffs as a multi-select and summarizes the chosen ones (ADR 0008)."
slug: handoff-and-continue-skills
epic: plugin
depends_on: [claude-plugin, new-concept-verbs, handoffs-list]
priority: 9
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T06:33:01+00:00'
---

# handoff-and-continue-skills

Relayed from: none

## Intent

Two skills in the plugin, modelled on memex's skills of the same names (ADR 0008):

- `/handoff [focus]`: the agent writes a technical summary of the current work in four sections (Summary, Where it stands, Next steps, Key references) and saves it with `kmctl new handoff TITLE --description TEXT --key "$CLAUDE_CODE_SESSION_ID"`. spike:handoff-and-continue-skills/1 showed the Bash tool's environment carries that id, the same one hooks get; it changes on `/clear`, so a `/handoff` after `/clear` starts a new handoff.
- `/continue [topic]`: reads `kmctl handoffs --json` (ticket `handoffs-list`), offers them with AskUserQuestion as a multi-select of 3 plus `more`, loads the chosen ones, summarizes them together, and asks what to do next. It takes no action before the user answers. With no live handoffs it says so and suggests `/handoff`.

This ticket adds `--key` to `kmctl new handoff`. The key is stored in one extension field, `handoff_key`, which ADR 0009 names as the only exception to invariant I4. When a handoff with the same key exists, kmctl replaces its body and description, keeps its file name and index entry, and appends one log line; an unknown key creates a new handoff.

Both skills are made with the skill-creator skill (ADR 0007), and their test prompts are kept beside them.

Done when tests show: `--key` with an existing key replaces body and description, keeps the file name and index entry, and writes one log line; an unknown key creates a new handoff; the bundle passes the pinned okf validator in strict mode afterwards; and both skills pass their skill-creator test prompts.

## Could invalidate this plan

- none
