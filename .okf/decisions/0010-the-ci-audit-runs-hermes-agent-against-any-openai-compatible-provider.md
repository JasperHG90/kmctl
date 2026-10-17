---
type: decision
title: "ADR 0010: The CI audit runs Hermes Agent against any OpenAI-compatible provider"
description: "The CI audit runs Hermes Agent with a read-only kmctl plugin against any OpenAI-compatible model endpoint, replacing the Claude Code runner, so the audit ties no repository to one model vendor."
tags: [adr, decision, ci, audit]
generated:
  by: claude-opus/5.5
  at: 2026-10-15
status: deprecated
---

# ADR 0010: The CI audit runs Hermes Agent against any OpenAI-compatible provider

- Status: Accepted
- Date: 2026-10-15

## Context

The action's audit mode, added with
[ADR 0005](0005-audits-report-only.md)'s two tiers, ran headless Claude Code
(`claude -p`) and needed an Anthropic API key. That tied every repository
that turns the audit on to one model vendor. The operator asked for the audit
to take any provider: Ollama, OpenAI, Bifrost, OpenRouter and others.

[Hermes Agent](https://hermes-agent.nousresearch.com) runs unattended with
`hermes -z` and talks to any OpenAI-compatible endpoint. It has no read-only
toolset of its own: its `file` toolset includes `write_file` and `patch`, and
with no `-t` it offers a terminal and code execution, all approved without a
prompt under `-z`. Its own read and search handlers read any file the runner
can, and its search passes the pattern to `rg` with no `--`, so a pattern
such as `--pre=rm` runs a command.

## Decision

- The audit runs Hermes Agent, pinned to 0.19.0, with provider `custom` and a
  base URL by default, so one setting covers any OpenAI-compatible server.
  Hermes' own provider names also pass through.
- `action/knowledge-audit.sh` writes the Hermes config into a fresh HOME for
  the run. The config names the variable that holds the key, never the key.
- The model gets only `kmctl_read_file`, `kmctl_search_files` and
  `kmctl_list_files`, from kmctl's own Hermes plugin in
  `action/hermes/kmctl-read/`, offered with `-t kmctl_read`. They are plain
  Python, start no program, refuse every path that resolves outside the
  repository, and match plain text, never a regex. Read-only (I2) holds
  because of them.
- `timeout` around hermes and `timeout-minutes` on the step bound the run.
- The shipped workflow spells out each command as its own step instead of
  `uses: ./`, so a reader sees all of it.

Rejected:

- Keep Claude Code. It needs an Anthropic key, which is the tie the operator
  wanted gone.
- Use Hermes' built-in `file` toolset with `HERMES_WRITE_SAFE_ROOT`. It still
  offers the write tools, and its read and search reach outside the
  repository, including `/proc/PID/environ`, where the API key is.
- Wrap Hermes' own read and search handlers in the plugin. Their search runs
  `rg` with the pattern as a bare argument, so a pattern can become a flag.

## Consequences

- This replaces the Claude Code runner described in ADR 0005's Consequences.
  ADR 0005's report-only rule and its two tiers stand.
- The action's audit inputs are `provider`, `model`, `base_url` and
  `api_key_env`; `anthropic_api_key` is gone.
- The model sees only the audited repository, and with it anything the
  repository holds, secrets checked into it included.
- One Hermes session audits every batch in turn, since Hermes has no
  subagent for the auditor. The prompt carries the audit skill, the review
  skills the due list needs and the kmctl-auditor instructions as text.
- A Hermes upgrade changes the pinned version and reruns the spike that runs
  the real script against a fake endpoint.
- Hermes refuses an endpoint that reports less than 64K of context, and
  Ollama serves a smaller context than the model reports unless `num_ctx` is
  set.

## Correction, 2026-10-17

Superseded by [ADR 0017](0017-the-ci-audit-is-a-standalone-pydanticai-agent-script.md).
