---
type: eval
title: 'Eval: hermes-workflows-reviewer-f2'
description: 'Definition of done for hermes-workflows-reviewer-f2: 1 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.2.2.dev82+g0ed6ce5f1.d20261019
  at: '2026-10-20T12:50:50+00:00'
slug: hermes-workflows-reviewer-f2
signoff:
  signer: delegated:jasperginn@gmail.com/planner
  hash: 7e79720ca6279439a36df71271cd4952d8af13872b60b81cf15fab392702271e
  at: '2026-10-20T12:50:50+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: No run: line in either Hermes workflow expands a step output; Apply triage reads the response file from a quoted $RESPONSE_FILE set in env
  Fails when: any run: in hermes-interactive.yaml or hermes-issue-triage.yaml contains '${{ steps.', or Apply triage's env lacks RESPONSE_FILE or its run does not quote "$RESPONSE_FILE"
