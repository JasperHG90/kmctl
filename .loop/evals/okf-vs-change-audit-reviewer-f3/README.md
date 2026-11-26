---
type: eval
title: 'Eval: okf-vs-change-audit-reviewer-f3'
description: 'Definition of done for okf-vs-change-audit-reviewer-f3: 4 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.4.0
  at: '2026-11-26T22:17:25+00:00'
slug: okf-vs-change-audit-reviewer-f3
signoff:
  signer: delegated:jasperginn@gmail.com/create-eval
  hash: 218b99fc92efb6ede3426123ea012d4ac466e23fdd730001a2ee8eb95ba681d5
  at: '2026-11-26T22:17:25+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: publish --pr leaves a person's comment that quotes the marker alone, posts its own, and replaces its own on the next run
  Fails when: publish edits the person's comment, or posts a second comment of its own on the next run
- r2: publish --pr still creates then replaces its own comment
  Fails when: the existing comment-replacement test fails
- r3: the how-to no longer says the publish job keeps !cancelled() too
  Fails when: the sentence still says it keeps it
- r4: the repo's pre-commit hooks pass on every file
  Fails when: prek run --all-files exits nonzero
