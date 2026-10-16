---
type: spike
title: Spike apm-only-install/7
description: after an old claude-plugin install, does claude plugin uninstall kmctl@kmctl leave okf@scaccogatto enabled, and do uninstalling okf and removing the kmctl marketplace leave no kmctl or okf plugin enabled for the repo?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev173+ga4f6ce93a.d20261016
  at: '2026-10-16T20:27:14+00:00'
slug: apm-only-install
n: 7
outcome_written: true
---

# Spike apm-only-install/7

after an old claude-plugin install, does claude plugin uninstall kmctl@kmctl leave okf@scaccogatto enabled, and do uninstalling okf and removing the kmctl marketplace leave no kmctl or okf plugin enabled for the repo?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-migrate/p2.sh
```

## Outcome

Answers plan review finding p2 (old claude-plugin users), under risk 4. This ran today's `kmctl plugin install --scope project` with claude 2.1.301, with HOME, CLAUDE_CONFIG_DIR and XDG_DATA_HOME pointed at scratch.
- After `claude plugin uninstall kmctl@kmctl --scope project` (exit 0), okf@scaccogatto is still installed and enabled. claude prints `1 auto-installed dependency no longer needed: okf. Run 'claude plugin prune --scope project' to remove.` `.claude/settings.json` keeps `enabledPlugins: {okf@scaccogatto: true}` and both `extraKnownMarketplaces` entries (scaccogatto, and kmctl as a directory source). `marketplace list` still shows both. So the plan's single uninstall leaves okf's skills loading from the plugin cache on top of APM's copies.
- After `claude plugin uninstall okf@scaccogatto --scope project` and `claude plugin marketplace remove kmctl` (both exit 0), `plugin list` is empty and `enabledPlugins` is `{}`. The kmctl marketplace is gone from settings.json and from the list, but the `scaccogatto` marketplace entry stays in both. The spike exits 0.
Settles finding p2 if the plan runs all three commands, not just the kmctl uninstall. Not tested: `claude plugin prune` instead of the okf uninstall, user scope, and a repo where okf was enabled for its own sake (uninstalling it there would remove something the user chose). The real ~/.claude was untouched.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/p2.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-migrate/p2.sh`, which the command used
