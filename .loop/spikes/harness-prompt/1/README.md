---
type: spike
title: Spike harness-prompt/1
description: does any caller in the repo run kmctl plugin install or update without --harness?
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T05:55:39+00:00'
slug: harness-prompt
n: 1
outcome_written: true
---

# Spike harness-prompt/1

does any caller in the repo run kmctl plugin install or update without --harness?

The command exited 0:

```
hits=$(git ls-files | grep -v "^\.loop/" | xargs grep -nE "kmctl plugin (install|update)" | grep -vE -- "--harness" ); echo "$hits"; printf "%s\n" "$hits" | grep -E "(action\.yml|^action/|^\.github/|justfile|subprocess|invoke|\[\"plugin\")" && exit 1; exit 0
```

## Outcome

The risk does not hold. No script runs kmctl plugin install or update without
--harness: action.yml, action/, .github/ and the justfile never run kmctl
plugin. Every other hit is prose (help text, docstrings, error fixes, docs) or
a test. One test, tests/test_plugin.py's test_install_update_runs_the_same_steps,
runs `kmctl plugin update` bare and relies on the old claude default; this
ticket changes it, since that default is what the ticket replaces. The docs'
bare `kmctl plugin update` lines are for a person at a terminal, who now gets
the question with the installed harnesses as its default.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
