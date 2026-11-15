---
type: spike
title: Spike kmaudit-namespaces/2
description: a plain folder hits no .okf assumption outside the widened touches (ui.html and check_instructions.py added)
tags:
- spike
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T13:07:47+00:00'
slug: kmaudit-namespaces
n: 2
outcome_written: true
---

# Spike kmaudit-namespaces/2

a plain folder hits no .okf assumption outside the widened touches (ui.html and check_instructions.py added)

The command exited 0:

```
uv run --project /home/vscode/workspace python /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-ns/plain_folder_widened.py
```

## Outcome

Reran spike 1's script with ui.html and check_instructions.py counted as touched. Exit 0: every wrong result it finds (SKIP_NAMES on a plain folder's index.md, Repository reading and counting the audited folder as code in checks, coverage and the page, the page's .okf/ path, the check instructions' folder list) sits in the plan's touched files; none outside. Settles risk 1 for the widened plan. Limit: the fixture repository, with the folder as docs/ and handbook/.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
