---
type: spike
title: Spike standalone-agent/2
description: does PydanticAI 2.57 run tool calls and validate a typed pydantic output_type through a plain OpenAI-compatible base URL (Gemini 3.8 Flash and 2.5 Flash)?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T07:01:53+00:00'
slug: standalone-agent
n: 2
outcome_written: true
---

# Spike standalone-agent/2

does PydanticAI 2.57 run tool calls and validate a typed pydantic output_type through a plain OpenAI-compatible base URL (Gemini 3.8 Flash and 2.5 Flash)?

The command exited 0:

```
uv run --no-project /tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-standalone-agent/pydantic_ai_tools_report.py
```

## Outcome

PASS, exit 0. pydantic-ai-slim 2.57.0 with OpenAIChatModel and OpenAIProvider(base_url=Gemini's OpenAI-compatible endpoint) ran both tools and returned a validated Report on gemini-3.8-flash and gemini-2.5-flash.
Each model made the calls read_file, run_shell, final_result. 3.8 Flash used 3 requests (one tool per turn); 2.5 Flash used 2 (both tools in one turn). Each run cost under $0.002.
No special output mode was needed: the default tool output mode (a `final_result` tool) validated the nested Literal and list fields first time, with no retries.
This rules out "PydanticAI cannot do tools plus a typed report over a plain base URL" for Gemini. Limits: one provider (Gemini), two models, one tiny task. Other OpenAI-compatible servers (OpenRouter, Ollama) were not tried.
Settles risk 1 for the Gemini models the audit will use.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/pydantic_ai_tools_report.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-standalone-agent/pydantic_ai_tools_report.py`, which the command used
