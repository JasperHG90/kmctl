---
type: spike
title: Spike antigravity-rules/3
description: in agy 1.4.0, does a plugin rule with globs **/.okf/** fire for .okf/index.md, a comma list fire for both its globs, and .okf/**, docs/** and {a,b} never fire?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T06:34:39+00:00'
slug: antigravity-rules
n: 3
outcome_written: true
---

# Spike antigravity-rules/3

in agy 1.4.0, does a plugin rule with globs **/.okf/** fire for .okf/index.md, a comma list fire for both its globs, and .okf/**, docs/** and {a,b} never fire?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-globs.sh
```

## Outcome

Exit 0: every glob claim in the plan holds for plugin rules in agy 1.4.0. Reading .okf/index.md, the rule with globs "**/.okf/**" fired and ".okf/**" did not, so ** does enter the hidden .okf/ folder. Reading docs/guide/intro.md, only "**/docs/**, **/README.md" fired; "docs/**", "{**/docs/**,**/README.md}" and "**/src/**" did not. Reading README.md, the same comma list fired, so both of its globs count.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike-globs.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-globs.sh`, which the command used
