---
type: plan
title: 'Plan: adr-audit-fixes'
description: "Fix what the first audit of kmctl's own decision log found: the briefing names its skills (ADR 0002), the records drop two fields no ADR allows (I4), and seven records gain their Consequences."
slug: adr-audit-fixes
epic: docs
depends_on: [okf-fields-invariant, audit-agent-and-skills]
priority: 12
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T12:47:16+00:00'
---

# adr-audit-fixes

Relayed from: none

## Intent

The audit skill's test run on this repository (plugin/skills/audit/evals/) found three kinds of drift in `.okf/decisions/`:

- ADR 0002 says the briefing tells the agent which skill to use. `ROUTING` in `src/kmctl/briefing.py` names folders and verbs but no skill. The briefing names every skill the packaged plugin ships, read from its `skills/` folder at run time so the list cannot go stale: `continue`, `handoff` and `write-docs` on main today, plus `audit` and the three review skills once audit-agent-and-skills lands, which this ticket waits for. It stays inside the I3 word budget (432 of 600 words today; seven one-line entries add about 70).
- All nine records carry `decision_status` and `decided_on` in their front matter. Neither is an OKF v0.2 field and no ADR allows them, against ADR 0009 and I4. Each record's body already says the same in its `- Status:` and `- Date:` lines, so the two fields are removed. The `supersede.py` docstring stops naming `decision_status`.
- Records 0001 to 0006 and 0008 have no Consequences section, which `.claude/rules/okf-bundle.md` asks for. Records are not rewritten, so each gains an appended `## Correction, 2026-10-15` section holding its consequences. `.okf/log.md` gets a line for every one of the nine records touched.

Measured on main today: 9 of 9 decision records carry both fields, 7 of 9 lack a Consequences heading, and the briefing names 0 of the 3 skills on main (0 of 7 once audit-agent-and-skills lands).

Done when a test fails on any front matter key in the repository's own `.okf/` that `ALLOWED_FIELDS` lacks, a test fails when every decision record does not have a Consequences heading (its own or in a Correction), a briefing test fails when a skill folder in the packaged plugin's `skills/` is not named in the briefing, the I3 budget test still passes, and the okf validator passes in strict mode.

## Could invalidate this plan

- none
