---
type: plan
title: 'Plan: kmaudit-mcp'
description: kmaudit mcp starts a stdio MCP server whose tools are kmaudit's verbs, so any MCP harness can drive the audit.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T13:41:57+00:00'
slug: kmaudit-mcp
epic: kmaudit
depends_on:
- kmaudit-namespaces
priority: 1
schema_version: '2.0'
---

# kmaudit-mcp

Relayed from: none

## Intent

The operator wants kmaudit's main interface to be an MCP server over stdio,
so any harness that speaks MCP (Claude Code, Codex, Antigravity, a
LangGraph agent) can drive the audit, instead of agents shelling out to a
CLI. Every verb is already a plain function that takes a path and returns a
Pydantic model (`todo`, `submit`, `list_claims` in
`packages/kmaudit/src/kmaudit/verbs.py`; `todo`, `try_answers`, `submit`,
`run`, `list_checks` in `packages/kmaudit/src/kmaudit/check_verbs.py`;
`coverage` in `packages/kmaudit/src/kmaudit/coverage.py`; `judge` in
`packages/kmaudit/src/kmaudit/judge.py`; `listing` in
`packages/kmaudit/src/kmaudit/namespaces.py`), so the server is a thin
layer.

`kmaudit mcp` starts the server, built on the official MCP Python SDK
(`mcp` 2.x, its `MCPServer`), in `new:packages/kmaudit/src/kmaudit/mcp_server.py`.
Its tools mirror the verbs: `namespaces`, `claims_todo`, `claims_submit`,
`claims_list`, `checks_todo`, `checks_try`, `checks_submit`, `checks_run`,
`checks_list`, `coverage` and `judge`. Each takes `folder` (the namespace,
a path relative to the server's working directory, as the CLI's path), and
answers take the agent's answers as structured input, not a heredoc. Each
returns the JSON the CLI's `--json` prints. The todo tools page: they take
`limit` (default 5) and `brief`, which leaves out the instructions and
schema the agent already has; `claims todo` gains the `--brief` that
`checks todo` already has, so a todo result stays well under a harness's
tool result limit. A refusal is an MCP tool error
whose text is the CLI's refusal line, naming the fix. The CLI keeps its
verbs in this ticket; the skills move to the tools and the CLI shrinks in
the next tickets.

kmaudit's README says how to add the server to Claude Code, Codex,
Antigravity and a LangGraph agent, and the docs list each tool.

It worked when an MCP client, started the way a harness starts a stdio
server, lists the tools and runs a claims todo, submit and list round trip
on a fixture repository, with a refusal coming back as a tool error.

## Problems

- P1: Driving kmaudit needs a shell and its CLI, so a harness without a shell tool, or one that prefers MCP, cannot use it.
- P2: Nobody is told how to connect kmaudit to their harness.

## Goals

- G1: Any harness that speaks MCP can drive the audit.

## Outcomes

### O1: kmaudit mcp serves the verbs as MCP tools over stdio
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `new:packages/kmaudit/src/kmaudit/mcp_server.py`, `packages/kmaudit/src/kmaudit/cli.py`, `packages/kmaudit/src/kmaudit/verbs.py`, `packages/kmaudit/pyproject.toml`, `uv.lock`, `new:packages/kmaudit/tests/test_mcp.py`
- checked by: a test that starts `kmaudit mcp` through the SDK's stdio client in a fixture repository, lists the tools, runs claims_todo, claims_submit and claims_list for a namespace, gets a refused submit back as a tool error naming the fix, and that a default claims_todo result on a 200-section folder stays under 25,000 tokens (bytes / 4)
- seen by: operator

### O2: The README tells each harness how to connect, and the docs list the tools
- kind: support
- goal: G1
- fixes: P2
- needs: O1
- touches: `packages/kmaudit/README.md`, `packages/kmaudit/docs/commands.md`
- checked by: a test that every tool the server lists is named in the docs, and the README has a section for Claude Code, Codex, Antigravity and LangGraph
- seen by: operator

## Could invalidate this plan

- The MCP SDK's 2.x dependencies (starlette, uvicorn, opentelemetry-api,
  httpx2) may not resolve beside the root lock, which pins
  opentelemetry-sdk and pydantic-ai-slim for the CI audit, forcing an
  older SDK or a hand-written server.
- A todo result may be too large for one tool result: Claude Code warns
  past about 25,000 tokens, and `claims todo` hands out its instructions
  and up to every pending section at once, so the tools would need paging
  the CLI does not have. spike:kmaudit-mcp/1 measured it: every pending
  section of this repository's `.okf/` is ~277k tokens, `--limit 15` ~41k,
  one section at most ~6.5k, and `checks todo --limit 5 --brief` ~5k. The
  plan now pages: the todo tools default to 5 and take `brief`, and
  `claims todo` gains `--brief`.
