---
type: plan
title: 'Plan: audit-agent-and-skills'
description: "An audit agent with three review skills (architecture, decision log, practices) that report findings and never write knowledge (ADR 0005, I2)."
slug: audit-agent-and-skills
epic: plugin
depends_on: [claude-plugin, review-due]
priority: 8
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T05:10:22+00:00'
---

# audit-agent-and-skills

Relayed from: none

## Intent

Adds an audit agent and three skills to the plugin:

- `architecture-review`: does each `.okf/architecture/` page still match the code;
- `decision-log-review`: does each decision still hold, or has a later decision or the code overtaken it;
- `practices-review`: does each practice still have the count or code site it cites.

The agent starts from `kmctl review due --json`, so it reads only what is due, plus anything the user names. It returns findings as data and has no write tools (I2).

Done when the agent run on this repository reports findings, its tool list has no write tool, and a test fails if one is added.

## Could invalidate this plan

- An audit may find little or a lot of false drift. Before tuning the skills, run the architecture review once on loop-harness, whose bundle is larger, and count real and false findings.
