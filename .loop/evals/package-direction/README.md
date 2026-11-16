---
type: eval
title: 'Eval: package-direction'
description: 'Definition of done for package-direction: 2 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-16T11:39:25+00:00'
slug: package-direction
signoff:
  signer: delegated:jasperginn@gmail.com/implementer
  hash: 3a558331194da49e40ce8a0102a3529e4fecaf11e0974dfd80370ee4a29b1fe1
  at: '2026-11-16T11:39:25+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: Decision 0046 exists, its front matter matches the decision schema, its sections are the decision skeleton, it says kmctl works from code and decisions toward docs/ and .okf/ and kmaudit from docs/ and .okf/ toward code, and it links ADR 0043; the root README's kmctl and kmaudit entries each name their direction and the README links decision 0046; CLAUDE.md's routing table links decision 0046.
  Fails when: the decision is missing or off-schema, either direction is missing from it, the ADR 0043 link is missing, a README entry lacks its direction, the README does not link the decision, or CLAUDE.md does not link the decision
- r2: Every README test and the bundle checks pass with the new decision: kmctl check over the repository reports nothing.
  Fails when: any test in test_readmes.py fails or kmctl check reports a finding
