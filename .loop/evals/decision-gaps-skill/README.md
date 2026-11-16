---
type: eval
title: 'Eval: decision-gaps-skill'
description: 'Definition of done for decision-gaps-skill: 3 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-16T16:13:50+00:00'
slug: decision-gaps-skill
signoff:
  signer: delegated:jasperginn@gmail.com/implementer
  hash: 87b58522cb895b12779fcfecddb1e77a020c978f2f799b91ff00cda1d0f80b30
  at: '2026-11-16T16:13:50+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl's package ships packages/kmctl/apm/.apm/skills/decision-gaps/SKILL.md with valid front matter (name decision-gaps and a description saying when to use it); its body runs kmctl decision candidates --json, judges every change it lists, reports missing decisions with the choice, the rejected option and the change, and says it writes nothing and leaves records to the user and kmctl new decision; the wheel carries it; the briefing lists it; the verb's help names the skill.
  Fails when: the skill folder or front matter is missing or invalid, the body lacks one of those instructions, the wheel or the briefing leaves it out, or the verb's help does not name it
- r2: The skill was made with the skill-creator skill: evals/evals.json holds its test prompts (at least one asking to find unrecorded decisions, one naming a starting point, and one asking to write a decision record that should not trigger it) with expectations, and evals/results.md records each run's outcome, including that no run wrote to .okf/.
  Fails when: evals.json is missing, malformed or lacks one of those prompt kinds or their expectations, or results.md lacks a result for a prompt or does not say whether .okf/ stayed unchanged
- r3: docs/how-to/ has a page on finding unrecorded decisions that runs the skill and says the user decides; the how-to index lists it; kmctl check and the docs frontmatter tests pass.
  Fails when: the page or its index entry is missing, it implies the skill writes records, or kmctl check reports a finding
