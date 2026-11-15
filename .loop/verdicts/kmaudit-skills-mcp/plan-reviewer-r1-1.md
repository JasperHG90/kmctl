---
type: verdict
title: 'Verdict: kmaudit-skills-mcp plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of kmaudit-skills-mcp: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-15T05:43:43+00:00'
slug: kmaudit-skills-mcp
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

One scope gap: the plan does not say who translates the moved agents for OpenCode and Antigravity. kmctl's plugin patch does that today, and it cannot handle MCP tool names. The touches also miss the kmctl tests and modules that name the agents. Both can be fixed by revising the plan; neither means rethinking it.

## Checked

The Evidence section's nested `claude -p` measurement settles the main risk: a subagent with `tools: mcp__probe__secret_word` called the project MCP tool and returned a word only the server knew. It is recorded only in prose, with no spike folder, but the loop guard explains why, and the result is specific. The permission side effect (the project allow rule did not reach the subagent in `-p` mode) matters only for headless runs. The action's agent does not run these skills.

Also fine: kmaudit's MCP server is named `kmaudit` and has the five tools plus claims_list; `kmaudit mcp` exists; release.py already tags `kmaudit-vX.Y.Z`; kmctl's audit skill and auditor agent do not use the moved skills; kmctl's briefing lists skills from its own folder, so the moved ones drop out of it on their own. The uvx-from-git cold start against MCP startup timeouts is something to watch during the build. kmaudit-cli-slim has to keep `kmaudit mcp`.

## Findings

- p1: no owner for translating kmaudit's agents into OpenCode and Antigravity form; kmctl's translators reject mcp__ tools.
- p2: touches miss test_opencode.py, test_antigravity.py, test_plugin_patch.py, kmctl's opencode.py/antigravity.py and kmaudit's cli.py help.

## Notes

One scope question, not many, so the ticket does not need a split.
