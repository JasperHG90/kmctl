---
type: spike
title: Spike starter-in-repo/2
description: after moving _src_path from kmctl-starter at _commit v0.3.0 to kmctl with _subdirectory starter, does copier update or recopy bring the project onto the new template, keeping answers, so a later copier update works?
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T09:55:53+00:00'
slug: starter-in-repo
n: 2
outcome_written: true
---

# Spike starter-in-repo/2

after moving _src_path from kmctl-starter at _commit v0.3.0 to kmctl with _subdirectory starter, does copier update or recopy bring the project onto the new template, keeping answers, so a later copier update works?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike3/migrate.sh
```

## Outcome

With copier 9.19.1, a project made from kmctl-starter v0.3.0 moves onto a kmctl clone (copier.yml at root, `_subdirectory: starter`, tagged v0.6.0) by editing `_src_path` in .copier-answers.yml, committing, then `copier recopy --defaults --skip-answered --overwrite`: exit 0, answers kept (project_name demo, codeowners @octocat), `_commit` becomes v0.6.0, the template change lands, and no kmctl files leak in.
Recopy overwrites local edits to template files (the README line the user added was lost); the user must re-apply them from `git diff` before committing.
After recopy, `copier update --defaults --skip-answered` to a later v0.6.1 exits 0, applies the change, keeps answers and keeps the user's README edit with no conflicts.
Plain `copier update` right after the `_src_path` move does not fail: it exits 0 and sets `_commit: v0.6.0`, but it leaves git conflicts (UU) in README.md and justfile, because kmctl has its own v0.3.0 tag, with no starter template, to diff from. Do not document it as the migration step.
Settles risk 3: the risk does not hold, and recopy is the migration path. Limits: one project, local file paths rather than gh: URLs, default answers.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/migrate.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike3/migrate.sh`, which the command used
