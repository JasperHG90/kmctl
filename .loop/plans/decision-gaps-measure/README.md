---
type: plan
title: 'Plan: decision-gaps-measure'
description: A prototype measures, on this repository's own history, how well a deterministic filter plus an agent judge find merges that made a decision nobody recorded, before kmctl builds the command and skill.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-16T11:35:11+00:00'
slug: decision-gaps-measure
epic: null
depends_on:
- package-direction
priority: null
schema_version: '2.0'
---

# decision-gaps-measure

Relayed from: none

## Intent

The operator wants a kmctl skill that scans git history for decisions
nobody recorded, and said to measure the approach first. The approach: a
command with no model splits history into units (one per ticket merge,
pull request or plain commit, walking merges as `scripts/release_notes.py`
does), drops units already tied to a decision, and ranks the rest by
decision-shaped signals (a dependency added or removed, a new module, files
deleted, workflow or config changes, harness surfaces, words such as
"instead of", "replace", "drop", "no longer"); an agent then reads each
candidate and says whether it made a choice with a rejected alternative
that no existing decision covers.

This repository is its own ground truth. ADRs 0010 to 0045 each arrived in
a known unit on `main` (mostly `Merge loop/SLUG` merges, ADRs 0036 to 0045
inside #53). Hiding each one, by dropping the decision files and index lines
from the unit's diff and the sentences naming an ADR or a decision from its
message and plan, turns it into a known missing decision. Units that added
no decision are the rest.

A prototype, `.okf/prototypes/decision-gaps/`, holds the scripts, the raw
results and a README concept with the numbers, over a fixed range
(`14799749..ee87e883`, after ADRs 0007 to 0009 and up to the badges merge):

- the filter's recall of hidden positives and how far it narrows the
  history, at each score threshold;
- the judge's recall on hidden positives, its "missing decision" rate on a
  fixed-seed sample of negative units, and the precision of those claims
  after each is read and labelled (labelled by Claude, said so in the
  README);
- the cost and time per judged unit.

The judge runs `claude -p` with a fixed prompt, no tools and no project or
user settings, so neither the repository's CLAUDE.md nor the loop's session
hook reaches it, and sees only what the real skill would: the unit's
message, diff stat, the plan's intent when the ticket has one, and the
decisions that existed before the unit. The README ends with a verdict on
whether to build `kmctl decision gaps` and the skill, and with what
threshold and inputs.

It worked when the prototype's scripts rerun to the README's numbers and
the README states recall, narrowing, precision and cost, and the verdict.

## Problems

- P1: Nobody knows whether a filter plus a judge finds unrecorded decisions well enough to build into kmctl.

## Goals

- G1: The decision to build the history scan rests on measured recall, precision and cost.

## Outcomes

### O1: A prototype measures the filter and the judge on this repository's history
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `new:.okf/prototypes/decision-gaps/README.md`, `new:.okf/prototypes/decision-gaps/scripts/units.py`, `new:.okf/prototypes/decision-gaps/scripts/hide.py`, `new:.okf/prototypes/decision-gaps/scripts/leak_check.py`, `new:.okf/prototypes/decision-gaps/scripts/signals.py`, `new:.okf/prototypes/decision-gaps/scripts/judge.py`, `new:.okf/prototypes/decision-gaps/scripts/score.py`, `.okf/prototypes/index.md`, `.okf/log.md`, `.okf/summary.md`, `new:tests/test_decision_gaps_prototype.py`
- checked by: the README states recall and narrowing per threshold, judge recall, false-alarm rate and precision, and cost per unit, each produced by a script in the folder from results in the folder; a test that rerunning the units and score scripts reproduces the README's filter numbers; kmctl check and strict OKF validation
- seen by: operator

## Could invalidate this plan

- Hidden positives may still give the answer away through words left in a ticket merge's subject or plan after the decision sentences are stripped, making the judge's recall look better than it is on a real gap. (spike:decision-gaps-measure/1)
