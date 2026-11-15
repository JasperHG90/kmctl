---
type: spike
title: Spike release-notes-owned-paths/1
description: how many commits do kmctl's release notes list that touch only paths no package ships (.loop/, .okf/, .claude/, uv.lock)?
tags:
- spike
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-15T05:20:41+00:00'
slug: release-notes-owned-paths
n: 1
outcome_written: true
---

# Spike release-notes-owned-paths/1

how many commits do kmctl's release notes list that touch only paths no package ships (.loop/, .okf/, .claude/, uv.lock)?

The command exited 0:

```
python3 /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/owned/measure.py agent-audit
```

## Outcome

## Outcome

Over the last six kmctl release ranges (v0.9.1 to agent-audit), the current rule kept 43 commits for kmctl's notes; 7 of them (16%) touch only `.loop/`, `.okf/`, `.claude/` or `uv.lock` among the paths kmctl owns, so they ship nothing to kmctl users. The coming release is the worst: 5 of 17, including the kmaudit-mcp and kmaudit-briefing merges, which reach kmctl's notes only through `.okf/` edits and the shared `uv.lock`. Leaving those four prefixes out of kmctl's paths would have dropped all 7 and nothing else. The ceiling grows once kmaudit work stops editing kmctl's APM package (kmaudit-skills-mcp), since kmaudit-namespaces is kept today only by its edits to `apm/.apm/skills/`.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/measure.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/owned/measure.py`, which the command used
