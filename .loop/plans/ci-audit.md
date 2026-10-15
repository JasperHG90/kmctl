---
type: plan
title: 'Plan: ci-audit'
description: "The GitHub Action gains an opt-in audit mode that runs the audit agent through Claude Code in CI and reports its findings, never pushing (ADR 0005, I2)."
slug: ci-audit
epic: ci
depends_on: [ci-action, audit-agent-and-skills]
priority: 11
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T08:07:39+00:00'
---

# ci-audit

Relayed from: none

## Intent

Adds a `mode: audit` input to `action.yml`. It needs an Anthropic API key secret and runs the audit agent through headless Claude Code (`claude -p`) with the plugin loaded from the action's own checkout (`--plugin-dir`), so it needs no install verb. The agent returns its findings as the JSON the audit-agent ticket defines, and the action writes them to the job summary and opens or updates one issue titled "Knowledge audit". Without the input the action behaves as before.

Reports only (I2):

- the allowed tools are Read, Grep, Glob and Bash limited to `kmctl` and `git log`, so no edit or write tool is available;
- it runs only on `workflow_dispatch` and `schedule`, never on `pull_request` or `pull_request_target`, so code from a fork never reaches a model that holds the key;
- the example workflow it ships sets `permissions: contents: read, issues: write`. A composite action cannot set token permissions, so the caller's workflow does, and the docs say so.

Done when a test run on a fixture repository writes findings to the summary and the issue, and a test shows a write attempt by the agent is refused.

## Could invalidate this plan

- Headless Claude Code on a clean runner may not load the plugin from `--plugin-dir`, resolve okf, run the audit agent with only those tools, and print findings a script can parse. Spike it in a clean container before building.
