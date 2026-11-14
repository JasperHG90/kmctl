---
type: spike
title: Spike kmaudit-mcp/1
description: how large claims todo and checks todo results are on this repository's .okf, against Claude Code's ~25k-token tool result warning
tags:
- spike
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T13:46:47+00:00'
slug: kmaudit-mcp
n: 1
outcome_written: false
---

# Spike kmaudit-mcp/1

how large claims todo and checks todo results are on this repository's .okf, against Claude Code's ~25k-token tool result warning

The command exited 0:

```
uv run python -c 
import json, shutil, subprocess
from pathlib import Path
def size(args):
    out = subprocess.run(['uv','run','kmaudit',*args], capture_output=True, text=True).stdout
    d = json.loads(out)
    return len(out), d
for f in ('.kmctl', '.kmaudit'):
    shutil.rmtree(f, ignore_errors=True)
n, d = size(['claims','todo','--json'])
print('claims todo, all pending:', n, 'bytes, ~', n//4, 'tokens,', len(d['sections']), 'sections')
biggest = max(len(json.dumps(s)) for s in d['sections'])
print('largest single section:', biggest, 'bytes')
n, d = size(['claims','todo','--json','--limit','15'])
print('claims todo --limit 15:', n, 'bytes, ~', n//4, 'tokens')
Path('.kmctl').mkdir(exist_ok=True)
shutil.copy('/home/vscode/workspace/.kmctl/audit.sqlite', '.kmctl/audit.sqlite')
n, d = size(['checks','todo','--json','--limit','5'])
print('checks todo --limit 5:', n, 'bytes, ~', n//4, 'tokens,', len(d['claims']), 'claims')
n, d = size(['checks','todo','--json','--limit','5','--brief'])
print('checks todo --limit 5 --brief:', n, 'bytes, ~', n//4, 'tokens')

```

## Outcome

Not written yet: `loopctl plan spike-note kmaudit-mcp 1`.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
