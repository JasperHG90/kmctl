---
type: plan
title: 'Plan: okf-fields-invariant'
description: "A test enforces invariant I4 by checking every front matter key kmctl writes is an OKF v0.2 field or handoff_key, and kmctl check stops reporting text GitHub does not render as a link."
slug: okf-fields-invariant
epic: cli
depends_on: []
priority: 14
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev77+gbd4712cf8.d20261015
  at: '2026-10-15T12:25:15+00:00'
---

# okf-fields-invariant

Relayed from: review-hardening round 2 note on `[x](<a>b.md>)`

## Intent

- Invariant I4 (`.okf/manifesto.md`) is still `planned`. A test runs every kmctl verb that writes a concept (`init`, `new` for each kind with and without `--key`, `new doc`, `decision supersede`) in a scratch repository and checks each front matter key it wrote is one the OKF v0.2 spec defines or `handoff_key` (ADR 0009). The allowed keys are listed once, in `src/kmctl/okf.py`, with the spec section each comes from. The manifesto marks I4 enforced by that test, with a log line.
- `kmctl check` reads an angle-bracket target only when the brackets hold no `<` or `>` inside, as CommonMark does, so `[x](<a>b.md>)` is not reported as a broken link.

Done when the I4 test passes and fails if a verb writes an unknown key, and a test shows `[x](<a>b.md>)` is not reported.

## Could invalidate this plan

- none
