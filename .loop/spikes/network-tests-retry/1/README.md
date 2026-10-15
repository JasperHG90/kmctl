---
type: spike
title: Spike network-tests-retry/1
description: with github.com unresolvable for git, do kmctl plugin install and the pytest failure report of an asserted install name the network error
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev61+g8318eb7a1.d20261015
  at: '2026-10-15T19:12:18+00:00'
slug: network-tests-retry
n: 1
outcome_written: true
---

# Spike network-tests-retry/1

with github.com unresolvable for git, do kmctl plugin install and the pytest failure report of an asserted install name the network error

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-ntr/spike.py
```

## Outcome

claude 2.1.300's marketplace clone honours git config: with `GIT_CONFIG_GLOBAL` mapping `https://github.com/` to `unresolvable.invalid`, `claude plugin marketplace add` exits 1, and the last line of its stderr is git's `fatal: unable to access '...': Could not resolve host: unresolvable.invalid`.
`_require` keeps that line, so `kmctl plugin install --scope project` exits 1 with "Could not resolve host" in its message. The pytest failure reports of test_install_pulls_okf and of test_update_after_bump (with its install asserted) both show the same full message in the AssertionError.
claude's own first line ("Network error or timeout ... check your internet connection") is dropped, so the retry hook must match git's wording, not claude's. `_require` does not need to keep more than the last line.
Settles risk 1 for a DNS failure on the okf marketplace add. Not tested: connection refused or timed out, or a network error at a later step (marketplace update, plugin install).

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-ntr/spike.py`, which the command used
