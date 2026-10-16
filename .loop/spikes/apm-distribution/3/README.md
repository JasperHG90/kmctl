---
type: spike
title: Spike apm-distribution/3
description: does an APM 0.33.0 consumer get the root apm.yml dependencies of the kmctl package, and do devDependencies or a plugin/ subfolder package keep them out; does apm.yml need version
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261016
  at: '2026-10-16T10:11:10+00:00'
slug: apm-distribution
n: 3
outcome_written: true
---

# Spike apm-distribution/3

does an APM 0.33.0 consumer get the root apm.yml dependencies of the kmctl package, and do devDependencies or a plugin/ subfolder package keep them out; does apm.yml need version

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm-dist/spike2-devdeps.sh
```

## Outcome

With the real dev rule (`jasperhg90/skills/rules/plain-language.instructions.md#f0813cd`) in the root apm.yml `dependencies.apm`, a consumer that installs the repo root gets `.claude/rules/plain-language.md` and no kmctl skills (R1). APM 0.33.0 does have `devDependencies`: `apm install --dev` writes there, and the lock marks those entries `is_dev: true`. Moved there, the rule stays out of a root consumer and still installs in the source repo itself (R2). A root install brings no kmctl skills either way, though.
The route that matters: a consumer that installs `path: plugin` gets no root dependencies, with or without a `plugin/apm.yml` (R3a, R3b). It gets the kmctl skills and no rule. So the repo's own root apm.yml can keep its dev rules under plain `dependencies`.
`version:` is required in the consumer's own apm.yml ("Missing required field 'version' in apm.yml", exit 1). A `plugin/apm.yml` with no version still installed, probably because APM then reads plugin.json instead; this run did not confirm that.
Settles risk 2: dev items do not reach consumers of the `plugin/` subfolder.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/spike2-devdeps.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm-dist/spike2-devdeps.sh`, which the command used
- `files/common.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm-dist/common.sh`, which the command used
- `files/githttp.py`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-apm-dist/githttp.py`, which the command used
