---
type: spike
title: Spike audit-any-provider/2
description: does hermes -z run unattended in CI with a fresh HOME and take provider, model and base URL from flags and env, or from a script-written config, and print a parseable json block
tags:
- spike
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T14:32:18+00:00'
slug: audit-any-provider
n: 2
outcome_written: true
---

# Spike audit-any-provider/2

does hermes -z run unattended in CI with a fresh HOME and take provider, model and base URL from flags and env, or from a script-written config, and print a parseable json block

The command exited 0:

```
python3 -I /tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-hermes/spike2_unattended.py
```

## Outcome

With a fresh HOME, stdin closed and no TTY, `hermes -z PROMPT --provider custom -m MODEL -t TOOLSETS` plus `CUSTOM_BASE_URL=<url>` ran in about 1 s and exited 0. It showed no wizard or prompt, used streaming, and needed no config.yaml. A script-written `~/.hermes/config.yaml` (`model: {provider: custom, base_url, default, api_key: ${ENV_VAR}}`) also worked and sent the env key as Bearer.
Flags and env alone cannot set an API key for an arbitrary host. Hermes sends `no-key-required` for loopback, or reads a `<VENDOR>_API_KEY` derived from the host name, so a real CI key needs the config file.
stdout is the final answer text: the fenced json block parsed. When a write tool was attempted, Hermes appended a "File-mutation verifier" footer after the block, so the parser should pull out the fenced block rather than take the whole of stdout.
Under `-z`, `--ignore-user-config` and `--ignore-rules` do nothing: AGENTS.md from cwd was still injected. Hermes loads one context file, the first found of .hermes.md, AGENTS.md, CLAUDE.md, .cursorrules. If the endpoint reports under 64K context, Hermes exits 1 with a clear stderr message. It probed /api/v1/models, /api/show and /v1/models/MODEL, and ran fine when none of them answered.
This settles risk 2. Ran against a fake endpoint only.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike2_unattended.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-hermes/spike2_unattended.py`, which the command used
- `files/drive.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-hermes/drive.py`, which the command used
- `files/fake_llm.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-hermes/fake_llm.py`, which the command used
