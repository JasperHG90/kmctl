---
type: plan
title: 'Plan: audit-drift-followup'
description: Fix the new mismatches the rerun of the three audits found after fix-audit-drift.
tags:
- plan
slug: audit-drift-followup
status: draft
epic: null
depends_on: [fix-audit-drift]
priority: null
generated:
  by: process:loopctl/2.2.1.dev14+g22f6ca3aa.d20261017
  at: '2026-10-17T19:26:54+00:00'
---

# audit-drift-followup

Relayed from: fix-audit-drift, the one audit rerun (DeepSeek V4.1 Flash on
the fixed tree) found these, outside the original 35.

## Intent

Check each against the code and fix the real ones, the way fix-audit-drift
did (Corrections for decisions, notes for index lines):

- ADR 0014 at lines 68-71 (the package layout before ADR 0020), 115-116
  (the wheel carries more than the skills), 117-118 (`kmctl plugin status`
  is gone) and 151-152 (the test file it names for the install).
- ADR 0012 at lines 90-93: release.py writes four apm.yml files, not two.
- ADR 0001 at lines 59-60: the wheel carries more than the skills.
- ADR 0011 at line 151: it names `apm/.apm/instructions/`, which moved to
  `apm/claude/.apm/instructions/` (ADR 0020).
- `.okf/architecture/overview.md` lines 17-18 (the action now holds
  `action/agent.py`) and 176-177 (more modules read `okf.py`).
- `docs/how-to/install-kmctl-with-apm.md` lines 80-81: APM does not write
  the Antigravity agents; `kmctl plugin patch` does.
- `docs/how-to/install-the-plugin-and-the-ci-action.md` line 206: kmctl has
  releases now, so the "`main` until then" advice can go.
- `src/kmctl/plugin.py` HOOK_DESCRIPTION and the package's `hooks.json`
  say the briefing gives "the rules"; check whether anything matches on that
  text before changing it.

## Could invalidate this plan

- none
