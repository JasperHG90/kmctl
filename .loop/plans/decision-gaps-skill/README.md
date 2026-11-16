---
type: plan
title: 'Plan: decision-gaps-skill'
description: A decision-gaps skill in kmctl's package runs kmctl decision candidates, judges every change it lists, and reports the changes that made a decision no record covers, each with the choice and the rejected option, writing nothing; made with the skill-creator skill.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-16T16:02:05+00:00'
slug: decision-gaps-skill
epic: null
depends_on:
- decision-candidates
priority: null
schema_version: '2.0'
---

# decision-gaps-skill

Relayed from: none

## Intent

The second half of the history scan the operator asked for, after
`decision-candidates` builds `kmctl decision candidates`. The operator's
words on what it does: "the skill would report back to the user what it
found, and it's up to the user to make that into decision records or not."

`new:packages/kmctl/apm/.apm/skills/decision-gaps/SKILL.md` is made with
the skill-creator skill (`anthropic-skills:skill-creator`), as ADR 0007
requires and the operator asked: drafted, run on realistic prompts, and its
description tuned for triggering. Its test prompts and results stay beside
it in `new:packages/kmctl/apm/.apm/skills/decision-gaps/evals/evals.json`
and `new:packages/kmctl/apm/.apm/skills/decision-gaps/evals/results.md`, as
the audit skill keeps its own.

The skill, following `.okf/prototypes/decision-gaps/`'s conclusion:

- runs `kmctl decision candidates` (with `--since` when the user names a
  starting point) and judges every change it lists, not only the high
  scorers;
- keeps the judging close to how it was measured, where each change was
  judged on its own with little context: it reads the table first, then one
  change at a time from `--json` and git, and judges in batches of about
  ten; where the harness has subagents (Claude Code), each batch goes to
  one with only that batch's changes. When the list is longer than about
  forty changes it says how many there are and asks the user to narrow the
  range with `--since` or to go ahead;
- for each change reads its message, its plan when it has one, its diff
  when the message is not enough, and the decision index as it stood
  before it, and answers missing, covered or not a decision; a change that
  added or amended a record counts as covered;
- counts features, interface details, bug fixes, refactors, docs and
  tests as not a decision, with the measurement's false alarms as examples;
- reports the missing ones, each with the choice, the option it turned
  down when the change shows one, and the change's sha and subject; lists
  apart the changes that only added a record and changed nothing else,
  since such a change points at a choice made elsewhere; and counts the
  covered and not-a-decision changes;
- writes nothing: no record, no draft file, no edit. It says the user turns
  a finding into a record with `kmctl new decision`, and does that only
  when the user asks, for the findings they pick.

kmctl's briefing lists the skill from its folder, as it lists the others;
`docs/how-to/` gets a page on finding unrecorded decisions, and the
`decision candidates` verb's help already names the skill.

The skill-creator evals include a range of this repository with known
answers: a `--since` range holding several of the ten gaps labelled in
`.okf/prototypes/decision-gaps/results/labels.json` and some of its false
alarms, scored against those labels, so the skill's recall and precision
can be compared with the prototype's. The two install pages that count and
list kmctl's skills name the eighth.

It worked when the skill-creator runs show the skill reporting the known
gaps on that range and writing nothing, its description
triggering on asks to find unrecorded decisions and not on asks to write
one, and the package tests and the briefing test list it.

## Problems

- P1: Nothing turns kmctl decision candidates' list into a report of unrecorded decisions a user can act on.

## Goals

- G1: A user can ask their agent which decisions their history made without a record, and get a report they decide on.

## Outcomes

### O1: The decision-gaps skill judges every candidate and reports unrecorded decisions without writing
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `new:packages/kmctl/apm/.apm/skills/decision-gaps/SKILL.md`, `new:packages/kmctl/apm/.apm/skills/decision-gaps/evals/evals.json`, `new:packages/kmctl/apm/.apm/skills/decision-gaps/evals/results.md`, `packages/kmctl/tests/test_apm_package.py`, `packages/kmctl/tests/test_briefing.py`, `new:packages/kmctl/tests/test_decision_gaps_skill.py`, `new:docs/how-to/find-unrecorded-decisions.md`, `docs/how-to/README.md`, `docs/how-to/install-kmctl-with-apm.md`, `docs/how-to/install-the-plugin-and-the-ci-action.md`
- checked by: tests that the skill folder ships in the package and the wheel, its front matter is valid, its body runs kmctl decision candidates and says it writes nothing, the briefing lists it, the install pages count eight skills; the skill-creator evals kept in evals/ with their results; kmctl check
- seen by: operator

## Could invalidate this plan

- none
