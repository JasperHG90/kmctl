---
type: spike
title: Spike langfuse-traces/2
description: does a full-length audit trace (64 chat spans, ~30 MB of gen_ai.* attributes, spans near 1 MB) reach Langfuse cloud over OTLP whole, with input, output, model and usage on every chat span?
tags:
- spike
generated:
  by: process:loopctl/2.2.1.dev10+g138a8c2ed.d20261017
  at: '2026-10-17T18:22:50+00:00'
slug: langfuse-traces
n: 2
outcome_written: true
---

# Spike langfuse-traces/2

does a full-length audit trace (64 chat spans, ~30 MB of gen_ai.* attributes, spans near 1 MB) reach Langfuse cloud over OTLP whole, with input, output, model and usage on every chat span?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-langfuse-live/run.sh /tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-langfuse-live/okf-vs-code-transcript.json
```

## Outcome

Exit 0. The run replayed the largest real DeepSeek V4.1 Flash audit transcript (okf-vs-code: 64 model requests, 102 tool returns, 1 output retry) through a FunctionModel with PydanticAI 2.57's default instrumentation (include_content on) and the default BatchSpanProcessor. It sent 166 spans in one OTLP request of 32.66 MB protobuf. The chat input attributes add up to 29.9 MB, and the largest is 0.81 MB. Langfuse cloud returned 200 with no exporter warning.
Langfuse's API gave back all 166 of 166 spans as observations within 44 s, plus a trace named after the run. All 64 chat spans are GENERATIONs with model, output, usageDetails (input, output, input_cached_tokens, total) and the full input: the largest came back at 819 kB for 807 kB sent.
This rules out a size limit or truncation at this scale, so no fix was needed (no small batch size, no include_content=False). It settles risk 2 with the defaults.
Limits: one run, on one transcript (the largest of the three; the 83-request upper estimate was not replayed). Langfuse cloud only, not self-hosted. The read API returned 429 under polling, so readers must back off.
Trace: abf43df87ea9ac2dfea6872d2d05300a.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/replay.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-langfuse-live/replay.py`, which the command used
- `files/run.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-langfuse-live/run.sh`, which the command used
- `files/okf-vs-code-transcript.json`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-langfuse-live/okf-vs-code-transcript.json`, which the command used
