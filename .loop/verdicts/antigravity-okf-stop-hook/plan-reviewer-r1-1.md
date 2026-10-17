---
type: verdict
title: 'Verdict: antigravity-okf-stop-hook plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of antigravity-okf-stop-hook: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T06:35:04+00:00'
slug: antigravity-okf-stop-hook
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The listed risk is settled by spike 2. One risk the plan does not list is
open (p1): whether executionNum goes back to 0 on each user turn. A two-turn
spike settles it before building.

## Checked

- spike:antigravity-okf-stop-hook/2: a Stop handler in the plugin folder's
  hooks.json, run from the plugin folder with `cd ../../..`, rewriting okf's
  block to `"decision":"continue"`, made agy re-enter the loop with okf's
  reason (the agent ran git status and git diff and read .okf/). The second
  stop came with executionNum 1 and ended. Spike 1 shows the counter starts
  at 0, not the docs' 1.
- Removing APM's okf handler from .agents/hooks.json does not break a later
  install. In APM 0.33.0, `integration/hook_integrator.py` (about lines
  1263-1405) reads the file, puts back `_apm_source` from apm-hooks.json,
  drops the entries it owns and appends fresh ones. That merge only adds and
  has no skip path for hooks.json, so a second `kmctl plugin install` gets
  the handler back and kmctl removes it again, with no SKIP_LINE failure. A
  bare `apm install` puts it back too, which the planned doctor check
  catches. apm-hooks.json keeps an entry that matches nothing on disk, which
  does no harm.
- okf-stop-check.sh reads `.okf/` and git from its working folder and only
  checks `stop_hook_active` on stdin, so `{}` on stdin from the repository
  root is what it needs.

## Findings

- p1 (premise, blocking): both spikes ran `agy -p`, which is one user turn.
  Spike 2 shows a forced continue moves executionNum from 0 to 1, so the
  counter counts executor runs. Nothing shows it goes back to 0 when the user
  sends the next message. If it keeps counting through a conversation, the
  hook fires only on the first turn of an interactive session, so "continues
  only on the first stop of a turn" is false and the guard needs another
  design, such as state keyed by conversationId. Spike question: in a
  two-turn conversation (a second message to the same conversation), what
  executionNum does the first Stop of turn 2 carry?
