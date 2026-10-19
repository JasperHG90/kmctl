---
type: spike
title: Spike release-notes/1
description: does first-parent history between v* tags give every release a Merge loop/ entry for each landed ticket, with no fast-forward lands?
tags:
- spike
generated:
  by: process:loopctl/2.2.1.dev16+g27435b040.d20261017
  at: '2026-10-19T12:49:54+00:00'
slug: release-notes
n: 1
outcome_written: true
---

# Spike release-notes/1

does first-parent history between v* tags give every release a Merge loop/ entry for each landed ticket, with no fast-forward lands?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/68b3e172-a942-4250-bcad-a0618f5282e7/scratchpad/spike-release-notes/ranges.sh
```

## Outcome

Across all 12 ranges (root..v0.2.0 through v0.9.1..v0.10.0), every `loop: land SLUG` on first-parent has a matching `Merge loop/SLUG` in the same range: no ticket landed by fast-forward.
Every range from v0.2.0..v0.3.0 on has at least one `Merge loop/` entry (1 to 20 per range; 74 in total, 34 of them before v0.2.0), so no range is empty after filtering.
Plain commits survive the filter in most ranges (0 to 14 per range); most are useful (`docs:`, `ci:`, `test:`), but `operator: manual commit(s)` (10 times, root..v0.4.0) and `chore; manual commits` (3 times, v0.4.0..v0.4.1) are noise the suggested filter misses.
Settles risk 1: the ticket ledger is not needed as a source, though the noise filter should also drop `operator: ` and `chore; manual` subjects.
Limit: checks land/merge pairing only for tickets with a `loop: land` commit; tickets done before loopctl wrote land commits would not show up.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/ranges.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/68b3e172-a942-4250-bcad-a0618f5282e7/scratchpad/spike-release-notes/ranges.sh`, which the command used
