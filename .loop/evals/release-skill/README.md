---
type: eval
title: 'Eval: release-skill'
description: 'Definition of done for release-skill: 4 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T17:50:46+00:00'
slug: release-skill
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 1556ad7b5827b674b8eb309c027849f5307d54d534b913866a0bbd4b04e2168c
  at: '2026-11-14T17:50:46+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: The skill .claude/skills/release/SKILL.md is named release, every -f KEY= it names is a release.yml input, its package values match that input's options, and every path it cites exists. A cited path holding a <tag> or <package> placeholder matches as a glob.
  Fails when: the name differs, an input or package is made up, or a cited path is missing, or a placeholder path's folder is missing
- r2: The skill explains why release.yml and release-tag.yml both exist and that apm/apm.yml is kmctl's version source because users pin the APM package to the CLI tag.
  Fails when: either explanation is absent
- r3: .claude/rules/releases.md keeps the no --admin rule and every-release-has-notes, reworded so notes are reviewed in the pull request and a gap after publish is added by hand to the published Release (gh release edit --notes-file) and the committed .github/release-notes/TAG.md, keeping the reviewed text, with scripts/release_notes.py fixed when the draft missed a change; it names .claude/skills/release/.
  Fails when: a rule is missing, it says to regenerate published notes from the script, it omits either the Release or the committed file, or it does not name the skill
- r4: After the merge the skill watches the release-tag run (gh run watch / gh run view) and reads its ::warning:: or step summary naming late commits; its gap step adds missing entries by hand to both gh release edit and the committed notes file, and never regenerates published notes.
  Fails when: the skill never names the release-tag run or its warning, or its gap step regenerates notes or edits only one of the Release and the file
