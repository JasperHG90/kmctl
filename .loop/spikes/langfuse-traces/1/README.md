---
type: spike
title: Spike langfuse-traces/1
description: 'does PydanticAI 2.57 instrumentation with a plain OTel TracerProvider (no Logfire) emit the gen_ai.* attributes Langfuse maps: model, token usage, input/output messages, tool arguments and results?'
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T17:58:32+00:00'
slug: langfuse-traces
n: 1
outcome_written: false
---

# Spike langfuse-traces/1

does PydanticAI 2.57 instrumentation with a plain OTel TracerProvider (no Logfire) emit the gen_ai.* attributes Langfuse maps: model, token usage, input/output messages, tool arguments and results?

The command exited 0:

```
uv run -q --script /tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-langfuse/spike.py
```

## Outcome

Not written yet: `loopctl plan spike-note langfuse-traces 1`.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-langfuse/spike.py`, which the command used
