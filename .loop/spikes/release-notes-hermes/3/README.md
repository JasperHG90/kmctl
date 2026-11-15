---
type: spike
title: Spike release-notes-hermes/3
description: does the response_file written by the toiminnot hermes action (551e8a6) pass the release-notes checks with default tools and with tools off, and does any rewrite reverse a bullet meaning (shipped work called postponed)?
tags:
- spike
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T19:59:21+00:00'
slug: release-notes-hermes
n: 3
outcome_written: true
---

# Spike release-notes-hermes/3

does the response_file written by the toiminnot hermes action (551e8a6) pass the release-notes checks with default tools and with tools off, and does any rewrite reverse a bullet meaning (shipped work called postponed)?

The command exited 0:

```
bash -ic 'python3 /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-hermes-2/spike2.py "$PWD" /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-hermes-2/toiminnot/actions/hermes/runner'
```

## Outcome

Ran the action's own runner (toiminnot `actions/hermes` at 551e8a6, `python -m hermes_runner`, the env vars `action.yaml` sets) against Bifrost (`base_url` = `$BIFROST_URL`, virtual key as `api_key`, sent as a Bearer token, model `ollama/deepseek-v4.1-flash`), each run in a fresh clone of the repo, with the revised prompt (`files/release-notes-system.md.txt`). The response file passed spike 1's checks on 15 of 15 runs in (A), default tools with `max_iterations: '40'`, and 15 of 15 in (B), `disabled_toolsets: 'browser,clarify,code_execution,delegation,file,memory,project,session_search,skills,terminal,todo,tts,web,vision'` with `max_iterations: '3'`. In B the agent got 0 tools and made 0 tool calls. In A, 10 of 15 runs called tools (`terminal` for git log/show, `search_files`, `read_file`), none changed the checkout, and every run still replied with the notes.
No run said shipped work was postponed, deferred or planned. All 6 v0.9.0 rewrites kept the three "Deferred hardening ... reviewer finding" bullets word for word. The regex flagged one A bullet ("a choice ... not yet accepted"), which describes draft status correctly. On reading every bullet, B changed one bullet's sense: v0.12.1 run 2 turned "Check a decision index entry against the record's corrected title" into "entries now show the corrected title". One more B line is borderline (v0.12.0 run 2: "says which release it is pinned to"). A added details from the commits that the draft lacks (for example "`kmctl summary ack` drops deleted concepts"), and the checks cannot verify those.
This settles risk 1 for both configurations: the agent wrapper does not make the checks fall back. On meaning, the revised prompt removes the postponed reversal in this sample (0 in 30), but the checks still pass an occasional reworded sense (1 in 15 runs in B), so a reviewer is still needed. Spike 2 is the same run with its stdout cut at 20 kB. Its summary also showed 15/15 for A and 15/15 for B with 0 flags. Limits: 5 drafts, 3 runs per configuration, run locally and not on a GitHub runner.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike2.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-hermes-2/spike2.py`, which the command used
- `files/checks.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-hermes-2/checks.py`, which the command used
- `files/release-notes-system.md.txt`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-hermes-2/release-notes-system.md`, which the command used
