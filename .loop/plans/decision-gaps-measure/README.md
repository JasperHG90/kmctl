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
inside #53): 31 of the 161 units in the range. Each one becomes a known
missing decision once its record is hidden. Hiding is the same for every
unit, positive or not: the judge and the filter see no path under `.okf/`
or `.loop/`, and no sentence of the subject, message or plan intent that
names an ADR, a decision, a record, `.okf/`, `summary.md`, `log.md`, "next
free" or "the number". A detector that shares nothing with that stripping
scores the visible paths at chance and a separate list of record-keeping
words at AUC 0.64 (spike:decision-gaps-measure/2); the README names that
residue. A positive whose unit changes nothing outside `.okf/` and `.loop/`
only records a choice made elsewhere (ADR 0030) and is reported apart, out
of the recall count. Units that added no decision are negatives; some may
be real gaps, so every judge claim on a negative is read and labelled, a
correct claim counting as a hit, and the false-alarm rate is an upper bound.

A prototype, `.okf/prototypes/decision-gaps/`, holds the scripts, the raw
results and a README concept with the numbers, over a fixed range
(`14799749..ee87e883`, after ADRs 0007 to 0009 and up to the badges merge):

- the filter's recall of hidden positives and how far it narrows the
  history, at each score threshold;
- the judge run on every unit in the range, not a sample: its recall on the
  30 counted positives with a 95% Wilson interval, the share of the 130
  negatives it calls missing, and the precision of those claims after each
  is read and labelled (labelled by Claude, said so in the README);
- the cost and time per judged unit and for the whole range.

The judge runs `claude -p` from an empty temporary folder with a fixed
prompt, no tools, no MCP servers and no project or user settings, so
neither the repository's CLAUDE.md nor a session hook reaches it, and sees
only the unit's stripped text, its visible files and the decision index as
it stood in the unit's first parent. The real skill reads more (the full
diff), so the README presents the judge's numbers as a floor for that.

The bars for building are set before the judge runs: build `kmctl decision
gaps` and the skill when the judge's recall on counted positives is at
least 70% with the Wilson interval's lower end at least 50%, the precision
of its claims on negatives is at least 50%, and judging the whole range
costs at most $10. The README ends with the verdict against these bars and,
if it is build, the threshold and inputs to build with.

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
- checked by: the README states recall and narrowing per threshold, judge recall with its Wilson interval, false-alarm rate and precision, cost per unit and per range, record-only positives apart, and the verdict against the bars set here, each produced by a script in the folder from results in the folder; a test that rerunning the units and score scripts reproduces the README's filter numbers; kmctl check and strict OKF validation
- seen by: operator

## Could invalidate this plan

- Hidden positives may still give the answer away through the files they touch or words left after stripping, making recall look better than on a real gap. Hiding .okf/ and .loop/ for every unit puts visible paths at chance and leaves record-keeping words at AUC 0.64 (spike:decision-gaps-measure/2; spike:decision-gaps-measure/1 could not fail and settles nothing).
