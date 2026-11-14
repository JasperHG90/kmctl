---
type: verdict
title: 'Verdict: kmaudit-namespaces plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of kmaudit-namespaces: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-14T13:12:39+00:00'
slug: kmaudit-namespaces
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

All three round 1 findings are resolved, and I found no new risk that could
break the plan. The one listed risk is settled by spikes 1 and 2. The 2.0
facts match the prose. Pass.

## Checked

- Spikes 1 and 2 (README outcome, stdout, run.json). Spike 1 ran every verb on
  a plain folder in a fixture repo: nothing raised, and every wrong result is
  in a file the plan now touches. Spike 2 reran it with ui.html and
  check_instructions.py added and exited 0. That answers the listed risk, with
  the fixture-repo limit the spike states.
- sections.py `resolve_target` (sections.py:125): today a file must sit under a
  bundle and a folder must be a bundle or hold `.okf`. The new mapping rule
  replaces both branches and keeps the root-means-`.okf` case (r6).
- verbs.py `submit` and `_check_answer` (verbs.py:250): an answer is matched
  to a section row in the store, so an answer sent to the wrong namespace's
  store is refused as an unknown section or a stale key. It is not stored
  silently. That bounds the harm if a caller leaves out `--path`.
- cli.py: `--path` already exists on claims submit, checks try, checks submit
  and judge (`_STORE_PATH_OPTION`), so O3 changes what it resolves to rather
  than adding a new surface. 16 `Store(` call sites, as the plan says.
- guard.py: the hook checks only the `kmaudit claims` / `kmaudit checks`
  prefix, so `--path docs` on a submit gets through.
- apm agents and skills: the agents run `todo FILE` and `submit -` today. They
  are in O3's touches, and r9 extends tests/test_skills.py to require
  `--path`.
- Facts against prose: O1 support, needs none, fixes P2, touches the store
  and the Store call sites. O2 behaviour, needs O1, fixes P1, touches
  steps.py and the Repository call sites. O3 support, needs O1, fixes P6.
  O4 behaviour, needs O1. O5 support, needs O1. O6 support, needs none. Each
  matches what the prose says changes. Eval rows r1 to r9 cover them.

## Findings

- p1: resolved. The write verbs name their namespace by `--path`, and the
  agents and skills pass it (O3, r2, r9).
- p2: resolved. The mapping rule is stated and checked (r2b, r6).
- p3: resolved. O1 and O2 are swapped, and the Repository sites sit under O2.

## Notes

- If plan.split ships O2 before O3, the skills can hand out docs sections, but
  the agents' answers, submitted without `--path`, are refused as unknown
  sections in the `.okf` store. That fails loudly and loses nothing, so I am
  not raising it. Shipping O2 and O3 together avoids the gap.
- The rule does not say what a plain `.md` file opens when no namespace sits
  above it yet. The skills run `todo [PATH]` on the folder before handing
  files to agents, so the folder opens first. The build should still pick
  the rule (the file's folder, or a refusal) and say it in the refusal text.
- The first call decides: running `todo docs/sub` first opens `docs/sub`, and
  `docs` is refused from then on, with the error naming `docs/sub`. That is
  the plan's stated contract. The refusal should say how to get out of it
  (for example, delete the store file under `.kmaudit/`).
- O1's check uses a `docs` namespace. Before O2 lands, that test needs `docs`
  to be an OKF bundle, or it has to build the Target directly.
