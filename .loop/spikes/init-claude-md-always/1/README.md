---
type: spike
title: Spike init-claude-md-always/1
description: with Claude Code 2.1.300, does it load AGENTS.md alone, still load AGENTS.md beside a CLAUDE.md, and load it exactly once through a CLAUDE.md holding only @AGENTS.md
tags:
- spike
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T16:36:06+00:00'
slug: init-claude-md-always
n: 1
outcome_written: true
---

# Spike init-claude-md-always/1

with Claude Code 2.1.300, does it load AGENTS.md alone, still load AGENTS.md beside a CLAUDE.md, and load it exactly once through a CLAUDE.md holding only @AGENTS.md

The command exited 0:

```
python3 /tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-agentsmd/driver.py
```

## Outcome

Claude Code 2.1.300 loads AGENTS.md only as a fallback when the repo has no CLAUDE.md. The built-in `cc-plugin-agents-md` plugin logs "no CLAUDE.md found; AGENTS.md loaded: …/AGENTS.md" in case 1 and logs nothing in the other cases.
Model counts (AGENTS codeword, CLAUDE codeword), same in both runs of each case: AGENTS.md only (1,0); CLAUDE.md only (0,1); both files, no import (0,1), so a CLAUDE.md hides AGENTS.md; CLAUDE.md holding only `@AGENTS.md` (1,0), so AGENTS.md's text loads exactly once.
This settles risk p2 for Claude Code: a new CLAUDE.md that holds only the kmctl block would hide an existing AGENTS.md, and adding an `@AGENTS.md` line fixes that without loading the text twice.
Limits: one Claude Code version, `-p` with no tools, the operator's login and global ~/.claude/CLAUDE.md, git repos with nothing committed. Other harnesses that read both files were not tested.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/driver.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-agentsmd/driver.py`, which the command used
