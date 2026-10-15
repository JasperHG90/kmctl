---
type: plan
title: 'Plan: new-doc-verb'
description: "kmctl new doc TYPE TITLE creates a docs/ page in its Diataxis folder with a skeleton and adds it to docs/README.md."
slug: new-doc-verb
epic: cli
depends_on: [scaffold-init, knowledge-check]
priority: 5
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T08:08:16+00:00'
---

# new-doc-verb

Relayed from: none

## Intent

`kmctl new doc tutorial|how-to|reference|explanation TITLE` creates the Diataxis folder under docs/ when it is the first page of that type, writes the page with its title and a skeleton for that type, and adds the entry to docs/README.md in the format `kmctl check` reads. It refuses when docs/README.md is missing and says to run `kmctl init`, and never overwrites a page.

Done when tests show each type is created and indexed, `kmctl check` passes afterwards, and the refusals fire.

## Could invalidate this plan

- none
