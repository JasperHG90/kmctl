---
type: spike
title: Spike plugin-install-verb/1
description: does claude plugin install pull a cross-marketplace dependency when its marketplace has not been added?
tags:
- spike
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T08:13:08+00:00'
slug: plugin-install-verb
n: 1
outcome_written: true
---

# Spike plugin-install-verb/1

does claude plugin install pull a cross-marketplace dependency when its marketplace has not been added?

The command exited 1:

```
/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-plugin-install/cross-mkt.sh
```

## Outcome

The risk is real. With claude 2.1.300 and an isolated CLAUDE_CONFIG_DIR, installing a throwaway plugin that depends on `okf@scaccogatto` (allowlisted in `allowCrossMarketplaceDependenciesOn`, declared in the marketplace entry) failed with exit 1 while the scaccogatto marketplace was not added: `Dependency "okf@scaccogatto" (required by tiny@spike-mkt) not found. Is the "scaccogatto" marketplace added?`. It installed nothing and did not add the marketplace itself.
After `claude plugin marketplace add scaccogatto/okf-skills`, the same install exited 0 with `(+ 1 dependency: okf)` and installed okf 0.10.3 at user scope. Running the install again exited 0 with "already installed".
So `kmctl plugin install` has to add the scaccogatto marketplace (`claude plugin marketplace add scaccogatto/okf-skills`) before it installs the plugin. Settles risk 1 as real.
Limits: tested at user scope only, with a local folder marketplace standing in for kmctl's, and with okf's marketplace taken from GitHub HEAD.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/cross-mkt.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-plugin-install/cross-mkt.sh`, which the command used
