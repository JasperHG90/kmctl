---
type: eval
title: 'Eval: adr-0057-correction'
description: 'Definition of done for adr-0057-correction: 13 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.4.0
  at: '2026-11-26T16:48:54+00:00'
slug: adr-0057-correction
signoff:
  signer: delegated:jasperginn@gmail.com/create-eval
  hash: 0371de8c24dae57ba218d391acdf26802bba868c8ad4750b1e17017b0fd47c6a
  at: '2026-11-26T16:48:54+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: the Correction links ADR 0055 and names kmctl review due --base
  Fails when: the Correction lacks the 0055 link or review due --base
- r2: the Correction gives the measured 86 and links the prototype
  Fails when: the Correction lacks 86 or the pr-audit-scope link
- r3: the prototype holds its script, results and measured commit, and is in the prototypes index
  Fails when: scope.py, results.txt or ref.txt is missing, or the index does not list pr-audit-scope
- r4 (judgment): the Correction says what the audit adds over ADR 0055: whether a decision still holds
  Fails when: a reviewer finds no sentence telling the audit's judgment apart from 0055's list
- r5: the Correction says a fork pull request is skipped with exit 0 on both jobs
  Fails when: the Correction does not say exit 0 or does not name both jobs
- r6: the Correction says the pull request's own workflow file runs on a pull_request event and that fetched context folders stay in the working tree
  Fails when: either point is missing
- r7 (judgment): the Correction does not claim the base checkout guards the API key
  Fails when: a reviewer finds the base checkout presented as guarding the key
- r8: the Correction names okf-vs-change, cites fetch-depth: 0 and links ADR 0046
  Fails when: any of the three is missing
- r9: the accepted text above the Correction is unchanged and the record stays stable
  Fails when: the diff against main removes or changes an existing line, or status is not stable
- r10: the repo's pre-commit hooks pass on every file
  Fails when: prek run --all-files exits nonzero
- r11: the Correction says publish with no report posts nothing and exits 0
  Fails when: the Correction does not cover the no-report case
- r12: the Correction says run_shell stays left out on a pull request and does not say a shell command can read the key
  Fails when: the Correction never names run_shell, or says a shell command can read the key
- r13 (judgment): nothing in the Correction reads as reversing the no-shell rule
  Fails when: a reviewer finds a sentence that weakens or contradicts the accepted no-shell rule
