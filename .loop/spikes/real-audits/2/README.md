---
type: spike
title: Spike real-audits/2
description: does a citation validator (ModelRetry on any path:line not read or search-hit) let a live Gemini 3.8 Flash audit of kmctl finish within 5 output retries and the 200-request cap?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T14:43:06+00:00'
slug: real-audits
n: 2
outcome_written: true
---

# Spike real-audits/2

does a citation validator (ModelRetry on any path:line not read or search-hit) let a live Gemini 3.8 Flash audit of kmctl finish within 5 output retries and the 200-request cap?

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-real-audits/run.sh
```

## Outcome

Exit 0: the live Gemini 3.8 Flash audit of kmctl finished in 9.4 minutes and 85 of the 200 allowed requests. The validator ran once and rejected 0 of 62 citations, so there were 0 retries. The report has 20 checked entries and 0 findings.
The agent made 47 read_file calls (16 of them with an offset or limit), 27 search_files calls, 6 list_files calls and 4 run_shell calls. All of its citations fell inside a range it read or matched a search hit. Run 1, which crashed on a stats bug in the spike, also passed 82 of 82 citations on the first try.
This settles risk 1 for this repo and model: with the prompt saying citations are checked, the agent did not get stuck in retries and stayed well under the cap.
Limits: two runs, one model, one repo. Neither run triggered a retry, so it is unknown whether the agent can recover once a citation is rejected. The offline TestModel did show the failure path: after 5 rejected outputs it stops with UnexpectedModelBehavior (7 requests). The plan's offline test should cover recovery.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/agent.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-real-audits/agent.py`, which the command used
- `files/run.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/dff53b03-6dd4-4578-a2d3-39665316bb2b/scratchpad/spike-real-audits/run.sh`, which the command used
