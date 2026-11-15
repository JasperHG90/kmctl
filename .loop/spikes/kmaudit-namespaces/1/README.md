---
type: spike
title: Spike kmaudit-namespaces/1
description: with Target.bundle pointed at a plain markdown folder (docs/, handbook/), which kmaudit code paths beyond resolve_target, the store path, EXCLUDE_DIRS and CLI help raise or give wrong results?
tags:
- spike
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T13:06:30+00:00'
slug: kmaudit-namespaces
n: 1
outcome_written: true
---

# Spike kmaudit-namespaces/1

with Target.bundle pointed at a plain markdown folder (docs/, handbook/), which kmaudit code paths beyond resolve_target, the store path, EXCLUDE_DIRS and CLI help raise or give wrong results?

The command exited 1:

```
bash -c unset VIRTUAL_ENV; uv run --project /home/vscode/workspace python -I /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-ns/plain_folder.py
```

## Outcome

I set Target.bundle to a plain folder (`docs/`, then `handbook/`) in the fixture repo and ran cut, claims todo/submit/list, checks todo/try/submit, coverage, ui.build and ui.file_text. **None of them raised.** The page lists the folder's pages. lines.py finds line windows for all 3 claims without `sources` front matter (from backticks and anchors).
Wrong results that need a change inside the plan's files: `SKIP_NAMES` (sections.py:18) skips a plain folder's `sub/index.md`. When the folder is not `docs/`, `Repository` (steps.py:290, which knows only `root`) lets a check read and hold on `handbook/guide.md`, and coverage, the ui code view and `ui.file_text` count it as code. So `Repository` has to take the audited folder, at its 12 call sites in check_verbs.py, ui.py and coverage.py.
Two sites fall outside the touched files, both one-line text: ui.html:479 always shows the path as `.okf/<concept>.md`, and check_instructions.py:34 tells check writers that only `.okf/` and `docs/` are never read (not hashed into any key).
Exit 1 only because of those two sites. Risk 1 holds but stays small: add ui.html and check_instructions.py to the touched files. Ran on one fixture repo, not on real docs.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/plain_folder.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-ns/plain_folder.py`, which the command used
