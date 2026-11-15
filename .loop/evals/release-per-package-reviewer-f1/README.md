---
type: eval
title: 'Eval: release-per-package-reviewer-f1'
description: 'Definition of done for release-per-package-reviewer-f1: 2 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-15T04:48:25+00:00'
slug: release-per-package-reviewer-f1
signoff:
  signer: delegated:jasperginn@gmail.com/implementer
  hash: 509a41c1fb45827e875a589168d626e6a15fc40c234210a4705fe41eed3d103f
  at: '2026-11-15T04:48:25+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: release-tag's late-commit step finds the drafted commit from the Drafted-From trailer on the release branch's own commits for a merge, so a release branch that took an 'Update branch' merge from main and then a later commit still has its late package commits named, with the drafted commit, in the warning and the step summary.
  Fails when: the step reads the update merge as the drafted commit, names no late commit in that case, or leaves the drafted commit out of the warning
- r2: The other cases keep working: a plain merge falls back to the parent of the merge's second parent when no trailer is found, a squash merge reads its own trailer, and a commit with neither warns that the drafted commit could not be found.
  Fails when: any existing release_tag test fails
