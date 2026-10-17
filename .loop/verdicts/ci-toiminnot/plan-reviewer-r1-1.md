---
type: verdict
title: 'Verdict: ci-toiminnot plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of ci-toiminnot: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T18:02:47+00:00'
slug: ci-toiminnot
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

Both listed risks are settled by their spikes, and an extra check shows the pytest action's uv 0.7.x handles this repo. One premise needs fixing before build: in toiminnot v1.3.0, `actions/prek` runs pre-commit and `actions/pre_commit` runs prek. The plan picked the action by its name, so CI would stop running prek and lose the justfile's prek pin. That is a revision, not a rethink. Verdict: fail.

## Checked

- Read both action.yaml files at the v1.3.0 SHA, plus `actions/pre_commit/action.yaml` and both READMEs. `actions/prek` installs `pre-commit==4.2.0`; `actions/pre_commit` installs `prek==${prek_version}` and runs `prek run --show-diff-on-failure --files $(git ls-files)`. The READMEs describe the opposite.
- Spike 1: `uvx --python 3.12 pre-commit==4.2.0 run --show-diff-on-failure --files $(git ls-files)` in a bare clone exited 0, tree clean. This answers the risk for pre-commit with uv on PATH. Both hooks are `language: system`, `pass_filenames: false`, `uv run ...`, so setup-python's 3.12 versus uv's Python does not matter: `uv run` uses `.python-version` (3.12) and the project venv.
- Spike 2: `uv sync --all-extras --all-groups` then `uv run pytest tests -m 'not integration'` gave 703 passed, 8 deselected. It ran with uv 0.13, not the action's `uv_version: 0.7.x`. I ran that gap myself in a fresh clone under the scratchpad: uv 0.7.22 synced against `uv.lock` (revision 5) without rewriting it, and pytest gave 703 passed, 8 deselected. So the old uv in the action does not break the job.
- Shallow checkout: both actions use `actions/checkout@v4` at its default depth 1. The current prek and tests jobs are shallow too, so nothing changes there; only the knowledge job needs full history and it keeps its own checkout.
- Eval r3's pin pattern allows `owner/repo/path@sha`; the current test's regex `[\w-]+/[\w-]+@[0-9a-f]{40}` does not, which the plan already says it changes.

## Findings

- p1 (premise): the plan picks `actions/prek` by its name, but at v1.3.0 that action runs pre-commit 4.2.0; `actions/pre_commit` is the one that runs prek. The plan has to choose deliberately, either prek via `actions/pre_commit` with `prek_version: "0.5.5"` or pre-commit with the operator's acceptance, and r1 has to follow that choice. If it picks prek, a short spike should confirm `pip install prek==0.5.5` on Python 3.12, then `prek run --show-diff-on-failure --files $(git ls-files)` in a bare clone with uv on PATH, passes.

## Notes

Not findings, but worth one line in the plan. The toiminnot actions use tag-pinned inner actions (`actions/checkout@v4`, `setup-python@v5`, `setup-uv@v6`, `actions/cache@v4`), so pinning toiminnot by SHA does not pin what runs inside it. The hook action also caches `~/.cache/pre-commit` (or `~/.cache/prek`) with `actions/cache@v4`, a second cache beyond the pytest uv cache the plan already accepts. Both come from the operator's own actions, so they need acceptance, not a code change here.
