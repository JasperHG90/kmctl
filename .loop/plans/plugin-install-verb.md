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

`kmctl plugin install [--scope project|user]` installs the plugin that ships inside this kmctl release, so the plugin and the CLI always match (ADR 0001). This follows loopctl: the wheel carries `plugin/` and the root marketplace file as package data (loopctl uses hatch `force-include`; kmctl switches its build backend from uv_build to hatchling if uv_build cannot do it). On install, kmctl copies them to a staging folder under the user's data directory, named by kmctl's version, and adds that folder as kmctl's marketplace. It never installs from GitHub HEAD.

Before that, it adds the scaccogatto marketplace (`scaccogatto/okf-skills`) when it is missing, because spike:plugin-install-verb/1 showed `claude plugin install` fails on the okf dependency until that marketplace is added, and pulls okf once it is.

A second install at the same version changes nothing. An install from a newer kmctl replaces the staged copy and updates the plugin. `kmctl plugin status` reports the installed plugin's version against this CLI's. Both verbs take `--json`.

Done when, with an isolated Claude config dir, an install at the chosen scope also installs okf, a second install changes nothing, and status reports a version mismatch after the staged copy is changed.

From planning (spike:plugin-install-verb/3): at project scope, adding both marketplaces with `--scope project` and installing with `--scope project` pulls okf, and reruns change nothing but a one-time key reorder in the project settings file (.claude/settings.json). That file then lists both marketplaces and plugins, but kmctl's staged marketplace is saved as an absolute local path, so a teammate who clones the repository runs `kmctl plugin install` once on their machine. `kmctl plugin status` says so when the declared marketplace path does not exist.

## Could invalidate this plan

- none
