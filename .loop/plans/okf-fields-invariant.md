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

- Invariant I4 (`.okf/manifesto.md`) is still `planned`. It covers what kmctl writes and what it reads, so two tests pin it, both against one list of allowed keys in `src/kmctl/okf.py` (the OKF v0.2 fields kmctl uses, each with its spec section, plus `handoff_key` from ADR 0009, and the nested `generated.by`/`generated.at` and `verified[].at`):
  - writes: every kmctl verb that writes a concept or index (`init`, `new` for each kind with and without `--key`, `new doc`, `decision supersede`) runs in a scratch repository, and every front matter key it wrote must be allowed;
  - reads: a scan of `src/kmctl/` finds every front matter key the code reads (string keys passed to `.get(...)` or `[...]` on a front matter mapping, found by parsing the source with `ast`), and each must be allowed.
  The manifesto marks I4 enforced by those two tests, with a log line.
- `kmctl check` reads an angle-bracket target only when the brackets hold no `<` or `>` inside, as CommonMark does, and a plain target never starts with `<`, so `[x](<a>b.md>)` is not reported as a broken link. Reference definitions (`[ref]: path`) get the same rule.

Done when the two I4 tests pass and each fails when an unknown key is written or read, and tests show `[x](<a>b.md>)` and `[r]: <a>b.md>` are not reported.

## Could invalidate this plan

- none
