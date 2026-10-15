---
type: spike
title: Spike ci-audit/3
description: does claude -p --tools Read,Grep,Glob,Agent remove NotebookEdit and other non-read tools while kmctl:kmctl-auditor still returns parseable findings?
tags:
- spike
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T12:59:37+00:00'
slug: ci-audit
n: 3
outcome_written: true
---

# Spike ci-audit/3

does claude -p --tools Read,Grep,Glob,Agent remove NotebookEdit and other non-read tools while kmctl:kmctl-auditor still returns parseable findings?

The command exited 0:

```
python3 -I /tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-ci-audit/spike3.py
```

## Outcome

Exit 0. With `--tools Read,Grep,Glob,Agent --allowedTools Read,Grep,Glob,Agent --disallowedTools Bash,Edit,Write,NotebookEdit`, the init tool list was only `Task, Glob, Grep, Read`. NotebookEdit, WebFetch, Cron, RemoteTrigger and Workflow were all gone, and a request to edit an existing nb.ipynb left it byte-for-byte unchanged.
`kmctl:kmctl-auditor` still dispatched (subagent used Read and Glob only) and returned a fenced json block that json.loads parsed: 1 finding, verdict drifted.
`--tools` (not --allowedTools) is the flag that narrows the tool set, so the action should pass it. Skill is not needed when the prompt carries the review instructions.
Surprise: the model said claude.ai Claude Docs MCP tools "showed up partway through" even with --tools. They come from this machine's OAuth account connectors and should be absent on a runner using ANTHROPIC_API_KEY; adding --strict-mcp-config would make sure.
Limits: one run, one fixture page, dev container rather than a clean runner. Settles risk 1 together with ci-audit/2.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike3.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-ci-audit/spike3.py`, which the command used
