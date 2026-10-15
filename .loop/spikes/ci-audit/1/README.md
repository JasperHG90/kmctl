---
type: spike
title: Spike ci-audit/1
description: does headless claude -p with --plugin-dir and Read,Grep,Glob-only tools load the kmctl plugin, refuse Bash and Write, dispatch kmctl-auditor and print a parseable findings block?
tags:
- spike
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T12:56:36+00:00'
slug: ci-audit
n: 1
outcome_written: true
---

# Spike ci-audit/1

does headless claude -p with --plugin-dir and Read,Grep,Glob-only tools load the kmctl plugin, refuse Bash and Write, dispatch kmctl-auditor and print a parseable findings block?

The command exited 1:

```
python3 -I /tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-ci-audit/spike.py
```

## Outcome

Invalid run: every `claude -p` call exited 1 with "Input must be provided either through stdin or as a prompt argument", because `--allowedTools <tools...>` (and `--disallowedTools`) take any number of values and swallowed the trailing prompt.
No model was reached, so this run shows nothing about tool refusal, plugin loading or the auditor; the absent bash-ran/write-ran files mean nothing.
Lesson for the action script: pass the prompt on stdin (or before the variadic flags), not as the last argument. Superseded by ci-audit/2.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-ci-audit/spike.py`, which the command used
