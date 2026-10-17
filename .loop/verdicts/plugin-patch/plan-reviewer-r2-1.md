---
type: verdict
title: 'Verdict: plugin-patch plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of plugin-patch: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T12:57:14+00:00'
slug: plugin-patch
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

Both round 1 findings are resolved. Spike plugin-patch/1 shows that, at
project scope, a second plain `apm install` writes okf-bundle back to both
MCP files once the stale entry is gone. The plan now has patch refuse
consumers on the old entry forms and name the commands to run. One new gap
remains. The plan keeps `--scope user`, but no evidence shows APM writes
okf's server at user scope, and patch's cleanup there deletes the server
kmctl wrote. A spike can settle it, so the verdict is fail, not reject.

## Checked

- The plan, its empty eval, and my round 1 verdict.
- Spike plugin-patch/1: README outcome, run.json (exit 0), stdout.txt and
  the script. The script seeds an older-pin okf-bundle plus another server,
  installs a local package that declares okf-bundle under
  dependencies.mcp, deletes the entry from both files and installs again.
  Both files held the package's launcher afterwards and the other server
  stayed. That answers p1 for project scope.
- src/kmctl/plugin.py: `_old_layout`, `_names_old_package`,
  `remove_old_apm_entry`, `uninstall_name`, `kmctl_package`, `read_lock`,
  `install_mcp`. The detection patch needs for p2 exists today, and
  `uninstall_name` already gives the exact `apm uninstall` name.
- `install_mcp` at user scope writes okf-bundle through `claude mcp
  add-json --scope user`, not through APM. The apm-hands-back plan and its
  spikes 1 to 3 cover project scope only. apm-only-install/2 showed `apm
  install -g` writing skills, agents and rules under CLAUDE_CONFIG_DIR, but
  not MCP servers.

## Findings

- p1 (resolved): spike:plugin-patch/1 shows the remove-then-reinstall
  order restores okf-bundle at project scope.
- p2 (resolved): the plan names the refusal and what it tells the user.
  The detection code already exists in plugin.py.
- p3 (open, premise): user scope. Spike question for spike-runner: "With
  apm-cli 0.33.0, HOME and CLAUDE_CONFIG_DIR pointed at scratch, run `apm
  install -g` of a package that declares okf-bundle under dependencies.mcp
  with --target claude (and antigravity). Does APM write okf-bundle into
  Claude Code's user MCP config (~/.claude.json mcpServers, or wherever
  `claude mcp list --scope user` reads)? If a different okf-bundle is
  already there, does it skip it, and does deleting it and installing again
  bring it back?" If APM does not write it, patch must keep writing the
  user-scope server itself, or the plan must drop `--scope user` or say
  that APM cannot write it there. That is a revision. The question also
  touches apm-hands-back, which drops kmctl's MCP write at every scope.

## Notes

The plan has patch refuse "when the lock lists no kmctl package" and also
refuse the old entry forms. `kmctl_package` matches only `virtual_path:
apm`, so a v0.3.0-layout lock (`virtual_path: plugin`) has no kmctl
package. The old-form check has to run first, or those users get told to
run `apm install`, which changes nothing for them. This is a detail for the
build to get right, not a plan risk. The eval still has no rows. The "It
worked when" paragraph names the checks that should become rows.
