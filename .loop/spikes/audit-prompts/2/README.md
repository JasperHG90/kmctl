---
type: spike
title: Spike audit-prompts/2
description: with three false claims planted in .okf/, does one live Gemini 3.8 Flash okf-vs-code run catch all three once the prompt says every option, default and number (Correction sections too) is a claim to check?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T17:05:51+00:00'
slug: audit-prompts
n: 2
outcome_written: true
---

# Spike audit-prompts/2

with three false claims planted in .okf/, does one live Gemini 3.8 Flash okf-vs-code run catch all three once the prompt says every option, default and number (Correction sections too) is a claim to check?

The command exited 0:

```
OKF_PROMPT=okf-vs-code-r2.md python3 /tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-audit-prompts/runner.py /tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-audit-prompts/run2 okf
```

## Outcome

Exit 0: with the revised okf-vs-code prompt, one live Gemini 3.8 Flash run caught 3 of 3 plants, including the ADR 0017 Correction default (`--min-severity` medium, cited against action/agent.py:993-997 and action.yml:91-96) that spike 1 missed. 135 requests (of 200), 1 output retry, 23/23 concepts checked.
The change from spike 1's prompt is one addition to step 2: Correction sections make claims too, and every option name, default, number and limit is a claim of its own, checked by searching for it and reading the line that sets it.
Its 3 other findings are the same real drift spike 1 found (architecture diagram, `apm/.apm/instructions/`, ADR 0011's init line); 0 false positives.
With spike 1 (docs-vs-code 3/3 with the flag plant caught from source, okf-vs-docs 3/3), this settles risks 1 and 2 for this repo, as long as okf-vs-code uses the revised wording.
Limits: one run with the revised prompt, one model, one repo; it used 135 of 200 requests, so a larger bundle may need a higher cap.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/runner.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-audit-prompts/runner.py`, which the command used
- `files/okf-vs-code-r2.md.txt`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-audit-prompts/prompts/okf-vs-code-r2.md`, which the command used
