---
type: spike
title: Spike fix-audit-drift/2
description: 'the docs-vs-code findings of the DeepSeek V4.1 Flash audit on main at 02c72d80: severity, title, path, claim, contradicted_by and fix for each'
tags:
- spike
generated:
  by: process:loopctl/2.2.1.dev14+g22f6ca3aa.d20261017
  at: '2026-10-17T18:46:21+00:00'
slug: fix-audit-drift
n: 2
outcome_written: true
---

# Spike fix-audit-drift/2

the docs-vs-code findings of the DeepSeek V4.1 Flash audit on main at 02c72d80: severity, title, path, claim, contradicted_by and fix for each

The command exited 0:

```
python3 -c 
import json
r=json.load(open('/tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/real-audits-main/out-docs-vs-code/report.json'))
print(json.dumps([{k:f[k] for k in ('severity','title','path','claim','contradicted_by','fix')} for f in r['findings']],indent=1))

```

## Outcome

Exit 0: the full finding list of one audit (spike 2 docs-vs-code, 3 okf-vs-code, 4 okf-vs-docs), not cut: severity, title, path, claim, contradicted_by and fix for each. Together 35 findings, the ticket's input.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
