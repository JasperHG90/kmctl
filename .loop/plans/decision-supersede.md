---
type: plan
title: 'Plan: decision-supersede'
description: "kmctl decision supersede OLD --by NEW marks the old decision superseded and links the two records both ways."
slug: decision-supersede
epic: cli
depends_on: [new-concept-verbs]
priority: 5
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T08:07:39+00:00'
---

# decision-supersede

Relayed from: none

## Intent

`kmctl decision supersede OLD --by NEW` sets the old record's `decision_status` to `Superseded by ADR NEW` and `status: deprecated`, appends a dated correction section to it that links the new record, adds a link back in the new record, and updates the decisions index. It never rewrites the old record's body (`.claude/rules/okf-bundle.md`).

Done when tests show both records and the index after a supersede, and a refusal when either record does not exist.

## Could invalidate this plan

- none
