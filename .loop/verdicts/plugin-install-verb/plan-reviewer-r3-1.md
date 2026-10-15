---
type: verdict
title: 'Verdict: plugin-install-verb plan-reviewer round 3'
description: 'plan-reviewer verdict for round 3 of plugin-install-verb: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T08:26:50+00:00'
slug: plugin-install-verb
pass: plan-reviewer
round: 3
body_schema: verdict/1
---

## Summary

p3 is resolved. The plan now uses one fixed staging folder under kmctl's data directory and the same claude command order as loopctl's `_install_claude`, which works in loopctl today. The done-when tests an update to a bumped version and checks the marketplace path stays the same. No new risk could break the plan, so the verdict is pass.

## Checked

- /home/vscode/workspace/src/loop_harness/commands/plugin.py: `marketplace_dir()` is the fixed `data_dir()/"marketplace"`; `stage_payload` removes and recopies it; `_install_claude` runs `marketplace add`, falls back to `marketplace update loopctl` on a nonzero exit, uninstalls on update, installs, then reads `plugin list --json`. The plan's order matches this.
- Spikes 1 and 3 (README outcomes): the okf marketplace must be added first, and project scope pulls okf and stays stable across reruns. The plan reflects both.
- The claude-plugin ticket (ready, not built) supplies plugin/ and the root marketplace with the okf cross-marketplace dependency. pyproject.toml still uses uv_build at static version 0.1.0; the plan covers the hatchling fallback.
- Previous verdict plan-reviewer-r2-1.md: p1 and p2 already resolved, p3 open.

## Findings

- p1 resolved: spike 3 covers project scope.
- p2 resolved: the source is staged package data.
- p3 resolved: fixed staging folder and loopctl's command order, with a bumped-version update in done-when.

## Notes

Not a finding, but worth settling while building: the post-install check compares the listed version with "this kmctl's version". loopctl makes that hold by writing the CLI version into the staged plugin.json. The plan does not say kmctl does the same. Without that step, a plugin.json version that lags the package version fails the check on every install. Stamping the version, as loopctl does, fixes it, and the done-when test for the bumped version will expose it either way.
