---
type: plan
title: 'Plan: handoff-and-continue-skills'
description: "The plugin gains /handoff, which writes a handoff concept to .okf/handoffs/ through kmctl, and /continue, which offers the live handoffs as a multi-select and summarizes the chosen ones (ADR 0008)."
slug: handoff-and-continue-skills
epic: plugin
depends_on: [claude-plugin, new-concept-verbs]
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

- `/handoff [focus]`: the agent writes a technical summary of the current work in four sections (Summary, Where it stands, Next steps, Key references) and saves it with `kmctl new handoff`, which fills the front matter, the `stale_after` date and the index entry. This ticket adds `--key`: when a handoff with the same key exists, kmctl replaces its body and description and logs the update instead of refusing. Running it twice in one session updates the same handoff instead of adding a second.
- `/continue [topic]`: reads `kmctl handoffs --json` (live handoffs, newest first, a verb this ticket adds), offers them with AskUserQuestion as a multi-select of 3 plus `more`, loads the chosen ones, summarizes them together, and asks what to do next. It takes no action before the user answers. With no live handoffs it says so and suggests `/handoff`.

Both skills are made with the skill-creator skill (ADR 0007), and their test prompts are kept beside them.

Done when `kmctl handoffs` has tests for ordering and for leaving out expired handoffs, and both skills pass their skill-creator test prompts.

## Could invalidate this plan

- Updating the same handoff on a second `/handoff` needs a stable key for the session. Claude Code exposes a session id to hooks, but the plan assumes a skill can read it too; if it cannot, the skill has to match on title instead. Settled by spike:handoff-and-continue-skills/1: the Bash tool's environment carries `CLAUDE_CODE_SESSION_ID` (the same id hooks get), and SKILL.md can use `${CLAUDE_SESSION_ID}`. The handoff stores it in its front matter as the key. The id changes on `/clear`, so a `/handoff` after `/clear` starts a new handoff, which is fine.
