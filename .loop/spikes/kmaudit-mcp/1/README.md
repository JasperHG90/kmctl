---
type: spike
title: Spike kmaudit-mcp/1
description: how large claims todo and checks todo results are on this repository's .okf, against Claude Code's ~25k-token tool result warning
tags:
- spike
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T13:47:12+00:00'
slug: kmaudit-mcp
n: 1
outcome_written: true
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

Measured on this repository's .okf/ with every section pending (a fresh store) and on a copy of the operator's store for checks: claims todo with no limit is 1,109,408 bytes (~277k tokens, 211 sections); --limit 15 is 163,018 bytes (~41k tokens), past Claude Code's ~25k-token tool result warning; the largest single section is 26,165 bytes (~6.5k tokens, its earlier-sections context included). checks todo --limit 5 is ~7.9k tokens, and ~5.1k with --brief. Risk 2 holds: the claims_todo tool needs a small default limit (5 sections is about 14k tokens) and a brief mode that leaves out the instructions after the first call, which claims todo lacks today; checks_todo is fine at --limit 5.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
