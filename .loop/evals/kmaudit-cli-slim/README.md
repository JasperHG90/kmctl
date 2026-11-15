---
type: eval
title: 'Eval: kmaudit-cli-slim'
description: 'Definition of done for kmaudit-cli-slim: 4 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-15T06:41:26+00:00'
slug: kmaudit-cli-slim
signoff:
  signer: delegated:jasperginn@gmail.com/implementer
  hash: 79018a77b126b90b7c2e98b4980ba0dff32c72bad5aaceff45416690243a5b2d
  at: '2026-11-15T06:41:26+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmaudit --help lists exactly mcp, ui, namespaces, briefing, claims (with only list) and checks (with only list); each dropped verb (claims todo/submit, checks todo/try/submit/run, judge, coverage, guard) exits 2 with a line naming the MCP tool that replaced it, or saying guard is gone.
  Fails when: a dropped verb still runs, exits other than 2, or names no replacement, or a kept command is missing
- r2: The UI shows a Rerun stale checks button, and POST /api/rerun reruns the stale checks of the namespace on screen through the same function the MCP checks_run tool calls, returning the run's result.
  Fails when: the button is missing, the endpoint is missing, or it does not rerun a stale check
- r3: No string in kmaudit's source, its MCP server's instructions and tool descriptions, its answer schema or ui.html names a dropped verb as a command to run, and ADR 0043 says the guard hook is gone.
  Fails when: any such string names kmaudit claims todo/submit, checks todo/try/submit/run, judge, coverage or guard as a command, or ADR 0043 still describes the guard hook as current
- r4: Every kmaudit test passes with the slim CLI: behaviours that did not leave with the CLI are tested through the MCP tools or the Python functions, and the docs list every tool and kept command.
  Fails when: any kmaudit test fails
