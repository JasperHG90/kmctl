---
type: spike
title: Spike audit-prompts/1
description: with three false claims planted per copy of kmctl, does a single live Gemini 3.8 Flash run of each draft audit prompt (docs-vs-code, okf-vs-code, okf-vs-docs) catch all three, including a renamed CLI flag that only --help or source shows?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T16:52:03+00:00'
slug: audit-prompts
n: 1
outcome_written: true
---

# Spike audit-prompts/1

with three false claims planted per copy of kmctl, does a single live Gemini 3.8 Flash run of each draft audit prompt (docs-vs-code, okf-vs-code, okf-vs-docs) catch all three, including a renamed CLI flag that only --help or source shows?

The command exited 1:

```
python3 /tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-audit-prompts/runner.py /tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-audit-prompts/run1
```

## Outcome

Exit 1: one live Gemini 3.8 Flash run per draft prompt caught 8 of 9 planted false claims. docs-vs-code 3/3 (78 requests, 1 output retry, 7/7 pages checked), okf-vs-docs 3/3 (47 requests, 0 retries, 7/7 pages), okf-vs-code 2/3 (111 requests, 0 retries, all 23 concepts checked; the 3 indexes were not). All three exited 0 within 9 minutes.
okf-vs-code missed the default changed in ADR 0017's Correction (`--min-severity` default high -> medium at line 113): it read lines 101-120 but checked that ADR with only 3 evidence lines. So risk 1 is real for okf-vs-code with this prompt: a whole-folder pass skims numbers in long concepts.
Risk 2 does not hold: the renamed flag (`--by` -> `--with` in docs/reference/commands.md:262) was caught, citing src/kmctl/__init__.py:623-628; the agent also ran `kmctl decision supersede --help` but cited the source.
The 8 findings that were not plants all look like real drift in main (sampled each against the code): stale `kmctl 0.1.0` in docs, briefing help text, `apm/.apm/instructions/` in the architecture page, pluginPy shown running APM, ADR 0011's old init line, and docs saying the CI auditor has only read and search tools. 0 false positives.
Limits: one run per prompt, one model, one repo; plants and the line lists are in the runner and in run1/plants-*.json.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/runner.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-audit-prompts/runner.py`, which the command used
- `files/agent.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-audit-prompts/agent.py`, which the command used
- `files/docs-vs-code.md.txt`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-audit-prompts/prompts/docs-vs-code.md`, which the command used
- `files/okf-vs-code.md.txt`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-audit-prompts/prompts/okf-vs-code.md`, which the command used
- `files/okf-vs-docs.md.txt`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-audit-prompts/prompts/okf-vs-docs.md`, which the command used
