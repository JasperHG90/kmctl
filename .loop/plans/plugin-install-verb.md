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

`kmctl plugin install [--scope project|user]` installs the plugin that ships inside this kmctl release, so the plugin and the CLI always match (ADR 0001). This follows loopctl: the wheel carries `plugin/` and the root marketplace file as package data (loopctl uses hatch `force-include`; kmctl switches its build backend from uv_build to hatchling if uv_build cannot do it). On install, kmctl copies them to one fixed staging folder, `marketplace/` under kmctl's data directory, replacing what was there, so the marketplace path never changes between releases and the committed project settings file is not rewritten on each upgrade. It never installs from GitHub HEAD.

The command order follows loopctl's working `plugin install` and `plugin update` (loop-harness src/loop_harness/commands/plugin.py, function _install_claude): `claude plugin marketplace add <staging folder>`; if that fails because the marketplace is already registered, `claude plugin marketplace update kmctl`; on `kmctl plugin update` (a newer kmctl), `claude plugin uninstall kmctl@kmctl --scope S` first; then `claude plugin install kmctl@kmctl --scope S`; then `claude plugin list --json` must show the plugin at this kmctl's version, or the command fails and says to run `kmctl plugin update`.

Before that, it adds the scaccogatto marketplace (`scaccogatto/okf-skills`) when it is missing, because spike:plugin-install-verb/1 showed `claude plugin install` fails on the okf dependency until that marketplace is added, and pulls okf once it is.

A second install at the same version changes nothing. `kmctl plugin update` from a newer kmctl replaces the staged copy and ends with the new version listed. `kmctl plugin status` reports the installed plugin's version against this CLI's. Both verbs take `--json`.

Done when, with an isolated Claude config dir: an install at the chosen scope also installs okf; a second install changes nothing; `kmctl plugin update` after the packaged plugin's version is bumped leaves the marketplace at the same path and `claude plugin list --json` showing the new version; and status reports a version mismatch after the staged copy is changed.

From planning (spike:plugin-install-verb/3): at project scope, adding both marketplaces with `--scope project` and installing with `--scope project` pulls okf, and reruns change nothing but a one-time key reorder in the project settings file (.claude/settings.json). That file then lists both marketplaces and plugins, but kmctl's staged marketplace is saved as an absolute local path, so a teammate who clones the repository runs `kmctl plugin install` once on their machine. `kmctl plugin status` says so when the declared marketplace path does not exist.

## Could invalidate this plan

- none
