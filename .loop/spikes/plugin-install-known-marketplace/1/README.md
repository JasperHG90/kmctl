---
type: spike
title: Spike plugin-install-known-marketplace/1
description: 'user settings declare scaccogatto from a git URL: the fixed-source add fails, and adding from the entry URL lets the kmctl install resolve okf'
tags:
- spike
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T14:28:34+00:00'
slug: plugin-install-known-marketplace
n: 1
outcome_written: true
---

# Spike plugin-install-known-marketplace/1

user settings declare scaccogatto from a git URL: the fixed-source add fails, and adding from the entry URL lets the kmctl install resolve okf

The command exited 0:

```
python3 /tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/mkt-repro/spike.py
```

## Outcome

Exit 0. With user settings declaring `scaccogatto` from `https://github.com/scaccogatto/okf-skills.git`, `claude plugin marketplace add scaccogatto/okf-skills --scope project` fails with the operator's exact message. Adding from the entry's own URL succeeds, and `claude plugin install kmctl@kmctl --scope project` then installs with okf as a dependency. An earlier run showed that skipping the okf add fails the install on `Dependency "okf@scaccogatto" ... not found`. So the fix is to add from the settings entry's source. One git-URL case on claude 2.1.300; github, url and directory kinds follow the same add argument and are covered by stub tests.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/mkt-repro/spike.py`, which the command used
