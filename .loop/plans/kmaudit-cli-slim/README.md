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
namespaces." Once the skills use the MCP tools, `packages/kmaudit/src/kmaudit/cli.py`
drops claims todo/submit, checks todo/try/submit/run, judge, coverage and
guard, keeping `kmaudit mcp`, `kmaudit ui`, `kmaudit namespaces`, `kmaudit
briefing` and read-only list commands (claims list, checks list). Tests
that drive the dropped verbs move to the MCP tools or the Python
functions. kmaudit's README and docs follow. To be planned once the skills
no longer call the CLI.

## Problems

- P1: kmaudit's CLI duplicates the MCP tools, so two surfaces must be kept correct.

## Goals

- G1: One interface for agents (MCP) and a small CLI for people.

## Outcomes

### O1: The CLI keeps only mcp, ui, namespaces, briefing and the list commands
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `packages/kmaudit/src/kmaudit/cli.py`, `packages/kmaudit/docs/commands.md`
- checked by: to be written when planned
- seen by: operator

## Could invalidate this plan

- none
