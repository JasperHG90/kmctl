---
type: plan
title: 'Plan: plugin-install-verb'
description: "kmctl plugin install installs the plugin and its okf dependency through the claude CLI at project or user scope (ADR 0001, 0003)."
slug: plugin-install-verb
epic: plugin
depends_on: [claude-plugin]
priority: 8
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T08:07:35+00:00'
---

# plugin-install-verb

Relayed from: none

## Intent

`kmctl plugin install [--scope project|user]` installs the plugin that ships with this kmctl release through the `claude` CLI, so the plugin and the CLI come from the same release (ADR 0001). `kmctl plugin status` reports what is installed against this CLI's version. Both take `--json`.

Done when installing into a scratch repository also installs okf, and a second install changes nothing.

From planning: The cross-marketplace dependency may need the user to have added the scaccogatto marketplace first. If `claude plugin install` cannot add it, `kmctl plugin install` must add it, which needs checking before the install verb is designed. Settled by spike:plugin-install-verb/1: the risk is real. With the scaccogatto marketplace not added, `claude plugin install` fails ("Dependency okf@scaccogatto not found. Is the scaccogatto marketplace added?"); after `claude plugin marketplace add scaccogatto/okf-skills` the same install pulls okf. So `kmctl plugin install` adds the scaccogatto marketplace first when it is missing, then kmctl's, then installs.

## Could invalidate this plan

- none
