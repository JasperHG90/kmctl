---
type: spike
title: Spike audit-prompts/3
description: 'risk 2: in spike 1''s docs-vs-code report, is the renamed flag (docs/reference/commands.md:262, --by -> --with) a finding whose contradicting evidence cites source lines, not shell output?'
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T17:37:13+00:00'
slug: audit-prompts
n: 3
outcome_written: false
---

# Spike audit-prompts/3

risk 2: in spike 1's docs-vs-code report, is the renamed flag (docs/reference/commands.md:262, --by -> --with) a finding whose contradicting evidence cites source lines, not shell output?

The command exited 0:

```
python3 -c 
import json,sys
r=json.load(open('/tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-audit-prompts/run1/out-docs/report.json'))
hit=[f for f in r['findings'] if f['claim'].startswith('docs/reference/commands.md:26') and any(c.startswith('src/') for c in f['contradicted_by'])]
print(json.dumps(hit,indent=1)); sys.exit(0 if hit else 1)
```

## Outcome

Not written yet: `loopctl plan spike-note audit-prompts 3`.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
