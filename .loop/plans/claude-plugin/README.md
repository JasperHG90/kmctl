---
type: plan
title: 'Plan: claude-plugin'
description: "A Claude Code plugin whose one SessionStart hook relays kmctl briefing, with okf@scaccogatto declared as a dependency (ADR 0003, 0004)."
slug: claude-plugin
epic: plugin
depends_on: [briefing]
priority: 7
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T05:10:21+00:00'
---

# claude-plugin

Relayed from: none

## Intent

Adds a plugin folder, plugin/, with its manifest (.claude-plugin/plugin.json), a marketplace at the repository root, and hooks/hooks.json holding one SessionStart hook that runs `kmctl briefing` and exits 0 when `kmctl` is missing, printing how to install it (I1).

The marketplace entry declares the `okf` dependency from marketplace `scaccogatto` and lists `scaccogatto` in `allowCrossMarketplaceDependenciesOn` (ADR 0003). Installing the plugin is the next ticket, `plugin-install-verb`; here it loads with `claude --plugin-dir plugin`.

Done when a test checks the plugin has exactly one hook and that the hook exits 0 and prints the install hint without `kmctl` on PATH.

## Could invalidate this plan

- none
