---
type: plan
title: 'Plan: drop-summary-nudge'
description: kmctl stops shipping the PostToolUse summary nudge for all three harnesses and goes back to one hook, the session briefing.
tags:
- plan
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-19T05:10:18+00:00'
slug: drop-summary-nudge
epic: null
depends_on: []
priority: 2
---

# drop-summary-nudge

Relayed from: none

## Intent

The operator (2026-10-19, ask j-20261019T051006+0000-e6635eec), after asking
"Do we need the nudge at all?": "Ok, drop it", then "When done, push, then
release".

Why: the summary only summarises what is on disk in `.okf/`, so a later
agent can bring it up to date as well as the one that changed a concept. The
briefing's `summary behind: N concepts changed` line, the AGENTS.md duty and
`kmctl review due` already say when it is behind. The nudge cost a kmctl
start (about 0.25 s) after each tool call, three harness hooks, three
`kmctl doctor` checks, and leaned on Antigravity's undocumented
`injectSteps` after PostToolUse.

What changes:

- **The hooks go.** The PostToolUse entries leave
  `apm/claude/.apm/hooks/hooks.json` and
  `apm/antigravity/.apm/hooks/hooks.json`, and the package descriptions in
  `apm/claude/apm.yml` and `apm/antigravity/apm.yml` stop naming them. The
  OpenCode plugin `src/kmctl/opencode.py` writes loses its
  `execute.after` hook and keeps the briefing.
- **The verb goes.** `kmctl summary nudge` leaves `src/kmctl/__init__.py`;
  `nudge`, `Nudge` and the dedupe hash leave `src/kmctl/summary.py`. The
  freshness rule, `kmctl summary ack`, the briefing line and `review due`
  stay as ADR 0027 sets them.
- **The checks go.** `claude.nudge-hook`, `antigravity.nudge-hook` and
  `opencode.nudge-hook` leave `src/kmctl/doctor.py`, with the NUDGE_*
  constants and helpers in `src/kmctl/plugin.py` and
  `src/kmctl/antigravity.py` that only they used. `tests/test_summary_nudge.py`
  goes, and the nudge tests in `tests/test_doctor.py`, `tests/test_opencode.py`
  and `tests/test_plugin.py` go or change.
- **The record.** A new decision supersedes ADR 0028 and says kmctl again
  ships one hook of its own, the SessionStart briefing, as ADR 0004 set it,
  and why the nudge went. Invariant I1 in `.okf/manifesto.md`, the
  architecture page, `.okf/summary.md`, `.claude/rules/cli-version-floor.md`,
  the README and the docs that name the nudge follow.

No migration: nobody else uses kmctl yet. A settings file that still holds an
old nudge entry stays harmless, because its guard prints `{}` when the verb
fails.

The outcome that shows it worked: `grep -ri nudge` finds nothing in `src/`,
`apm/`, `docs/` or `README.md` (tests keep only checks that it is gone); the Claude and Antigravity
packages ship SessionStart only; the full suite passes.

## Could invalidate this plan

- none
