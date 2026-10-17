---
type: eval
title: 'Eval: langfuse-traces'
description: 'Definition of done for langfuse-traces: 4 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.2.1.dev10+g138a8c2ed.d20261017
  at: '2026-10-17T18:24:00+00:00'
slug: langfuse-traces
signoff:
  signer: delegated:jasperginn@gmail.com/claude
  hash: 2fcd5e4cb910e62c9707cd1669f98ee3b467a7c3d3e51a54a284ba273937d9d8
  at: '2026-10-17T18:24:00+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: With LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY set, a run sends spans for the agent run, each model request and each tool call to LANGFUSE_BASE_URL (default https://cloud.langfuse.com) plus /api/public/otel/v1/traces, with the header Authorization: Basic base64(public:secret).
  Fails when: no spans are exported, the endpoint or header is wrong, or the model-request or tool-call spans are missing
- r2: Tracing is optional: with no Langfuse keys and no OTEL_EXPORTER_OTLP_ENDPOINT or OTEL_EXPORTER_OTLP_TRACES_ENDPOINT, no exporter is built and OpenTelemetry is not imported; with only an OTLP endpoint set, spans go to that endpoint.
  Fails when: a run without the variables builds an exporter or imports opentelemetry, or a run with only the OTLP endpoint sends nothing
- r3: The shell tool's environment holds none of the Langfuse keys or OTLP headers, and spans are flushed when the run times out or fails.
  Fails when: a Langfuse or OTEL variable reaches run_shell's environment, or spans of a timed-out run are never exported
- r4 (judgment): A live, full-length audit run with Langfuse keys shows its whole trace in a Langfuse project, with input, output and usage on its model calls; the how-to's section 5 says how to turn tracing on and that traces hold what the agent read, and ADR 0017 has a correction.
  Fails when: the live trace is missing spans or the generations lack input, output or usage, or the docs leave out how to turn it on or what it sends
