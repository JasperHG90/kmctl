---
type: verdict
title: 'Verdict: plugin-install-verb plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of plugin-install-verb: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T08:25:29+00:00'
slug: plugin-install-verb
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

Both round 1 findings are resolved. Spike 3 settles project scope, and the plan now says the marketplace comes from package data staged locally, never from GitHub HEAD. One new risk remains (p3). The plan names the staging folder by version, unlike loopctl, which uses one fixed path. Nothing shows that Claude Code will re-point an existing directory marketplace to a new path and pick up the new plugin version, and that is what the "newer kmctl updates the plugin" promise depends on. This needs a revision or a spike, not a rethink, so the verdict is fail.

## Checked

- Spike plugin-install-verb/3: read README.md, stdout.txt, run.json and files/project-scope-v2.sh. Exit 0. okf@scaccogatto installs at project scope with "(+ 1 dependency: okf)". Settings content is the same across runs 1 to 3, with a key reorder on run 2 only. .claude/settings.json saves the directory marketplace as an absolute path. A fresh config dir in a clone lists nothing. The plan's From-planning paragraph matches this.
- Spike 2 is superseded by spike 3, as its README says.
- loopctl's design: /home/vscode/workspace/pyproject.toml force-includes plugin/ and .claude-plugin/marketplace.json with hatchling. /home/vscode/workspace/src/loop_harness/install.py only builds a `uv tool install` command and does no staging. The staging is in src/loop_harness/commands/plugin.py: marketplace_dir() is the fixed data_dir()/"marketplace"; stage_payload replaces it and writes the CLI version into plugin.json; _install_claude runs `marketplace add`, falls back to `marketplace update`, and uninstalls before installing on update.
- kmctl pyproject.toml uses uv_build. The plan's fallback to hatchling covers packaging. plugin/ and .claude-plugin/ do not exist yet; they come from claude-plugin, the ticket this one depends on.
- The eval has no rows yet.

## Findings

- p1 resolved: spike 3 covers project scope and the plan records the teammate limit.
- p2 resolved: the source is package data staged locally, never GitHub HEAD.
- p3 open: the version-named staging folder makes upgrades depend on untested Claude Code behaviour (re-adding a directory marketplace at a new path under the same name), and it changes committed project settings on every release. Use loopctl's fixed path and its add/update/uninstall sequence, or answer the spike question in the claim.

## Notes

The "Could invalidate this plan" section says none. With p3 open, it should list the upgrade risk until a spike or a design change settles it. One ticket is still the right scope.
