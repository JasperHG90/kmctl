---
type: eval
title: 'Eval: okf-summary-holistic'
description: 'Definition of done for okf-summary-holistic: 5 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T21:49:09+00:00'
slug: okf-summary-holistic
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 1d22206214350135da31b26ff2829b3191d8f3e056fd70d07c840205050dcf76
  at: '2026-10-18T21:49:09+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl init writes .okf/summary.md with the sections The project, How it works, What it has settled and Where it stands, in that order, each with a prompt line, and the prompts say to summarise what the knowledge says and link concepts as evidence, not to list them; kmctl schema summary lists the four sections.
  Fails when: a section is missing, out of order or another name, a prompt asks to link or list each decision, or the schema lists other sections
- r2: The AGENTS.md block's summary duty, the okf-bundle rule (both package copies and .claude/rules/okf-bundle.md) and docs/reference/commands.md say the summary distils what the knowledge says as a whole and that the indexes list the concepts.
  Fails when: any of them still describes the summary as theme-by-theme links to each decision, or lacks the distil wording
- r3: This repository's .okf/summary.md uses the four sections, is at most 500 words, passes kmctl check, and no section is a list in which most items are one decision link each.
  Fails when: a section is missing, it is over 500 words, kmctl check fails, or a section's bullets are mostly single-decision links
- r4 (judgment): A reader can follow the repository's summary as a whole view: it says what kmctl is for, how its parts fit, the principles its decisions settle with their reasons, and where it stands, citing concepts as evidence.
  Fails when: the reviewer finds it lists decisions rather than distilling them, misstates what the bundle says, or leaves out a part of the design
- r5: The full suite and every tier pass.
  Fails when: any test fails
