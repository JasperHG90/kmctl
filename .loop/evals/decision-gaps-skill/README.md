---
type: eval
title: 'Eval: decision-gaps-skill'
description: 'Definition of done for decision-gaps-skill: 3 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-16T16:50:20+00:00'
slug: decision-gaps-skill
signoff:
  signer: delegated:jasperginn@gmail.com/implementer
  hash: 5d8f345f85bcaea310d593f5ba00d1fee5c0ad06012c7cdc0f58cf260170deef
  at: '2026-11-16T16:50:20+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl's package ships packages/kmctl/apm/.apm/skills/decision-gaps/SKILL.md with valid front matter (name decision-gaps and a description saying when to use it); its body runs kmctl decision candidates --json, judges every change it lists, reports missing decisions with the choice, the rejected option and the change, and says it writes nothing and leaves records to the user and kmctl new decision; the wheel carries it; the briefing lists it; it judges in batches and asks to narrow a long range; it lists record-only changes apart; the two install pages count eight skills and name it.
  Fails when: the skill folder or front matter is missing or invalid, the body lacks one of those instructions, the wheel or the briefing leaves it out, or an install page still counts seven skills
- r2: The skill was made with the skill-creator skill, its tests kept as the skill-creator's case folders under evals/ (prompt.md, case.yaml, graders/): one asking to find unrecorded decisions in a named range of this repository that holds labelled gaps and false alarms from .okf/prototypes/decision-gaps/results/labels.json, one asking with no range, and one asking to write a decision record, which must not run kmctl decision candidates; evals/results.md records each run's outcome, the known-answer run's labelled gaps found and false alarms raised, and that no run of the skill wrote to .okf/.
  Fails when: a case folder is missing or malformed, one of those three cases is absent, results.md lacks a case's result or the known-answer counts against the labels, or results.md does not say whether .okf/ stayed unchanged
- r3: docs/how-to/ has a page on finding unrecorded decisions that runs the skill and says the user decides; the how-to index lists it; kmctl check and the docs frontmatter tests pass.
  Fails when: the page or its index entry is missing, it implies the skill writes records, or kmctl check reports a finding
