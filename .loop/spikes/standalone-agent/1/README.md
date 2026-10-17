---
type: spike
title: Spike standalone-agent/1
description: does PydanticAI 2.57 run tool calls and validate a typed pydantic output_type through a plain OpenAI-compatible base URL (Gemini 3.8 Flash)?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T07:01:19+00:00'
slug: standalone-agent
n: 1
outcome_written: true
---

# Spike standalone-agent/1

does PydanticAI 2.57 run tool calls and validate a typed pydantic output_type through a plain OpenAI-compatible base URL (Gemini 3.8 Flash)?

The command exited 1:

```
uv run --no-project /tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-standalone-agent/pydantic_ai_tools_report.py
```

## Outcome

Script bug, not a PydanticAI failure: the run exited 1 only because `result.usage` is a property in pydantic-ai 2.57.0 and the script called it (`result.usage()`).
Before that line, everything worked. Gemini 3.8 Flash on the OpenAI-compatible endpoint made the calls read_file, then run_shell, then final_result, and the output validated as Report. The Report holds one medium finding with evidence quoted from both files.
Run 2 repeats this with the bug fixed and is the run to cite.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/pydantic_ai_tools_report.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-standalone-agent/pydantic_ai_tools_report.py`, which the command used
