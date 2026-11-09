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

`kmctl decision supersede OLD --by NEW` does, in one change:

- sets the old record's `status` to `deprecated`. kmctl writes only fields the OKF v0.2 spec defines (I4), so it does not touch `decision_status`, which some repositories add by hand;
- appends a dated `## Correction, YYYY-MM-DD` section to the old record saying "Superseded by ADR NEW", linking the new record. It never rewrites the old record's body (`.claude/rules/okf-bundle.md`);
- appends a line to the new record linking back to the old one;
- marks the old entry in the decisions index with "(superseded by ADR NEW)";
- appends a dated line to `.okf/log.md` naming both concept ids, so the change passes the rule that every touched concept is logged.

Done when tests show both records, the index and the log after a supersede, the bundle passes the pinned okf validator in strict mode, and it refuses when either record does not exist or OLD is already deprecated.

## Could invalidate this plan

- none
