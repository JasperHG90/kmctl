---
type: plan
title: 'Plan: new-concept-freshness'
description: "kmctl new takes --stale-after and repeatable --source, so the concepts agents write carry the two fields kmctl review due already reads, and the kmctl block tells agents to use them."
slug: new-concept-freshness
epic: knowledge
depends_on: [init-claude-md-always]
priority: 3
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T17:19:06+00:00'
---

# new-concept-freshness

Relayed from: operator, 2026-10-15: "can they add a stale_after or something?", then "add it", after I proposed `--stale-after` and `--source` on `kmctl new` with no default expiry per kind.

## Intent

`kmctl review due` already reads `stale_after` (OKF v0.2 section 5.5) and `sources` (section 5.1): a concept is due when its `stale_after` has passed, or when a file in its `sources` changed after it was last verified (ADR 0006). But only `kmctl new handoff` writes either field (`stale_after`, 14 days), so on every other concept an agent writes, both reasons can never fire.

- `kmctl new decision|practice|proposal|prototype|handoff` takes `--stale-after`, either a duration (`30d`, `12w`, `6m` for calendar months, `1y` for calendar years) from now or a date (`2027-01-15`, or a full UTC timestamp), written as a UTC timestamp in the form handoffs already use (`%Y-%m-%dT%H:%M:%SZ`). A date in the past is refused. For a handoff it replaces the 14-day default.
- `kmctl new decision|practice|proposal|prototype` take `--source PATH`, repeatable, written as the concept's `sources` list as `- resource: PATH` mappings (the shape `review due` reads and the strict validator accepts without a warning). A path must exist on disk when the concept is written, found the way `review due` finds sources (its `_resolve`: the concept's folder, then the bundle, then the repository root, a leading `/` as bundle-relative, a name with `.md` added), so the check and `review due` never disagree. Git is not needed: a file the agent wrote in this change but has not added yet is accepted, and outside git or in a shallow clone the check still works while `review due` notes it cannot read history. A path that does not exist is refused, naming it. `kmctl new handoff` refuses `--source`, as other kinds refuse `--key`: `review due` never reads a handoff's sources, and the `--key` update rewrites its front matter (round 1 plan review).
- No kind gets a default expiry: a concept tied to its code by `--source` comes due when that code changes, which beats a fixed date.
- The kmctl block's duties in `src/kmctl/scaffold.py` gain one line: when a concept describes code, name it with `--source`; give anything time-bound a `--stale-after`. `kmctl new --help`, the reference page and the write path in `.okf/architecture/overview.md` follow.

Measured on this repository's own bundle: of the concepts `kmctl new` can write here, 0 carry `stale_after` or `sources` except handoffs, so `review due`'s stale and source-changed reasons fire on none of them; the only reason it gives is "unverified".

Done when tests show each verb writes `stale_after` from each duration form and from a date, refuses a past date and an unparseable value with a message naming it, and a handoff's `--stale-after` replaces its default; `--source` writes every path given, in order, as `resource` mappings, accepts an existing file that git does not track yet, refuses a path that does not exist, and is refused on a handoff; and `kmctl review due` then lists the concept as due after a commit that changes that path; the written front matter passes the strict okf validator and the I4 fields test; and the block names both options.

## Could invalidate this plan

- none
