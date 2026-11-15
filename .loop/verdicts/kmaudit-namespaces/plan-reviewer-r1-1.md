---
type: verdict
title: 'Verdict: kmaudit-namespaces plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of kmaudit-namespaces: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-14T13:10:02+00:00'
slug: kmaudit-namespaces
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach works and the one listed risk is settled by spikes 1 and 2. Three
gaps stand. Nothing says how the write verbs choose a namespace, so docs
answers would land in the `.okf` store (p1). The rule from a file or subfolder
to its namespace is missing (p2). And O1/O2's `needs` and `touches` would let
plan.split ship the folder change before the store split, which causes the
clash the plan sets out to stop (p3). Each is a revision, not a rethink.

## Checked

- Spikes 1 and 2: README outcomes, stdout, run.json. Spike 1 ran every verb on
  a plain folder (`docs/`, `handbook/`) in a fixture repo and found two sites
  outside the touches (ui.html:479, check_instructions.py:34). Spike 2 reran it
  with those added and found none outside. That answers the listed risk, within
  the fixture-repo limit the spike states.
- sections.py: `Target`, `resolve_target`, `SKIP_NAMES`. Concept ids are paths
  relative to the bundle, and a file walks up to a marked bundle root.
- store.py: `Store(root)` writes `root/.kmctl/audit.sqlite`; the tables include
  repo-wide `cache` and `decisions`.
- cli.py: `_STORE_PATH_OPTION` and the `--path` options on claims submit,
  checks try, checks submit and judge, all defaulting to `.`.
- steps.py: `EXCLUDE_DIRS` and how `Repository` filters on it.
- apm/.apm/agents and skills: the agents run `todo FILE` and then `submit -`
  with no `--path`.
- Eval rows r1 to r8 against the outcomes.

## Findings

- p1: the write verbs choose their store by `--path`, which defaults to the
  repository root, now the `.okf` namespace. The plan does not say how a submit
  reaches the docs namespace, and the agents and skills that call submit are
  outside every outcome's touches.
- p2: there is no rule from a file or subfolder to its namespace. A plain
  folder has no marker, so a per-file call can open a second, overlapping store.
- p3: O1 should need O2, not the reverse, and the Repository call sites that
  O1's check depends on are listed under O2.

## Notes

- Today `EXCLUDE_DIRS` keeps both `.okf` and `docs` out of every check. If the
  build swaps that fixed set for "only the audited folder", `.okf` checks could
  start reading `docs/` prose, which changes the read sets of the 1137 stored
  checks. Keeping the fixed set and adding the audited folder avoids this. I am
  not raising it as a finding because the build will show it.
- The O4 copy should use SQLite's backup API, not a file copy, so rows still in
  an uncheckpointed WAL file are not lost. r5's row counts will catch it if the
  fixture leaves a WAL file behind.
- README.md, docs/commands.md and the two SKILL.md files name
  `.kmctl/audit.sqlite`. Only commands.md is in the touches.
