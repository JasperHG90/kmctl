---
type: spike
title: Spike decision-gaps-measure/2
description: With .okf/ and .loop/ paths hidden from every unit and the wider strip pattern, can detectors that share nothing with strip tell hidden positives from negatives?
tags:
- spike
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-16T11:51:35+00:00'
slug: decision-gaps-measure
n: 2
outcome_written: true
---

# Spike decision-gaps-measure/2

With .okf/ and .loop/ paths hidden from every unit and the wider strip pattern, can detectors that share nothing with strip tell hidden positives from negatives?

The command exited 0:

```
python3 /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/gaps/scripts/leak_spike.py . /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/gaps/results/units.jsonl
```

## Outcome

Answered, with a small residue the README must state. Spike 1 could not fail (it tested strip's output with strip's own pattern). This spike uses detectors that share nothing with strip, on the view the judge gets once .okf/ and .loop/ paths are hidden from every unit alike and the strip pattern also drops sentences naming .okf/, summary.md, log.md, 'next free' or 'the number'. Visible bookkeeping paths: AUC 0.50, chance, so the file view no longer gives positives away. A separate list of record-keeping words: AUC 0.64 over 30 positives and 130 negatives, driven by 'summary' and 'bundle' (24 v 14-15 per 10k words), which reflects that decision-making tickets here often change the knowledge system itself rather than a trace of the hidden record. The README reports judge recall with this residue named, and ADR 0030, whose unit changes nothing outside .okf/ and .loop/, is counted apart as record-only.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
