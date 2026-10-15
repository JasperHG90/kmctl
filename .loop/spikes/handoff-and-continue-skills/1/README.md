---
type: spike
title: Spike handoff-and-continue-skills/1
description: can a Claude Code skill read the current session id, from its Bash env or a SKILL.md substitution?
tags:
- spike
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T08:12:42+00:00'
slug: handoff-and-continue-skills
n: 1
outcome_written: true
---

# Spike handoff-and-continue-skills/1

can a Claude Code skill read the current session id, from its Bash env or a SKILL.md substitution?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-session-id/check.sh
```

## Outcome

A skill can read the session id two ways, so no hook is needed. The Bash tool env carries `CLAUDE_CODE_SESSION_ID` (a UUID, here `eee74b7b-...`, the same as the parent session even from a subagent and a loopctl worktree). The skills docs list a `${CLAUDE_SESSION_ID}` substitution for SKILL.md text.
The env-vars docs say this value matches the hook `session_id` and changes on `/clear`. So a second `/handoff` in the same session finds the same key, but one after `/clear` gets a new key. memex reads `.session_id` from hook stdin; we do not need that.
This rules out falling back to matching on title. It settles risk 1. Limits: tested on Claude Code 2.1.300 in a local CLI session only. Per the docs, `${CLAUDE_SESSION_ID}` stays literal text in a non-local (synced) skill.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/check.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-session-id/check.sh`, which the command used
