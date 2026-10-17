---
type: verdict
title: 'Verdict: langfuse-traces plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of langfuse-traces: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T18:16:43+00:00'
slug: langfuse-traces
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The listed risk is settled on the emitting side. spike:langfuse-traces/1
shows that PydanticAI 2.57 with a plain TracerProvider and the Instrumentation
capability emits the gen_ai.* attributes Langfuse maps, never imports
logfire, builds the Langfuse exporter with the Basic header, and flushes on
shutdown. The plan correctly leaves the Langfuse-side mapping to the live
check.

One unlisted risk could break the plan: real audits produce traces of tens
of megabytes, because each chat span carries the full message history. We do
not know whether Langfuse accepts traces that large, and failed exports are
silent by design. This needs a spike or a live check against a full-length
audit before building. It may only need a config change, so it is a revision,
not a rethink.

## Checked

- Spike 1: README outcome, stdout.txt (span names and attributes, the
  checks, the exporter endpoint and header, the flush test), run.json (exit 0),
  and files/spike.py. The evidence answers the emitting-side risk as the plan
  says.
- action/agent.py: `SHELL_ENV_KEEP` (line 71) is an allowlist, so Langfuse
  keys and OTEL_* headers never reach `run_shell` (line 376). `refuse_tokens`
  (line 490) is unaffected. `run_agent` wraps `agent.run` in
  `asyncio.wait_for` (line 625). `run` catches TimeoutError and
  UnexpectedModelBehavior around `asyncio.run` (line 680), so a `finally` that
  shuts down the provider there covers the timeout path. On timeout,
  cancellation ends the open spans through their context managers before
  `asyncio.run` returns. The SDK's TracerProvider also registers an atexit
  shutdown.
- action.yml: the audit step's `env` lists only its own variables. The
  caller's step env reaches the composite step, which is how the model key
  arrives today, so the claim that no new input is needed holds.
- Payload size: I replayed the five real transcripts in the session
  scratchpad (live-audit, live-run, ollama-plants/*) and summed the
  per-request history each chat span would carry. That gave 16 MB, 38 MB,
  43 MB, 38 MB and 11 MB per run. This is an estimate from the message JSON,
  not an OTLP measurement.

## Findings

- p1: trace size. Spike question: "Built from a real transcript (for example
  scratchpad/ollama-plants/out-okf-vs-code/transcript.json, replayed through
  a FunctionModel so the spans match a real audit), do all spans of a
  full-length audit reach a Langfuse project through OTLPSpanExporter with
  the default BatchSpanProcessor, and does Langfuse show input, output and
  usage for the largest chat spans? If not, which setting makes it work
  (max_export_batch_size, include_content=False, or dropping the cumulative
  attributes)?" At the least, Done when should require the live check to be
  a full-length audit, not a short prompt.

## Notes

Risks the caller raised that I judged not to break the plan:

- Key security: the Langfuse secret key gets the same protection as the
  model key. It stays out of the shell env, but a command could still read
  it from /proc. ADR 0017 already accepts that leftover risk, and the plan
  corrects the ADR.
- Repo content sent to Langfuse: the plan makes tracing opt-in and has the
  how-to warn that traces hold what the agent read. That is an operator
  choice, already documented.
- Flushing on timeout: covered above.
- An unreachable endpoint: the OTLP HTTP exporter times out each export and
  logs errors without raising, so it adds a bounded delay at shutdown and
  does not fail the run. Building it will show the exact delay.
- PEP 723 weight: the new pinned dependencies (sdk, otlp-proto-http,
  protobuf, requests) install on every `uv run --script`, including
  `publish`, even though they are imported only when tracing is on. They
  are wheels and are never imported there, so they slow installs but do not
  break the plan.

The ticket is small enough. It does not need splitting.
