---
type: spike
title: Spike fix-audit-drift/1
description: the 35 findings of the three DeepSeek V4.1 Flash audits (docs-vs-code, okf-vs-code, okf-vs-docs) on main at 02c72d80, kept as the ticket's input
tags:
- spike
generated:
  by: process:loopctl/2.2.1.dev14+g22f6ca3aa.d20261017
  at: '2026-10-17T18:43:03+00:00'
slug: fix-audit-drift
n: 1
outcome_written: true
---

# Spike fix-audit-drift/1

the 35 findings of the three DeepSeek V4.1 Flash audits (docs-vs-code, okf-vs-code, okf-vs-docs) on main at 02c72d80, kept as the ticket's input

The command exited 0:

```
python3 -c 
import json
for a in ('docs-vs-code','okf-vs-code','okf-vs-docs'):
    r=json.load(open('/tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/real-audits-main/out-'+a+'/report.json'))
    print('=== '+a); print(json.dumps(r,indent=1))

```

## Outcome

Exit 0: the three audits' report.json files, printed in full to stdout.txt: docs-vs-code 7 findings (1 high, 3 medium, 3 low), okf-vs-code 21 (12 medium, 9 low), okf-vs-docs 7 (2 medium, 5 low); 35 in all. This is the ticket's input list; each finding is checked against the code before anything is fixed.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
