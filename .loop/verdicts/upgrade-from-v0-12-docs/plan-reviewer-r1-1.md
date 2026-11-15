---
type: verdict
title: 'Verdict: upgrade-from-v0-12-docs plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of upgrade-from-v0-12-docs: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-15T19:46:05+00:00'
slug: upgrade-from-v0-12-docs
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The upgrade order and the steps hold against the code and v0.12.2. One premise is wrong: `kmctl doctor` cannot give a v0.12 user the new entry during the move (p1).

## Checked

- v0.12.2's pin.py hands off with `uvx --from git+...kmctl@COMMIT kmctl`, with no subdirectory. After the move, the root builds an empty wheel (ADR 0044), so a v0.12.2 CLI cannot run a v0.13.0 pin. A new CLI on PATH still runs a v0.12.2 pin, because `subdirectory_fragment` keeps the root for refs up to LAST_ROOT_RELEASE. So "install the CLI first" is safe and needed.
- `just upgrade` from a v0.12.2 project works. The old recipe runs `copier update`, then calls `just kmctl install` again, so it reads the rewritten justfile. That file has the subdirectory `kmctl_src`, and the `kmctl` recipe installs it because the CLI on PATH is older than the ref. apm.yml.jinja switches `path` above 0.12.2.
- action.yml installs from `${{ github.action_path }}/packages/kmctl`, and the hook uses `additional_dependencies: ["./packages/kmctl"]`. For both, changing only the tag is right.
- The 2.0 facts match the prose: one behaviour outcome, and its touches cover the README, the how-to and test_docs.py.

## Findings

- p1 (open, premise, blocking): doctor's update fix never shows during the move, because the CLI hands off to the pin in the lock. Write the entry straight into the docs and keep doctor as the final check.
