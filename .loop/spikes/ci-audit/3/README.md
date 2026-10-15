---
type: spike
title: Spike ci-audit/3
description: does claude -p --tools Read,Grep,Glob,Agent remove NotebookEdit and other non-read tools while kmctl:kmctl-auditor still returns parseable findings?
tags:
- spike
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T12:59:28+00:00'
slug: ci-audit
n: 3
outcome_written: false
---

# Spike ci-audit/3

does claude -p --tools Read,Grep,Glob,Agent remove NotebookEdit and other non-read tools while kmctl:kmctl-auditor still returns parseable findings?

The command exited 0:

```
python3 -I /tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-ci-audit/spike3.py
```

## Outcome

Not written yet: `loopctl plan spike-note ci-audit 3`.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike3.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-ci-audit/spike3.py`, which the command used
