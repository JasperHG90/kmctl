---
type: spike
title: Spike plugin-remove/2
description: does dropping a target from apm.yml targets and running apm 0.33.0 install --target REST remove the dropped target files and lock entries, for a claude+antigravity kmctl install in each direction?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T06:08:29+00:00'
slug: plugin-remove
n: 2
outcome_written: true
---

# Spike plugin-remove/2

does dropping a target from apm.yml targets and running apm 0.33.0 install --target REST remove the dropped target files and lock entries, for a claude+antigravity kmctl install in each direction?

The command exited 1:

```
/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-remove-2/drop-target.sh
```

## Outcome

The risk holds in part: exit 1. A claude+antigravity kmctl install went through APM 0.33.0. Then `targets:` was edited to one harness and `apm install --target REST --allow-insecure` was run.
- Drop claude, keep antigravity: clean. APM cleaned 54 stale files. No APM file is left under `.claude/` (44 before, 0 after), and the lock has 0 `.claude/` entries. okf's Stop hook left `.claude/settings.json`; kmctl's SessionStart hook stays.
- Drop antigravity, keep claude: the skills, rules and `.agents/apm-hooks.json` go (42 files before, 2 after), but two files stay. `.agents/hooks/okf-skills/hooks/okf-stop-check.sh` stays on disk and in the lock, because APM records its deployment as `target: legacy`, not `antigravity`. `.agents/hooks.json` stays, emptied to `{}`.
- Neither a plain `apm install` (targets from apm.yml) nor `apm prune` ("no orphaned packages") removes those two. The fix: after dropping antigravity, remove deletes the okf hook script, its folder and an empty `.agents/hooks.json` itself, and drops the `legacy` lock entry, or leaves them and documents it.
- `.agents/plugins/kmctl/` and claude's settings/MCP entries are kmctl's own and were not part of this check. Ran once per direction on kmctl v0.3.0 at HEAD.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/drop-target.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/ca0a6ec4-fb78-4dae-a201-8e5e832f449a/scratchpad/spike-remove-2/drop-target.sh`, which the command used
