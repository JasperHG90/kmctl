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

- Invariant I4 (`.okf/manifesto.md`) is still `planned`. It covers what kmctl writes and what it reads, so two tests pin it against one list of allowed keys in `src/kmctl/okf.py`: the OKF v0.2 fields kmctl uses, each with its spec section, plus `handoff_key` (ADR 0009). Nested keys are written as paths: `generated.by`, `generated.at`, `verified[].at`, `sources[].resource`.
  - writes: every kmctl verb that writes a concept or index (`init`, `new` for each kind with and without `--key`, `new doc`, `decision supersede`) runs in a scratch repository, and every front matter key it wrote, nested keys as paths, must be allowed;
  - reads: every front matter read in `src/kmctl/` goes through one accessor, `okf.field(meta, "generated.at")`, which raises when its key is not allowed and returns a list for `[]` paths. Today's reads (`stale_after`, `generated.at`, `title`, `description`, `verified[].at`, `sources[].resource`, `status`, `handoff_key`) move to it. The test parses `src/kmctl/` with `ast` and checks two things: every key passed to `field(...)` is allowed, and no code reads a `front_matter(...)` result in any other way (no `.get`, subscript or `in` on a name bound from `front_matter(...)`, and no `front_matter(...)` passed anywhere but to `field`, a variable, or a return). Other dicts (`plugin.py`'s claude output, `checks.py`) are untouched, because they never come from `front_matter`.
  The manifesto marks I4 enforced by those two tests, with a log line.
- `kmctl check` reads an angle-bracket target only when the brackets hold no `<` or `>` inside, as CommonMark does, and a plain target never starts with `<`, so `[x](<a>b.md>)` is not reported as a broken link. Reference definitions (`[ref]: path`) get the same rule.

Done when the two I4 tests pass and each fails when an unknown key is written or read, and tests show `[x](<a>b.md>)` and `[r]: <a>b.md>` are not reported.

## Could invalidate this plan

- none
