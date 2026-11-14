---
type: spike
title: Spike kmaudit-briefing/1
description: how long a read-only summary of this repository's .okf namespace takes (cut every page, compare keys, count check statuses), against a SessionStart hook's budget
tags:
- spike
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T14:00:02+00:00'
slug: kmaudit-briefing
n: 1
outcome_written: false
---

# Spike kmaudit-briefing/1

how long a read-only summary of this repository's .okf namespace takes (cut every page, compare keys, count check statuses), against a SessionStart hook's budget

The command exited 0:

```
uv run python -c 
import shutil, time
from pathlib import Path
Path('.kmctl').mkdir(exist_ok=True)
shutil.copy('/home/vscode/workspace/.kmctl/audit.sqlite', '.kmctl/audit.sqlite')
from kmaudit.sections import cut, resolve_target
from kmaudit.store import Store
from kmaudit.check_verbs import list_checks
t = time.perf_counter()
target = resolve_target(Path('.okf'))
Store(target.root, target.namespace).db.close()
t_open = time.perf_counter() - t
t = time.perf_counter()
sections = list(cut(target))
with Store(target.root, target.namespace) as store:
    extracted = store.extracted()
pending = [s for s in sections if extracted.get(s.id) != s.key]
t_cut = time.perf_counter() - t
t = time.perf_counter()
counts = list_checks(Path('.okf')).counts
t_list = time.perf_counter() - t
print(f'first open (legacy copy): {t_open:.2f}s')
print(f'cut + compare keys: {t_cut:.2f}s, {len(sections)} sections, {len(pending)} pending')
print(f'list_checks: {t_list:.2f}s, counts {counts}')

```

## Outcome

Not written yet: `loopctl plan spike-note kmaudit-briefing 1`.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
