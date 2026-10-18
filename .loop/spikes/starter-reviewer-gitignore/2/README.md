---
type: spike
title: Spike starter-reviewer-gitignore/2
description: which apm.yml forms of jasperhg90/skills agents/adversarial-reviewer.md (pinned or unpinned shorthand, git object with path) does APM 0.33.0 accept?
tags:
- spike
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T18:18:31+00:00'
slug: starter-reviewer-gitignore
n: 2
outcome_written: true
---

# Spike starter-reviewer-gitignore/2

which apm.yml forms of jasperhg90/skills agents/adversarial-reviewer.md (pinned or unpinned shorthand, git object with path) does APM 0.33.0 accept?

The command exited 1:

```
python3 /tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-reviewer/forms.py
```

## Outcome

`apm install --target claude` on APM 0.33.0, one dependency per apm.yml. The pinned shorthand `jasperhg90/skills/agents/adversarial-reviewer.md#09b7a0a8` exits 1. So does the unpinned README form, both with the same "Individual files must end with one of: .prompt.md, .instructions.md, .agent.md" error. The `git:` object with `path: agents/adversarial-reviewer.md` and `ref` also exits 1 ("1 package failed"; the detailed reason was filtered out of the output).
Control: the pinned single file `rules/adversarial-reviews.instructions.md#09b7a0a8` exits 0 and lands at `.claude/rules/adversarial-reviews.md`. So `#sha` pins on single files work, and the rule could still come from APM.
Rules out the pin as the cause. The agent needs an `.agent.md` name upstream, or another way to install it. README.md's reviewer section (line 319) gives the same rejected form.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/forms.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/efac4bda-9c30-41af-bec2-10265f82b0d7/scratchpad/spike-reviewer/forms.py`, which the command used
