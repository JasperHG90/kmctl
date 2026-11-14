---
type: plan
title: 'Plan: kmaudit-skills-mcp'
description: The extract-claims and write-checks skills and their agents call kmaudit's MCP tools instead of its CLI.
tags:
- plan
slug: kmaudit-skills-mcp
status: draft
epic: kmaudit
depends_on:
- kmaudit-mcp
priority: 2
schema_version: '2.0'
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T14:31:36+00:00'
---

# kmaudit-skills-mcp

Relayed from: none

## Intent

The operator: "The skills that we currently have stay, but they should
point at the MCP." Once kmaudit-mcp lands, `apm/.apm/skills/extract-claims/SKILL.md`,
`apm/.apm/skills/write-checks/SKILL.md` and the agents
`apm/.apm/agents/kmctl-claims-extractor.md` and
`apm/.apm/agents/kmctl-check-writer.md` call the MCP tools (claims_todo,
claims_submit, checks_todo, checks_try, checks_submit) with structured
answers instead of shell heredocs. The agents then need no shell, so their
`tools` become Read, Grep, Glob and the kmaudit MCP tools, and the
`kmaudit guard` hook goes. kmctl's APM package declares the kmaudit MCP
server for each harness the way it declares okf's, and `kmctl plugin
patch` carries it into Antigravity and OpenCode. To be planned once the
tool names and shapes exist.

## Problems

- P1: The skills and agents drive kmaudit through a shell, which needs a per-harness guard hook and heredoc quoting.

## Goals

- G1: The skills drive kmaudit through MCP in every harness kmctl supports.

## Outcomes

### O1: The skills and agents call kmaudit's MCP tools
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `apm/.apm/skills/extract-claims/SKILL.md`, `apm/.apm/skills/write-checks/SKILL.md`, `apm/.apm/agents/kmctl-claims-extractor.md`, `apm/.apm/agents/kmctl-check-writer.md`
- checked by: to be written when planned
- seen by: operator

## Could invalidate this plan

- Subagents in some harnesses may not see a session's MCP tools, so an
  agent could not reach kmaudit without a shell; to be spiked per harness.
