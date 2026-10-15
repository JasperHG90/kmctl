---
type: eval
title: 'Eval: write-docs-skill'
description: 'Definition of done for write-docs-skill: 3 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev33+ge3aeaa855.d20261015
  at: '2026-10-15T11:15:33+00:00'
slug: write-docs-skill
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: fe375eba85393e3df7ba70fd6a362f1550b0331d50bbb30a7085ab1e6689c4b1
  at: '2026-10-15T11:15:33+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: The write-docs skill exists in the plugin with one reference file per Diataxis type.
  Fails when: plugin/skills/write-docs/SKILL.md is missing or any of the four reference files is missing
- r2 (judgment): The skill creates pages only through kmctl new doc and writes only the prose.
  Fails when: SKILL.md tells the agent to create a page file, folder or index entry itself instead of running kmctl new doc
- r3 (judgment): The skill was made with skill-creator and its test prompts are kept beside it, covering one request of each Diataxis type.
  Fails when: no test prompts are kept, fewer than four types are covered, or the skill-creator run's results show a request filed in the wrong folder
