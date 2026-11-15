---
type: plan
title: 'Plan: kmaudit-cli-slim'
description: kmaudit's CLI keeps only mcp, ui, the list commands and briefing; the verbs live on as MCP tools.
tags:
- plan
slug: kmaudit-cli-slim
status: draft
epic: kmaudit
depends_on:
- kmaudit-skills-mcp
priority: 3
schema_version: '2.0'
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T14:31:38+00:00'
---

# kmaudit-cli-slim

Relayed from: none

## Intent

The operator: "The CLI should only give access to the MCP or UI. Perhaps a
couple of list commands to check a database, or something like list
namespaces." Once kmaudit-skills-mcp moves the skills and agents to the MCP
tools, nothing in the repository calls kmaudit's other verbs through the
shell (a search for `kmaudit claims|checks|judge|coverage|guard` outside
kmaudit's own tests and docs finds only those skills and agents).

`packages/kmaudit/src/kmaudit/cli.py` keeps `kmaudit mcp`, `kmaudit ui`,
`kmaudit namespaces`, `kmaudit briefing`, `kmaudit claims list` and
`kmaudit checks list`, and drops `claims todo`, `claims submit`,
`checks todo`, `checks try`, `checks submit`, `checks run`, `judge`,
`coverage` and `guard`. Each dropped verb lives on as an MCP tool or a
Python function (guard has no MCP tool and goes: it held an agent's shell to
kmaudit commands, and the agents no longer have a shell). A dropped verb
typed anyway exits 2 with a line naming the MCP tool that replaced it. The
tests that drive a dropped verb through the CLI move to the MCP tools (the
stdio client `test_mcp.py` already uses) or to the Python functions; the
behaviour they check stays covered. kmaudit's README and
`packages/kmaudit/docs/commands.md`, ADR 0043 and the architecture concepts follow.

Choice carried from the operator's words: `checks run` (rerunning checks
with no model) is reachable only through MCP or Python afterwards, so a CI
job reruns checks through an MCP client or a short Python call, not a shell
verb.

It worked when `kmaudit --help` lists only mcp, ui, namespaces, briefing,
claims list and checks list, a dropped verb names its MCP tool, and every
behaviour the old CLI tests checked is still tested.

## Problems

- P1: kmaudit's CLI duplicates the MCP tools, so two surfaces must be kept correct.

## Goals

- G1: One interface for agents (MCP) and a small CLI for people.

## Outcomes

### O1: The CLI keeps only mcp, ui, namespaces, briefing and the two list commands
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `packages/kmaudit/src/kmaudit/cli.py`, `packages/kmaudit/src/kmaudit/guard.py`, `packages/kmaudit/README.md`, `packages/kmaudit/docs/commands.md`, `packages/kmaudit/tests/*.py`, `.okf/decisions/0043-the-audit-is-its-own-library-kmaudit-served-over-mcp.md`, `.okf/architecture/audit-pipeline.md`
- checked by: a test that `kmaudit --help` lists exactly those commands; a test per dropped verb that it exits 2 naming its MCP tool; the moved tests pass through the MCP tools or the Python functions, with no behaviour test deleted (a count of test functions per behaviour before and after in the build notes); the docs test that every tool and command is documented
- seen by: operator

## Could invalidate this plan

- none
