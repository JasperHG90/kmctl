---
type: plan
title: 'Plan: antigravity-live-check'
description: The operator confirms in a live Antigravity session on an eligible account that kmctl's workspace plugin hook injects the briefing and okf's MCP server starts, and records what the offline spikes could not see.
slug: antigravity-live-check
epic: multi-harness
depends_on:
- antigravity-harness
status: draft
tags:
- plan
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261016
  at: '2026-10-16T20:24:05+00:00'
---

# antigravity-live-check

Relayed from: antigravity-harness, plan review round 1 finding p2 (the hook
firing and the MCP server starting need a live session).

## Intent

agy 1.4.0 on this machine refuses sessions ("Eligibility check failed"), so
spike:antigravity-harness/3 and spike:antigravity-harness/4 showed only that
Antigravity discovers the workspace plugin, loads its agent and registers
its hook. In a repository set up with `kmctl plugin install --harness
antigravity`, trusted in Antigravity, on an eligible account, the operator
starts a session and checks: the first turn carries the kmctl briefing (the
hook fired and its JSON was injected); okf's `search_concepts` tool answers
(the MCP server started and found `.okf/`); the kmctl-auditor agent can be
invoked. Each outcome is recorded; a failure becomes a ticket.

## Could invalidate this plan

none
