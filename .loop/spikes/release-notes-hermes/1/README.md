---
type: spike
title: Spike release-notes-hermes/1
description: does deepseek-v4.1-flash, rewriting a real release-notes draft, keep the headings, the sections after What changed and every (`slug`)/(#N) reference often enough for the cleaning checks to keep its rewrite?
tags:
- spike
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T19:49:08+00:00'
slug: release-notes-hermes
n: 1
outcome_written: true
---

# Spike release-notes-hermes/1

does deepseek-v4.1-flash, rewriting a real release-notes draft, keep the headings, the sections after What changed and every (`slug`)/(#N) reference often enough for the cleaning checks to keep its rewrite?

The command exited 0:

```
bash -ic python3 /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-hermes/spike.py "$PWD"
```

## Outcome

`ollama/deepseek-v4.1-flash` through Bifrost kept every check on 15 of 15 rewrites (5 real drafts, v0.9.0 to v0.12.1, 3 runs each, default temperature): headings in order, everything from `## Other changes` on unchanged, the same `` (`slug`) ``/`(#N)` set under What changed, one per bullet, no preamble or fence. The rewrites were real (the v0.12.1 `fix(release-notes):` prefix dropped, every v0.11.0 bullet reworded), not copies.
This rules out the fallback-almost-every-time case and settles risk 1. Checker and caller: `files/spike.py`; the draft prompt it sent is `release-notes-system.md` beside it in the scratch dir (not copied into the evidence).
Limits: a single chat call, not the Hermes agent action with tools and its own wrapper; small sample. The checks do not catch vague wording: v0.9.0's "reviewer finding f4" bullets became "the `verify` command now handles more edge cases safely", which passes but says little.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-hermes/spike.py`, which the command used
