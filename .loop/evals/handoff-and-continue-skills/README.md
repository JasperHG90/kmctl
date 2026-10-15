---
type: eval
title: 'Eval: handoff-and-continue-skills'
description: 'Definition of done for handoff-and-continue-skills: 6 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev47+g2444f9291.d20261015
  at: '2026-10-15T11:29:35+00:00'
slug: handoff-and-continue-skills
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 9432f32a534b24865a5dd6a59b31a90782009c3134aaadf2140295c8bc0b89e0
  at: '2026-10-15T11:29:35+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl new handoff --key K, with an existing handoff of key K, replaces body and description, refreshes generated.at and stale_after, keeps file name and index entry, appends one log line, and prints the path.
  Fails when: a second file appears, the file name or index entry changes, the dates are not refreshed, log.md gains other than one line, or the path is not printed
- r2: An unknown key creates a new handoff carrying handoff_key.
  Fails when: no new handoff is created, or its front matter lacks handoff_key
- r3: After either path the bundle passes the pinned okf validator in strict mode and kmctl check.
  Fails when: the strict validator or kmctl check exits nonzero
- r4: The /handoff and /continue skills exist in the plugin, and /handoff passes --key only when CLAUDE_CODE_SESSION_ID is set.
  Fails when: either SKILL.md is missing, or /handoff passes an empty --key
- r5 (judgment): /continue offers live handoffs as a multi-select of 3 plus more, summarizes the chosen ones, and acts on nothing before the user answers.
  Fails when: SKILL.md lists handoffs as plain text, offers more than 3 per question, loads a handoff the user did not pick, or takes an action before asking what next
- r6 (judgment): Both skills were made with skill-creator and keep their test prompts beside them.
  Fails when: no test prompts are kept for either skill, or the skill-creator results show a failed prompt
