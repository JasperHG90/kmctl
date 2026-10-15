---
type: eval
title: 'Eval: repo-uses-apm'
description: 'Definition of done for repo-uses-apm: 6 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.1.1.dev61+g8318eb7a1.d20261015
  at: '2026-10-15T19:08:34+00:00'
slug: repo-uses-apm
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: d5be1b0791f4bc48d26c0e0ed613e697762e6ee0896426d0d55902526df95f84
  at: '2026-10-15T19:08:34+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: apm.yml lists the 13 rules and 3 skills aim managed, pinned to one jasperhg90/skills commit at or after f0813cd, with targets [claude], and apm.lock.yaml pins the full commit and each file's hash.
  Fails when: apm.yml lacks any of the 13 rules or 3 skills, an entry is unpinned or pinned to a commit that does not include the merge of JasperHG90/skills PR 139, targets is not [claude], or apm.lock.yaml is missing or lacks a resolved commit or file hashes
- r2 (judgment): The installed rules and skills sit at the same paths as under aim, each rule keeps its path scoping and has the pinned upstream body, and each skill equals the pinned upstream folder.
  Fails when: any of the 13 rules or 3 skills is missing from .claude/rules/ or .claude/skills/, a rule's paths: list differs from what aim installed (or a rule with none gains one), a rule body differs from the pinned upstream .instructions.md body, or a skill file differs from upstream at the pin
- r3: aim is gone: no aim.toml or aim.lock.toml, no aim: markers or aim header in AGENTS.md, and no file names aim; the guidelines text in AGENTS.md is otherwise unchanged.
  Fails when: aim.toml or aim.lock.toml exists, AGENTS.md has an aim: marker or the aim header line, a tracked file outside .loop/ names agent-integrations-manager or aim as the manager, or the guidelines text changed beyond the markers and header
- r5: The installed python-testing rule keeps this repository's additions, through upstream PR 139: the Test tiers section and the measure-before-marking, run-your-own-test and every-tier-runs-somewhere constraints.
  Fails when: .claude/rules/python-testing.md lacks the Test tiers heading or any of those three constraint names
- r6: tests/test_rules.py reads the upstream-managed rules from apm.yml, and its docstring and pyproject.toml's ruff comment no longer name aim.
  Fails when: tests/test_rules.py reads aim.toml or fails, or it or pyproject.toml names aim
- r4: The other tests still pass.
  Fails when: any test fails
