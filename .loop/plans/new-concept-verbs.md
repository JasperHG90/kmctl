---
type: plan
title: 'Plan: new-concept-verbs'
description: "kmctl new creates a decision, practice, proposal, prototype or handoff with its front matter, number and index entry."
slug: new-concept-verbs
epic: cli
depends_on: [scaffold-init]
priority: 5
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T05:10:20+00:00'
---

# new-concept-verbs

Relayed from: none

## Intent

`kmctl new decision|practice|proposal|prototype|handoff TITLE` writes the concept with valid OKF front matter, the next number for decisions, a `stale_after` date for handoffs, a folder with `README.md` for prototypes, and adds the entry to the section index and the root index count. The agent writes the prose; the command writes the structure.

Done when tests show each kind is created, indexed and passes the okf validator.

## Could invalidate this plan

- none
