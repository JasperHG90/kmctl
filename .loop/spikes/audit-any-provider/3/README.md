---
type: spike
title: Spike audit-any-provider/3
description: does the real knowledge-audit.sh with real Hermes 0.19.0 against a fake OpenAI-compatible endpoint offer only the three kmctl read tools, refuse a requested write and get the findings into the summary
tags:
- spike
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T15:10:34+00:00'
slug: audit-any-provider
n: 3
outcome_written: true
---

# Spike audit-any-provider/3

does the real knowledge-audit.sh with real Hermes 0.19.0 against a fake OpenAI-compatible endpoint offer only the three kmctl read tools, refuse a requested write and get the findings into the summary

The command exited 0:

```
python3 -I /tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-hermes/spike3_real_script.py
```

## Outcome

The worktree's real `action/knowledge-audit.sh` ran real Hermes Agent 0.19.0 against a fake OpenAI-compatible endpoint, on a fixture repository with one due architecture page, and exited 0 in about 6 s. The child environment was built in Python: a scratch HOME, no inherited keys or tokens.
In both requests that carried tools, the model was offered exactly `kmctl_list_files`, `kmctl_read_file` and `kmctl_search_files`. Its requested `write_file`, `patch`, `terminal` and `execute_code` calls each got "Tool 'X' does not exist", the target file kept its text and `git status` stayed clean. A read and a search of `/proc/self/environ` through the kmctl tools were refused as outside the repository, and the key did not come back. The key reached the endpoint as Bearer from the variable the caller named.
The model's findings block reached the job summary as a table row, and `knowledge-audit-issue.sh` with a stub gh posted the same body as a new "Knowledge audit" issue.
A first run found one bug, fixed in the build before this run: Hermes 0.19.0 turns a dict result from a plugin tool into a contract error, so the plugin now returns its refusals as JSON text, and a test checks every result is a string.
This settles r8 for a fake endpoint only; no real model was called.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike3_real_script.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-hermes/spike3_real_script.py`, which the command used
- `files/fake_llm_r8.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-hermes/fake_llm_r8.py`, which the command used
