---
type: verdict
title: 'Verdict: langfuse-traces reviewer round 1'
description: 'reviewer verdict for round 1 of langfuse-traces: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T18:38:58+00:00'
slug: langfuse-traces
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. Tracing is off without the variables and
imports no OpenTelemetry SDK or exporter then; with Langfuse keys it sends
OTLP/HTTP to the base URL plus /api/public/otel/v1/traces with the Basic
header; with only an OTLP endpoint it uses the standard variables. The
provider shuts down in a finally on every exit of the agent run, and the
keys cannot reach run_shell because its environment is an allowlist. The
tests are real. One misplaced test comment, which does not block.

## Checked

- Gates, re-run by me with `loopctl gate stamp` from the worktree: lint,
  format, tests, integration, and rows r1, r2 and r3 all pass; "stamp green:
  12895a1eb3eec8ddd393c770d9db8d9a877cb45f6a498f1f1a9b7ebdcefb6c99".
- run(): `tracer_provider()` is called after all the usage checks, and the
  try/finally around `asyncio.run` shuts the provider down on success, on
  TimeoutError, on UnexpectedModelBehavior and on any other exception.
  Nothing between creating the provider and the try can raise.
- run_shell builds its env only from SHELL_ENV_KEEP (PATH, HOME, LANG,
  LC_ALL, TERM, TMPDIR, USER), so no LANGFUSE_* or OTEL_* variable gets in.
  test_traces_safe_keys_stay_out_of_the_shell runs `env` through the real
  tool and asserts that none of them appear.
- A failed export does not fail the run. I ran the agent with
  LANGFUSE_BASE_URL set to a closed port (rc 0, 6.9 s) and to an address that
  does not route (rc 0, 10.1 s), using a script in the scratchpad. Shutdown
  is bounded by the exporter's timeout.
- r1: the test starts a local OTLP/HTTP receiver that decodes the protobuf
  ExportTraceServiceRequest. It asserts the path, the exact Basic header for
  pk-lf-1:sk-lf-2, and the invoke_agent, chat and "execute_tool read_file"
  spans. The default base URL is checked on the built exporter. A wrong
  path, header or span set would fail it.
- r2: a subprocess loads the script under the dev venv (where the SDK is
  installed) with the variables removed. It asserts that tracer_provider()
  returns None and that no opentelemetry.sdk or opentelemetry.exporter
  module was imported. The endpoint-only test asserts the request reaches
  /v1/traces with no Authorization header.
- r3: the timeout test stalls the model for 30 s under --timeout 1 and
  asserts that the receiver got an invoke_agent span, which only happens if
  the flush on that path works.
- r4 (judgment): I accept the live evidence. Trace
  3df9d9d5b04f070e6bab8286dda11921 has 1 AGENT, 31 GENERATION and 66 TOOL
  observations, which matches the transcript's 31 requests and 68 tool
  calls (66 plus the 2 final_result calls PydanticAI does not trace as
  tools). All 31 generations have input, output and usageDetails. Spike 2
  covers the 64-request size case. The how-to tells you to put the two keys
  in the audit step's env, names LANGFUSE_BASE_URL and the OTEL_*
  alternative, and warns that a trace holds the file contents the agent
  read.
- Pins: the PEP 723 block and the pyproject dev group both pin
  opentelemetry-sdk and opentelemetry-exporter-otlp-proto-http to 1.45.1,
  and uv.lock resolves 1.45.1.
- Docs: the ADR 0017 correction, the log line and the overview edge match
  the code. cloud.langfuse.com is Langfuse's EU region, so "default
  Langfuse's EU cloud" is correct, and the docstrings of tracer_provider and
  run_agent match the code.

## Findings

- f1 (nit, not blocking): in tests/test_agent.py, TRACE_VARS sits between
  the `#: Cites only README.md...` comment and REPORT, so the comment now
  documents the wrong constant. Move TRACE_VARS above the comment.
