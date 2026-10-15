---
type: spike
title: Spike ci-audit/2
description: does headless claude -p with --plugin-dir and Read,Grep,Glob-only tools load the kmctl plugin, refuse Bash and Write, dispatch kmctl-auditor and print a parseable findings block?
tags:
- spike
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T12:58:57+00:00'
slug: ci-audit
n: 2
outcome_written: true
---

# Spike ci-audit/2

does headless claude -p with --plugin-dir and Read,Grep,Glob-only tools load the kmctl plugin, refuse Bash and Write, dispatch kmctl-auditor and print a parseable findings block?

The command exited 0:

```
python3 -I /tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-ci-audit/spike.py
```

## Outcome

Exit 0. With `claude -p --plugin-dir PLUGIN --setting-sources project --allowedTools Read,Grep,Glob --disallowedTools Bash,Edit,Write --output-format stream-json --verbose` and the prompt on stdin, the plugin loaded as `kmctl@inline`. It listed agent `kmctl:kmctl-auditor` and skills `kmctl:*`. Bash and Write were missing from the tool list, and bash-ran and write-ran were never created.
The main session dispatched `kmctl:kmctl-auditor` with or without `Agent` in --allowedTools, because Agent is not permission-gated. The subagent used only Read and Glob and returned a fenced json block that json.loads parsed (1 finding, verdict drifted, correct evidence).
Surprise: NotebookEdit, WebFetch, WebSearch, CronCreate, RemoteTrigger, Workflow and the claude.ai MCP tools stayed in the tool list, because --allowedTools does not narrow the tool set. NotebookEdit failed here only because the notebook did not exist. A general-purpose subagent inherited the Bash/Edit/Write removal.
okf did not resolve. No okf skill or plugin was loaded and plugin.json declares no dependency. The audit did not need it.
The plugin's SessionStart hook still ran ("kmctl is not installed").
Limits: run on a dev container with OAuth from CLAUDE_CONFIG_DIR and user settings excluded, not on a clean runner with ANTHROPIC_API_KEY. One fixture page.
Settles risk 1 for loading, dispatch and parsing. The reports-only claim needs the tool set narrowed further (see ci-audit/3).

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-ci-audit/spike.py`, which the command used
