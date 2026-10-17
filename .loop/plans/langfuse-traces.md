---
type: plan
title: 'Plan: langfuse-traces'
description: action/agent.py sends OpenTelemetry traces of each run to Langfuse over OTLP when Langfuse keys (or any OTLP endpoint) are set.
tags:
- plan
slug: langfuse-traces
epic: null
depends_on: [audit-prompts]
priority: null
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T17:57:06+00:00'
---

# langfuse-traces

Relayed from: none

## Intent

The operator wants each agent run traced in Langfuse: the model calls, tool
calls, tokens and timing, so a reviewer can see what an audit did without
reading `transcript.json`.

Tracing is optional and off by default. `action/agent.py run` turns it on
only when the environment asks for it, imports OpenTelemetry only then,
and otherwise runs exactly as today, with no new required option or input:

- `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` set: the script sends
  OTLP over HTTP to `LANGFUSE_BASE_URL` (default
  `https://cloud.langfuse.com`) plus `/api/public/otel`, with the
  `Authorization: Basic base64(public:secret)` header Langfuse documents.
- Otherwise, `OTEL_EXPORTER_OTLP_ENDPOINT` or
  `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` set: the exporter reads the
  standard OpenTelemetry variables, for any other OTLP backend.

It builds a `TracerProvider` with a batch `OTLPSpanExporter`, passes it to
the agent as the `Instrumentation` capability (`capabilities=[...]`; 2.57's
`Agent` has no `instrument=` keyword), and shuts it down
before exit so spans are flushed, also when the run fails or times out.
The PEP 723 dependencies gain `opentelemetry-sdk` and
`opentelemetry-exporter-otlp-proto-http`, pinned, and so does the dev
group. The Langfuse keys and OTLP headers stay out of the shell tool's
environment (they are not in `SHELL_ENV_KEEP`), and a failed export never
fails the run.

`action.yml` audit mode needs no new input: the step's `env` carries the
keys, as it carries the model's key. The how-to's section 5 says how to
turn tracing on, that traces hold what the agent read (file contents and
prompts) and so go to a Langfuse project the repository's readers may
see, and ADR 0017 gets a correction.

Done when the offline tests show: with Langfuse keys set, spans for the
agent run, the model requests and the tool calls reach an exporter at
`<base>/api/public/otel/v1/traces` with the Basic header; with neither
Langfuse keys nor an OTLP endpoint, no exporter is built; the shell tool's
environment holds none of the keys; spans are flushed when the run times
out. A live, full-length audit shows its whole trace in a Langfuse project,
with input, output and usage on its model calls.

## Could invalidate this plan

- PydanticAI 2.57's instrumentation with a plain `TracerProvider` (no
  Logfire) may not emit the GenAI attributes Langfuse reads for input,
  output and token use, so traces arrive as bare spans; then the plan
  needs the Langfuse SDK or extra attributes. Spike: run the agent offline
  with an in-memory exporter and list the span names and `gen_ai.*`
  attributes, then live against a Langfuse project. Settled for the
  emitting side by spike:langfuse-traces/1: with no Logfire, the run gives
  an `invoke_agent` root span, `chat` spans with `gen_ai.request.model`,
  `gen_ai.usage.*` and `gen_ai.input.messages`/`gen_ai.output.messages`,
  and `execute_tool` spans with arguments and result: the gen_ai.* names
  Langfuse's OTel page says it maps. Whether Langfuse shows them as
  input, output and usage is the live check in Done when.
- A real audit's trace may be too big for Langfuse. Each chat span carries
  the conversation so far, so a 30 to 83 request audit sends roughly 11 to
  43 MB of span attributes, with single spans near 1 MB (estimate from the
  session's transcripts). If Langfuse rejects or cuts them, traces vanish
  without failing the run. Spike: replay a full DeepSeek transcript through
  a FunctionModel into a live Langfuse project, then read the trace back
  through Langfuse's API and count its observations, input, output and
  usage; if it fails, find the setting that fixes it.
  Settled by spike:langfuse-traces/2: replaying the 64-request DeepSeek
  okf-vs-code audit with the defaults sent 166 spans (32.66 MB) in one
  request; Langfuse cloud returned 200 and its API gave back all 166, every
  chat span a generation with model, full input (up to 819 kB), output and
  usage. No batch or content setting is needed.
