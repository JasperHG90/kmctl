---
type: verdict
title: 'Verdict: okf-summary-nudge-agy-opencode plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of okf-summary-nudge-agy-opencode: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-18T22:02:11+00:00'
slug: okf-summary-nudge-agy-opencode
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

Both risks the plan lists are settled by live spikes. One gap could break the plan: the OpenCode half never says what goes to the nudge verb on stdin. The parent verb reads stdin and is quiet when stdin is empty, so the plugin either hangs for the full timeout on every tool call or never nudges. Revise the plan to fix that contract. The rest holds.

## Checked

- Spike 1 (agy 1.4.0): README, stdout, run.json and script. PostToolUse fired after write_to_file in `WS/.agents`, with workspacePaths on stdin, and the injectSteps systemMessage reached the model. That settles risk 1. The plan already records the caveat that injectSteps is undocumented for PostToolUse (r5).
- Spike 1 used the nested `{matcher, hooks}` form, but APM writes SessionStart and Stop to `.agents/hooks.json` flat. I read APM 0.33.0's source (`apm_cli/integration/hook_native_formats.py`, `_to_antigravity_hook_entries`, `_ANTIGRAVITY_NESTED_EVENTS = {PreToolUse, PostToolUse}`). It renders PostToolUse for Antigravity in the nested form with default matcher `*`, which is the form the spike proved. So APM delivering the entry is not a risk.
- Spike 2 (OpenCode 2.0.32): `ctx.tool.hook("execute.after")` fired once after `write`, `process.cwd()` was the project, and text appended to `event.result.content` reached the model. That settles risk 2.
- `src/kmctl/opencode.py` PLUGIN_SOURCE: the briefing runs through execFile with `cwd` and a timeout, passes `--path`, and writes nothing to stdin. Node is installed (v24.21.0), and tests/test_opencode.py runs the plugin under node with a stub ctx, so r4's node test is feasible.
- The parent plan and its eval (okf-summary-nudge r1, r2): the verb reads stdin and is quiet on empty or unreadable stdin. That is the source of p1.
- Eval rows r1 to r6 match the plan's Done-when and its four changes.

## Findings

- p1: the stdin contract for `--format opencode` and the plugin is missing. As written, OpenCode either hangs for HOOK_TIMEOUT on every tool call or never nudges. See the claim.

## Notes

These are for the build, not findings:
- `_flat_commands` and `hook_present` in `src/kmctl/antigravity.py` read only flat handler lists. APM writes PostToolUse nested (groups with `hooks`), so the doctor check for r3 has to look inside the groups. A fixture built from the flat SessionStart shape would hide this.
- agy's matcher `*` and OpenCode's execute.after run kmctl after every tool call, reads included. Claude's hook runs only after Write|Edit|MultiEdit|Bash. `kmctl --version` starts in about 0.25 s here. Filtering by tool name (agy's matcher, or a tool check in JS) would cut that cost, but leaving it out does not break the plan.
