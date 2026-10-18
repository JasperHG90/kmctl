---
type: verdict
title: 'Verdict: okf-summary-nudge plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of okf-summary-nudge: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-18T21:52:36+00:00'
slug: okf-summary-nudge
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

Both listed risks are settled by real evidence. Spike 2 shows Claude Code 2.1.302
delivers PostToolUse `additionalContext` after Write and Bash, with `cwd`,
`tool_name` and `tool_input` on stdin, and that empty output or `{}` is harmless.
Spike 3 shows APM 0.33.0 deploys the PostToolUse entry into `.claude/settings.json`
exactly once across reinstalls, tracked in `.claude/apm-hooks.json`. Spike 1 was a
broken command and the plan rightly does not cite it. One risk the plan does not
list could break it: the pin hand-off (ADR 0026) would send every matching tool
call through uvx online in a project whose pin differs from the copy on PATH.
That is one fix to the plan, not a reason to split the ticket.

## Checked

- Spike folders 1 to 3: README outcomes, stdout, stderr and run.json. The evidence
  answers both risks. Edit and MultiEdit were not exercised, but they share the
  matcher, and the plan's done-when uses Bash.
- apm/claude/.apm/hooks/hooks.json: the SessionStart guard pattern
  (`command -v kmctl ... ; exit 0`) the plan says it copies.
- src/kmctl/pin.py `hand_off`/`handoff_pin` and src/kmctl/__init__.py `main`. The
  hand-off runs before Typer parses, and every verb but `briefing` goes through
  uvx online. stdin is inherited, so the payload would reach the child.
- src/kmctl/summary.py: `changed_concepts` uses git only, as the plan claims.
- src/kmctl/doctor.py `_claude_hook` and src/kmctl/plugin.py `kmctl_hooks`/`drop_old_hook`
  read SessionStart only, so a new `claude.nudge-hook` check is additive and
  `drop_old_hook` leaves the PostToolUse entry alone.
- tests/test_plugin.py `test_hook_the_package_ships_is_one_sessionstart_entry`
  asserts the package ships only SessionStart. It must change with ADR 0004's
  supersession. r6 covers it, so it is a build detail.
- The eval rows r1 to r6 match the plan's intent and done-when. The only gap is
  the hand-off case under p1.

## Findings

- p1: the plan does not say how `summary nudge` passes through the pin hand-off.
  The online uvx path would run on every Write, Edit, MultiEdit and Bash call
  in a project pinned to another release, and could time out there. In a
  project pinned to a release older than this ticket, it runs a copy that lacks
  the verb. A spike can settle the question: in a project whose apm.lock.yaml pins
  another kmctl release, time `kmctl summary nudge --format claude < payload`
  through the hand-off with the pin cached and uncached, and record what an old
  pinned release prints. The plan then picks the briefing-style offline path,
  or no hand-off, and adds the quiet case to r2.

## Notes

The briefing budget is untouched, because the plan adds nothing to the briefing.
