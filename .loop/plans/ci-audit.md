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

Adds a `mode: audit` input to `action.yml`. It needs an Anthropic API key secret. The action's script runs `kmctl review due --json` itself, then runs headless Claude Code (`claude -p`) with the plugin from the action's own checkout (`--plugin-dir`) and a prompt that hands the due list to the `kmctl-auditor` agent from audit-agent-and-skills. It parses the agent's findings block (the shape that ticket defines), writes them to the job summary, and opens or updates one issue titled "Knowledge audit". Without the input the action behaves as before.

Reports only (I2):

- the run allows only `Read`, `Grep` and `Glob` (`--allowedTools`) and refuses `Bash`, `Edit` and `Write` (`--disallowedTools`), the same tools the agent itself has, so neither the agent nor the session around it can run kmctl's write verbs or edit a file;
- the script refuses to run in audit mode unless `GITHUB_EVENT_NAME` is `workflow_dispatch` or `schedule`, so code from a fork never reaches a model that holds the key;
- the example workflow it ships sets `permissions: contents: read, issues: write`. A composite action cannot set token permissions, so the caller's workflow does, and the docs say so.

Done when a test runs the script's audit path on a fixture repository with a stub `claude` that prints a findings block, and the summary and the issue body hold the findings; a test shows the script refuses a `pull_request` event; and a spike shows that in `-p` mode with those flags a request to run Bash or to write a file is refused.

## Could invalidate this plan

- Headless Claude Code on a clean runner may not load the plugin from `--plugin-dir`, resolve okf, run the audit agent with only those tools, and print findings a script can parse. Spike it in a clean container before building.
