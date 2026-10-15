---
type: spike
title: Spike audit-any-provider/1
description: can Hermes Agent 0.19 offer file read and search to the model without write_file, patch or terminal, and refuse writes the model asks for
tags:
- spike
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T14:32:17+00:00'
slug: audit-any-provider
n: 1
outcome_written: true
---

# Spike audit-any-provider/1

can Hermes Agent 0.19 offer file read and search to the model without write_file, patch or terminal, and refuse writes the model asks for

The command exited 0:

```
python3 -I /tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-hermes/spike1_readonly.py
```

## Outcome

Hermes Agent 0.19.0 has no built-in read-only toolset: `-t file` offers `patch, read_file, search_files, write_file`, and the fake model's `write_file` overwrote the target. With no `-t`, 16 tools are offered, including terminal and execute_code, and `-z` auto-approves them (execute_code wrote the target).
A read-only setup does work: a small user plugin (`~/.hermes/plugins/kmctl-read/`, enabled by `plugins: {enabled: [kmctl-read]}` in config.yaml) that registers toolset `kmctl_read` with only `kmctl_read_file` and `kmctl_search_files`. With `-t kmctl_read` those two were the only tools offered. Calls to write_file, patch, terminal and execute_code got "Tool 'X' does not exist", the target stayed unchanged, and the read returned the fixture. If the plugin is not enabled, `-t kmctl_read` exits 2 before calling the model, so it fails closed.
`HERMES_WRITE_SAFE_ROOT=<empty dir>` with `-t file` also refused write_file and patch, but it still offers them, and Hermes calls it defense-in-depth.
This settles risk 1 only if the plan ships the Hermes plugin. Bare `-t file` would break I2. Ran against a fake endpoint, not a real model.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike1_readonly.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-hermes/spike1_readonly.py`, which the command used
- `files/drive.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-hermes/drive.py`, which the command used
- `files/fake_llm.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-hermes/fake_llm.py`, which the command used
- `files/__init__.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-hermes/plugin/__init__.py`, which the command used
- `files/plugin.yaml`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-hermes/plugin/plugin.yaml`, which the command used
