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

Rerunning checks, the operator's choice: `checks run` leaves the CLI, and
the UI gains a "Rerun stale checks" button. The UI server gets a
`POST /api/rerun` endpoint that calls the same Python function the MCP
`checks_run` tool calls, for the namespace on screen, and the page refreshes
its data from the result. A person reruns from the UI; an agent through
`checks_run`; a CI job through an MCP client or a short Python call.

Every message that names a dropped verb changes in the same change, so no
hint sends a person to a command that exits 2: the refusals and `next`
lines in `verbs.py`, `check_verbs.py`, `judge.py`, `sections.py` and
`coverage.py`; the MCP server's instructions and tool descriptions in
`mcp_server.py` ("as `kmaudit ... --json`" becomes the tool's own terms);
the answer schema's field descriptions in `models.py` and `check_store.py`,
which the todo tools hand to agents; the docstrings that name a dropped verb
anywhere in kmaudit's source; the
instructions handed to agents in `instructions.py` and
`check_instructions.py` (they name the MCP tools instead); and the UI's
text in `ui.html` and `ui.py` ("Run kmaudit checks run" becomes the button,
"Run kmaudit claims todo" names /extract-claims, "see kmaudit judge --help"
goes). A test fails when any string in kmaudit's source or UI names a
dropped verb as a command to run.

Some behaviours exist only on the CLI and leave with it, so their tests go
rather than move: reading answers from a file or stdin, the counts printed
for people by `claims todo`, the `--help` walk over the dropped verbs, the
exit codes of `checks run`, the one-line refusal outside a git repository
for the dropped verbs, and the CLI-against-MCP comparisons in
`test_mcp.py` (the MCP side keeps its own tests). Every other behaviour the
old CLI tests checked is kept, through the MCP tools or the Python
functions; the build lists each deleted test with the behaviour it covered.

It worked when `kmaudit --help` lists only mcp, ui, namespaces, briefing,
claims list and checks list, a dropped verb names its MCP tool, the UI's
button reruns stale checks, no message names a dropped verb, and every
behaviour that did not leave with the CLI is still tested.

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
- touches: `packages/kmaudit/src/kmaudit/*.py`, `packages/kmaudit/src/kmaudit/ui.html`, `.okf/manifesto.md`, `.okf/architecture/overview.md`, `packages/kmaudit/README.md`, `packages/kmaudit/docs/commands.md`, `packages/kmaudit/tests/*.py`, `.okf/decisions/0043-the-audit-is-its-own-library-kmaudit-served-over-mcp.md`, `.okf/architecture/audit-pipeline.md`
- checked by: a test that `kmaudit --help` lists exactly those commands; a test per dropped verb that it exits 2 naming its MCP tool; a UI test that POST /api/rerun reruns a stale check and the page shows the button; a test that no string in kmaudit's source or ui.html names a dropped verb as a command; the moved tests pass through the MCP tools or the Python functions, and the build notes list each deleted test with the CLI-only behaviour it covered; the docs test that every tool and command is documented
- seen by: operator

## Could invalidate this plan

- none
