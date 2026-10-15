---
type: eval
title: 'Eval: ci-action'
description: 'Definition of done for ci-action: 6 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev47+g2444f9291.d20261015
  at: '2026-10-15T11:37:28+00:00'
slug: ci-action
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 32ca05137d22a65fa97dd06317a81ef35c147bde5063479a33079376726f21f8
  at: '2026-10-15T11:37:28+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: When kmctl check passes, the action's script exits 0 and writes both reports to the job summary.
  Fails when: the script exits nonzero, or the summary file lacks the check report or the review-due report
- r2: When kmctl check fails, the script exits nonzero.
  Fails when: the script exits 0 on a fixture with a missing index entry
- r3: Concepts due for review do not fail the script.
  Fails when: the script exits nonzero on a fixture where check passes and a concept is due
- r4: A shallow clone is deepened before review due reads history.
  Fails when: after the script runs on a clone made with git clone --depth 1 from a file:// URL, the repository is still shallow or the summary says the history reason was skipped
- r5: If kmctl review due itself crashes, the script exits nonzero and says so in the summary.
  Fails when: a crashing review due leaves the script at exit 0 or the summary silent
- r6: action.yml is a composite action that runs the script, and this repository has a workflow using it.
  Fails when: action.yml is not runs.using composite, does not run the script, or no workflow under .github/workflows/ uses the action
