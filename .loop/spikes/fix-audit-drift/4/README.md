---
type: spike
title: Spike fix-audit-drift/4
description: 'the okf-vs-docs findings of the DeepSeek V4.1 Flash audit on main at 02c72d80: severity, title, path, claim, contradicted_by and fix for each'
tags:
- spike
generated:
  by: process:loopctl/2.2.1.dev14+g22f6ca3aa.d20261017
  at: '2026-10-17T18:46:09+00:00'
slug: fix-audit-drift
n: 4
outcome_written: false
---

# Spike fix-audit-drift/4

the okf-vs-docs findings of the DeepSeek V4.1 Flash audit on main at 02c72d80: severity, title, path, claim, contradicted_by and fix for each

The command exited 0:

```
python3 -c 
import json
r=json.load(open('/tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/real-audits-main/out-okf-vs-docs/report.json'))
print(json.dumps([{k:f[k] for k in ('severity','title','path','claim','contradicted_by','fix')} for f in r['findings']],indent=1))

```

## Outcome

Not written yet: `loopctl plan spike-note fix-audit-drift 4`.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
