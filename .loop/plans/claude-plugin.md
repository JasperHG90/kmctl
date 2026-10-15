---
type: plan
title: 'Plan: claude-plugin'
description: "A Claude Code plugin whose one SessionStart hook relays kmctl briefing, depending on okf@scaccogatto, installed by kmctl plugin install (ADR 0001, 0003, 0004)."
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

Adds `new:plugin/.claude-plugin/plugin.json`, a marketplace at the repository root, and `new:plugin/hooks/hooks.json` with one SessionStart hook that runs `kmctl briefing` and exits 0 when `kmctl` is missing, printing how to install it (I1).

The marketplace entry declares the `okf` dependency from marketplace `scaccogatto` and lists `scaccogatto` in `allowCrossMarketplaceDependenciesOn` (ADR 0003). `kmctl plugin install` installs the plugin through the `claude` CLI at project or user scope.

Done when a test checks the plugin has exactly one hook and that it exits 0 without `kmctl` on PATH, and installing it in a scratch repository also installs okf.

## Could invalidate this plan

- The cross-marketplace dependency may need the user to have added the scaccogatto marketplace first. If `claude plugin install` cannot add it, `kmctl plugin install` must add it, which needs checking before the install verb is designed.
