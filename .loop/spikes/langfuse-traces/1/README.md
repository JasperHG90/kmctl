---
type: spike
title: Spike langfuse-traces/1
description: 'does PydanticAI 2.57 instrumentation with a plain OTel TracerProvider (no Logfire) emit the gen_ai.* attributes Langfuse maps: model, token usage, input/output messages, tool arguments and results?'
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T17:58:44+00:00'
slug: langfuse-traces
n: 1
outcome_written: true
---

# Spike langfuse-traces/1

does PydanticAI 2.57 instrumentation with a plain OTel TracerProvider (no Logfire) emit the gen_ai.* attributes Langfuse maps: model, token usage, input/output messages, tool arguments and results?

The command exited 0:

```
uv run -q --script /tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-langfuse/spike.py
```

## Outcome

Exit 0: with pydantic-ai-slim 2.57.0, opentelemetry-sdk and otlp-proto-http 1.45.1 and no `logfire` installed, a FunctionModel agent with one tool and a pydantic output emitted an `invoke_agent agent` root span with 2 `chat fake-model` spans and 1 `execute_tool read_file` span under it.
Each chat span carries `gen_ai.request.model`, `gen_ai.usage.input_tokens`/`output_tokens` (53/6, 57/13), and `gen_ai.input.messages`/`gen_ai.output.messages` as JSON span attributes, not events. The tool span carries `gen_ai.tool.name`, `gen_ai.tool.call.arguments` and `gen_ai.tool.call.result`. The root span has `final_result` and `gen_ai.aggregated_usage.*`.
API change: 2.57's `Agent` has no `instrument=` keyword. Pass `capabilities=[Instrumentation(settings=InstrumentationSettings(tracer_provider=p))]` (from `pydantic_ai.capabilities`), or set `agent.instrument`. The default is `version=5` with `include_content=True`, and there is no event-mode option.
`logfire` is never imported. Only the bundled `logfire_api` no-op shim loads. The OTLPSpanExporter builds with the `/api/public/otel/v1/traces` endpoint and a `Basic` authorization header. `provider.shutdown()` flushed a held BatchSpanProcessor span (0 before, 1 after).
This settles risk 1 for the emitting side. Whether Langfuse maps these attributes is untested here and needs the live check.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-langfuse/spike.py`, which the command used
