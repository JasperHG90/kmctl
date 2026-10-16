---
type: spike
title: Spike release-flow/1
description: does the hatchling regex version source reading plugin.json give 0.2.0 for uv build, uv tool install git+file at tag, and uv tool install of a git archive folder
tags:
- spike
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261015
  at: '2026-10-16T05:28:47+00:00'
slug: release-flow
n: 1
outcome_written: true
---

# Spike release-flow/1

does the hatchling regex version source reading plugin.json give 0.2.0 for uv build, uv tool install git+file at tag, and uv tool install of a git archive folder

The command exited 0:

```
/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-release-flow/version-source.sh
```

## Outcome

In a clone of HEAD 90ea08d with `dynamic = ["version"]`, `[tool.hatch.version] source = "regex"`, `path = "plugin/.claude-plugin/plugin.json"`, `pattern = '"version": "(?P<version>[^"]+)"'` and the manifest set to 0.2.0, every install path gave 0.2.0, and the run exited 0.
`uv build` made `kmctl-0.2.0-py3-none-any.whl` and `kmctl-0.2.0.tar.gz`. The sdist holds `plugin/.claude-plugin/plugin.json`, and a wheel built from the extracted sdist is also 0.2.0. Installing the wheel prints `kmctl 0.2.0`.
`uv tool install git+file://<bare remote>@v0.2.0` and `uv tool install <git archive folder with no .git>` (the `action.yml` path) both print `kmctl 0.2.0`.
This settles risk 1. Limits: one uv version on Linux, a local `file://` remote rather than GitHub, and the GitHub action download stood in for by `git archive`.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/version-source.sh`: a copy of `/tmp/claude-1000/-home-vscode-kmctl/eee74b7b-f30f-4b17-b768-7eca3fbaa063/scratchpad/spike-release-flow/version-source.sh`, which the command used
