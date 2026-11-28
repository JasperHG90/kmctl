---
type: decision
title: "ADR 0047: Unrecorded decisions are listed by kmctl and judged by a skill that only reports"
description: "kmctl decision candidates lists, with no model, the changes since the newest decision record; the decision-gaps skill judges every one and reports the changes that made a decision no record covers; the user decides which become records."
tags: [decision]
generated:
  by: process:kmctl/0.13.0
  at: 2026-11-16T16:07:23Z
status: stable
sources:
  - resource: "packages/kmctl/src/kmctl/candidates.py"
  - resource: ".okf/prototypes/decision-gaps/"
verified:
  - by: human:jasper
    at: 2026-11-27T09:48:51Z
  - by: human:jasper
    at: 2026-11-27T20:41:20Z
---

# ADR 0047: Unrecorded decisions are listed by kmctl and judged by a skill that only reports

## Context

Changes that make a decision without a record are easy to miss and hard to
find later. On 2026-11-16 the operator asked for a skill that scans git
history for them, said to measure it first, and said what it does with what
it finds: "the skill would report back to the user what it found, and it's
up to the user to make that into decision records or not."
[ADR 0046](0046-kmctl-works-from-code-toward-knowledge-and-kmaudit-from-knowledge-toward-code.md)
puts it in kmctl. [The decision-gaps prototype](../prototypes/decision-gaps/README.md)
measured it on this repository: an agent judging every change found 25 of
30 hidden decisions, 10 of its 17 claims on changes that recorded nothing
were real gaps, and judging all 161 changes cost $3.19.

## Decision

The work is split between a command with no model and a skill.

- **`kmctl decision candidates` lists.** It splits history since the
  newest decision record into changes, one per ticket merge, pull request
  or plain commit, and gives each what a judge needs: the message, the
  ticket's plan, the files, the decisions it added or amended, and
  decision-shaped signals with a score. It orders by score and drops
  nothing. The operator named it: a command that only lists must not
  promise gaps.
- **The decision-gaps skill judges every change and reports.** It reads
  each change, decides whether it made a decision no record covers, and
  reports those with the choice and the option turned down.
- **The user decides.** Nothing writes a record; a finding becomes one
  only when the user turns it into one with `kmctl new decision`.

Rejected:

- Judging only the changes above a score. In the measurement, cutting at a
  score of 2 lost 5 of 30 decisions and saved under $2.
- Letting the skill read `git log` itself. Splitting merges, syncs and
  pull requests that carry tickets is easy to get wrong, and an agent that
  does it pays for it on every run; in kmctl it is done once and tested.
- Drafting or writing records automatically. Precision near 60%, resting
  on labels, means a person must read every finding first.

## Consequences

- A user asks their agent which decisions went unrecorded and gets a
  report; nothing in `.okf/` changes until they act on it.
- The skip list and the ticket and pull request patterns follow this
  repository's loop harness and GitHub. In another repository they match
  nothing, and the verb lists one change per pull request merge or
  first-parent commit.
- `scripts/release_notes.py` keeps its own copy of the history walk, since
  the release script cannot import the installed package; the two can
  drift.
