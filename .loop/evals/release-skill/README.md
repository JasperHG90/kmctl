---
type: eval
title: 'Eval: release-skill'
description: 'Definition of done for release-skill: 3 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T17:47:17+00:00'
slug: release-skill
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 309c4f450a90e742c38aedc3fd96c0f883ba92354111cfb7c245d1e5f6217e3b
  at: '2026-11-14T17:47:17+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: The skill .claude/skills/release/SKILL.md is named release, every -f KEY= it names is a release.yml input, its package values match that input's options, and every path it cites exists.
  Fails when: the name differs, an input or package is made up, or a cited path is missing
- r2: The skill explains why release.yml and release-tag.yml both exist and that apm/apm.yml is kmctl's version source because users pin the APM package to the CLI tag.
  Fails when: either explanation is absent
- r3: .claude/rules/releases.md keeps the no --admin rule and every-release-has-notes, reworded for notes reviewed in the pull request, and names .claude/skills/release/.
  Fails when: a rule is missing, it still says to regenerate notes by hand after publishing as the only path, or it does not name the skill
