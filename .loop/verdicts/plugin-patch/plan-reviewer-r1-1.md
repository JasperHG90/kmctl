---
type: verdict
title: 'Verdict: plugin-patch plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of plugin-patch: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T12:55:09+00:00'
slug: plugin-patch
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach holds. APM installs, and kmctl writes only the Antigravity
agents and the okf Stop fix. Most of what patch keeps is code that exists
today (write_plugin, drop_apm_okf_stop, remove_old_plugin, kmctl_hooks), and
apm-hands-back's spikes already cover APM's side. The plan lists no risks,
but two gaps could break it. One APM behaviour on re-install has never been
checked, which a spike can settle. The other is a migration case the plan
does not cover. Neither needs a rethink, so the verdict is fail, not reject.

## Checked

- Read the plan, its empty eval, and the apm-hands-back plan with spikes 1
  to 3 (README outcome and stdout of 3).
- src/kmctl/plugin.py: install's order (remove_old_apm_entry, then
  write_manifest, apm install, remove_old_plugin, merge_hook, install_mcp,
  then the Antigravity steps), read_lock, kmctl_package, remove_old_plugin,
  install_mcp at user scope (it needs the claude CLI, not APM).
- src/kmctl/doctor.py harnesses_found: it already reads the harnesses from
  the lock's deployed_files, as the plan assumes patch will.
- src/kmctl/antigravity.py: OKF_AGENTS comes from apm_modules/, and
  plugin_files fails when that folder is missing. That matches the plan's
  "after apm install" order.
- action.yml, the justfile and scripts do not call kmctl plugin
  install/update/remove, so removing them breaks no CI path in the repo.

## Findings

- p1 (premise): after the stale okf-bundle is removed, a second apm install
  may not write it back. Spike question for spike-runner: "With apm-cli
  0.33.0, in a consumer whose .mcp.json held an okf-bundle different from
  the package's, run apm install (it skips okf-bundle and records it in the
  lock), delete okf-bundle from .mcp.json and .agents/mcp_config.json, then
  run apm install again with no flags. Does APM write okf-bundle back to
  both files? If not, does --force, or what does?" If it does not come back,
  patch should rewrite the entry itself or the order must change. That is a
  revision, not a rethink.
- p2 (missing): consumers with the ADR 0013 string entry or the v0.3.0
  layout. Today only install's apm uninstall moves them over. The plan
  removes install and does not say how patch detects them or what it tells
  the user to run.

## Notes

The eval has no rows yet. The plan's "It worked when" paragraph names the
checks that should become rows: doctor passing for both harnesses, a clean
removal, and plugin install gone. Plus one for p1's upgrade path once it is
settled.
