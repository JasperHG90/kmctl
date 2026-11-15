---
type: spike
title: Spike release-notes-hermes/2
description: does the response_file written by the toiminnot hermes action (551e8a6) pass the release-notes checks with default tools and with tools off, and does any rewrite reverse a bullet meaning (shipped work called postponed)?
tags:
- spike
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T19:59:22+00:00'
slug: release-notes-hermes
n: 2
outcome_written: true
---

# Spike release-notes-hermes/2

does the response_file written by the toiminnot hermes action (551e8a6) pass the release-notes checks with default tools and with tools off, and does any rewrite reverse a bullet meaning (shipped work called postponed)?

The command exited 0:

```
bash -ic 'python3 /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-hermes-2/spike2.py "$PWD" /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-hermes-2/toiminnot/actions/hermes/runner'
```

## Outcome

This is the same harness as spike 3, but loopctl cut stdout to its last 20 kB (`truncated: true`), so the A runs' rewrites are missing from the record. Only the B rewrites and the summary survived. The summary showed 15 of 15 kept in A (default tools, 9 runs called tools, none changed the checkout), 15 of 15 kept in B (tools off: `disabled_toolsets` set to all 14 default toolsets, `max_iterations: '3'`, 0 tool calls), and 0 flagged reversal bullets. The surviving B v0.9.0 rewrites kept the "Deferred hardening" bullets word for word. Spike 3 reran with compact output split across stdout and stderr. Cite spike 3, not this one.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike2.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-hermes-2/spike2.py`, which the command used
- `files/checks.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-hermes-2/checks.py`, which the command used
- `files/release-notes-system.md.txt`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-hermes-2/release-notes-system.md`, which the command used
