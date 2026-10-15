---
type: spike
title: Spike ci-audit/4
description: real knowledge-audit.sh with real claude reads the audit skill by path, dispatches the auditor, writes a drifted finding and changes nothing
tags:
- spike
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T13:13:01+00:00'
slug: ci-audit
n: 4
outcome_written: true
---

# Spike ci-audit/4

real knowledge-audit.sh with real claude reads the audit skill by path, dispatches the auditor, writes a drifted finding and changes nothing

The command exited 0:

```
python3 /tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/ci-audit-real/spike4.py
```

## Outcome

Exit 0. The real `action/knowledge-audit.sh` (after the review round 1 fixes f1 and f2) ran real claude 2.1.300 with the action's flags on a fixture with one due architecture page that had drifted. The session read the audit skill by its path, dispatched `kmctl:kmctl-auditor`, and the script wrote a drifted finding for `architecture/overview` to the summary, citing the page and `src/greet.py:2`. gh was asked to list issues and then create "Knowledge audit". The fixture's git status stayed empty.

The JSON error on stderr comes from the stub gh printing nothing for `issue list`. Real gh prints `[]`. The script's handling of a failing gh is reviewer finding f4, deferred to its stub ticket.

Limits: one fixture page, a dev container with OAuth rather than a runner with an API key, and a stub gh.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike4.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/ci-audit-real/spike4.py`, which the command used
