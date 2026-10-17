---
type: verdict
title: 'Verdict: ci-toiminnot plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of ci-toiminnot: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T18:04:31+00:00'
slug: ci-toiminnot
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

p1 is resolved. The plan now uses `actions/pre_commit` with `prek_version: "0.5.5"`, which at v1.3.0 runs prek, and spike 3 shows that command passes on this repository. Eval r1 follows that choice. No other risk could break the plan, so the verdict is pass.

## Checked

- Re-read `actions/pre_commit/action.yaml` at tag v1.3.0 (commit 4763b90706d1f689664a7b100f1924c34d15f040). It installs `prek==${prek_version}` on setup-python and runs `prek run --show-diff-on-failure --color=always --files $(git ls-files -- .)`. It takes `python_version`, `prek_version` and `directory` as inputs, so the plan's inputs exist.
- Spike 3: README, run.json and stdout. It used a bare clone, empty HOME and a Python 3.12 venv with pip-installed prek 0.5.5 and uv on PATH. It ran the action's command, both hooks passed, the exit code was 0 and the tree stayed clean. This settles the first risk for the prek path. `--color=always` and `-- .` do not change the outcome.
- Spike 2 settles the pytest risk, as round 1 found, including my uv 0.7.22 check from that round.
- setup-uv before the action's own `actions/checkout@v4` works. The checkout cleans only the workspace, and uv stays in the tool cache on PATH.
- Eval r1 to r4 match the revised intent: the pre_commit action, the prek_version tied to the justfile, the SHA pins and cache-off on the setup-uv steps ci.yml writes.

## Findings

- p1: resolved. The plan chooses prek through `actions/pre_commit` on purpose, records the swap in a ci.yml comment, and spike 3 backs the choice.

## Notes

The plan now names the inner tag pins and caches in the toiminnot actions as the operator's to change, which covers round 1's note.
