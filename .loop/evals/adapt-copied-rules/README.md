---
type: eval
title: 'Eval: adapt-copied-rules'
description: 'Definition of done for adapt-copied-rules: 6 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T08:28:28+00:00'
slug: adapt-copied-rules
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 6aa684516d730eba27e437041ebbd1b449dd67732db0e0eaf43c4f8c7e2b08b2
  at: '2026-10-15T08:28:28+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: No rule outside the aim-managed set mentions loop_harness, loop-harness, v1 or v2.
  Fails when: any non-aim file under .claude/rules/ contains loop_harness, loop-harness, or v1 or v2 as a word
- r2: Every ADR a non-aim rule cites exists under .okf/decisions/.
  Fails when: a non-aim rule cites ADR NNNN and no .okf/decisions/NNNN-*.md file exists
- r3: Every repository path a non-aim rule cites in backticks exists, or is a planned location or sits under one.
  Fails when: a backticked path in a non-aim rule (text or paths: glob) neither exists nor starts with one of the planned locations the plan lists
- r4: AGENTS.md no longer points at the adapt-copied-rules ticket.
  Fails when: AGENTS.md contains adapt-copied-rules
- r5 (judgment): The aim-managed rules listed in aim.toml are unchanged.
  Fails when: any rule file aim.toml lists differs from its content before this ticket
- r6 (judgment): Each kept rule is true for kmctl: rules about loopctl's internals are deleted, and a kept rule names loopctl only as the tool this repository's tickets run on.
  Fails when: a kept rule states something false about kmctl, or describes loopctl's internals or the loop workflow
