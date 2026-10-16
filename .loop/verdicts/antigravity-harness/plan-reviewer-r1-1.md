---
type: verdict
title: 'Verdict: antigravity-harness plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of antigravity-harness: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-16T20:21:02+00:00'
slug: antigravity-harness
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach holds. APM delivers skills and rules to `.agents/`. A kmctl-owned workspace plugin
carries the translated agents, the hook and the MCP server. Spike 3 confirms that agy discovers
the workspace plugin, and spike 1 confirms the URL-run MCP server works when it is given the
bundle path. Two things are still open. The way the MCP server finds `.okf` depends on PLUGIN_ROOT,
and the agy binary does not show that MCP servers get it (p1, worth a spike). The live part of
risk 1 has neither a spike nor an operator acceptance (p2). Neither one invalidates the plan, and
two risks do not call for a split.

## Checked

- Spikes 1, 2 and 3 (README, stdout, run.json). Spike 1 answers the MCP-over-URL risk, including
  the failure without an argument from another folder. Spike 3 answers discovery and trust for
  agents only; its own outcome says the hook and MCP need a live session.
- The agy 1.4.0 binary's strings (`~/.local/bin/agy`). `PLUGIN_ROOT=` appears once, next to
  `PLUGIN_DATA=` and `sidecar.json`. The MCP guide documents command, args and env only. The
  plugin guide says a plugin's mcp_config.json servers are launched, and that hooks.json must sit
  at the plugin root, which the plan does. SessionStartHookResult has InjectSteps, and
  workspacePaths appears in the binary, so the hook shape is plausible; any detail is left to the
  build.
- okf-skills at the pinned commit, from a spike consumer's `apm_modules/scaccogatto/okf-skills/agents/`.
  bundle-weaver uses Read, Write, Edit, Bash, Grep and Glob, and event-analyzer uses Bash, Read and
  Write, so the translator map covers both. In the same consumer, APM's antigravity target wrote
  okf's Stop hook into `.agents/hooks.json`, which does not conflict with the plugin's hook.
- apm-only-install's plan: the `--source` apm.yml entry, `targets:`, and `plugin status` kept
  until kmctl-doctor. r5's "or its successor" covers that.

## Findings

- p1: PLUGIN_ROOT for plugin MCP servers is unproven. If it is wrong, the okf MCP server starts
  but every tool call fails, and no row catches it. This needs a spike or a design that does not
  depend on it.
- p2: the live hook and MCP part of risk 1 has no spike and no operator acceptance, and its
  fallback widens scope into user-level config.

## Notes

The plan's claim that backfill "then works in Antigravity" assumes the skill's agent references
(`okf:event-analyzer`) resolve to the plugin's agents. That is a build detail, not a plan risk.
