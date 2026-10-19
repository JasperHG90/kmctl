---
type: verdict
title: 'Verdict: drop-summary-nudge plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of drop-summary-nudge: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-19T05:12:17+00:00'
slug: drop-summary-nudge
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The plan lists no risks. I found none that could break it. No spike is needed. This ticket is one removal across three harnesses, so there is no reason to split it.

## Checked

- Every nudge site the plan names exists, and those are the only sites in shipped code. They are `apm/claude/.apm/hooks/hooks.json`, `apm/antigravity/.apm/hooks/hooks.json`, both `apm.yml` files, the `kmctl summary nudge` command in `src/kmctl/__init__.py`, the nudge code in `src/kmctl/summary.py` (`nudge`, `Nudge`, `NUDGE_STATE`, `nudge_text`), the doctor checks `_claude_nudge_hook`, `_antigravity_nudge_hook` and `_opencode_nudge_hook`, the `NUDGE_*` names and helpers in `plugin.py` and `antigravity.py`, and the OpenCode `execute.after` hook and `nudge_problems`. Outside `src/`, `apm/`, `docs/` and the README, grep finds the nudge only in `.okf/` concepts, `.claude/rules/cli-version-floor.md` and tests, and the plan covers all of these. `.claude/skills/rule-creator` uses "nudge" in an unrelated sense and sits outside the r3 grep paths.
- No other code calls any of the nudge pieces. `as_antigravity` and `KMCTL_PINNED`/`pin.py` are shared with the briefing and must stay. The plan removes only the helpers "that only they used", so it already allows for this.
- The Antigravity hooks.json also has kmctl's Stop hook (ADR 0018). Eval r1 says this hook stays, so the outcome line "ship SessionStart only" is looser than the contract but cannot mislead the build.
- The next decision number is 0029, which matches r3's `0029-*.md` glob. "status: deprecated" is how this repo marks a superseded decision (0004 is marked that way today).
- Old installs: both the Claude and Antigravity hook commands send stderr to /dev/null and fall back to `{}` when the verb fails, so a leftover entry does no harm. Since there are no outside users, a migration is not needed.

## Findings

None.
