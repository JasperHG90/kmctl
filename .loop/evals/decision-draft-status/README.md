---
type: eval
title: 'Eval: decision-draft-status'
description: 'Definition of done for decision-draft-status: 3 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.2.2.dev1+gd84319696
  at: '2026-10-19T14:32:33+00:00'
slug: decision-draft-status
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: fadf60918f13df2b727ae4da203b2ecb601efd8e2327b15162f41e40f3ff0568
  at: '2026-10-19T14:32:33+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: None of the three okf-bundle rule copies (apm claude source, apm antigravity copy, .claude/rules/okf-bundle.md) still says status is stable or deprecated; each names draft, stable and deprecated.
  Fails when: any copy still has the two-value wording, or lacks draft
- r2: The pinned okf-bundle rule hash in tests/test_apm_package.py matches the new body and its comment names the new ADR, and the package tests pass.
  Fails when: any test in tests/test_apm_package.py fails
- r3 (judgment): A new decision record says a decision may be draft until accepted, how a draft becomes stable (status edit plus a log.md line), and rejects refusing draft in the schema; the rule says the same and tells draft apart from a proposal.
  Fails when: the record is missing, or the rule or record omits how a draft becomes stable
