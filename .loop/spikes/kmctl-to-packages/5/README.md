---
type: spike
title: Spike kmctl-to-packages/5
description: on the moved tree (root package = false, kmctl in packages/kmctl), can a consumer repo install and run the kmctl-check hook with prek 0.5.5 and pre-commit, via additional_dependencies ./packages/kmctl alone or with an empty-wheel root build-system?
tags:
- spike
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T19:50:47+00:00'
slug: kmctl-to-packages
n: 5
outcome_written: true
---

# Spike kmctl-to-packages/5

on the moved tree (root package = false, kmctl in packages/kmctl), can a consumer repo install and run the kmctl-check hook with prek 0.5.5 and pre-commit, via additional_dependencies ./packages/kmctl alone or with an empty-wheel root build-system?

The command exited 0:

```
python3 /tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-k2p-hook/hook_install.py
```

## Outcome

On the moved tree (restructure.py `--variant hook`, root `[tool.uv] package = false`, members `packages/*`), committed in a throwaway repo, a consumer repo pointing `repo:` at that clone ran kmctl-check with prek 0.5.5 and pre-commit 4.7.0.
(a) `additional_dependencies: ["./packages/kmctl"]` alone fails in both tools (prek exit 2, pre-commit exit 3). Both still install the root, and a root with no `[build-system]` falls back to setuptools legacy, which stops with "Multiple top-level packages discovered in a flat-layout: ['apm', 'action', 'starter', 'packages']". kmctl itself builds fine from `./packages/kmctl`.
(b) Works in both tools: (a) plus a root `[build-system]` of hatchling with `[tool.hatch.build.targets.wheel] bypass-selection = true`, so the root builds an empty `kmctl-workspace` wheel. With no args the hook fails with kmctl's own finding ("docs/how-to folder has no README.md index"). `args: [--fix]` writes the index and exits 0, and the next run exits 0. At the root, `uv sync --locked` still exits 0, `uv run kmctl --version` prints `kmctl 0.12.1`, and kmctl-workspace is not installed.
Settles risk 4: yes, with candidate (b). Limits: (c) (uvx entry, language system) was not tried because (b) works. The hook repo was a local path, not a GitHub URL. The run uses restructure.py from the earlier spikes' scratch folder, which this spike's evidence does not copy.

## Files

- `run.json`: the command, when it ran, its exit, the commit and tree it ran on, and where its output went
- `stdout.txt`: its standard output
- `stderr.txt`: its standard error
- `files/hook_install.py`: a copy of `/tmp/claude-1000/-home-vscode-workspace/ea1edca4-2d55-48a1-b186-f81e60a3d11d/scratchpad/spike-k2p-hook/hook_install.py`, which the command used
