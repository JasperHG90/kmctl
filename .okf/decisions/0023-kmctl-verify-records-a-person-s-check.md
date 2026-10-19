---
type: decision
title: "ADR 0023: kmctl verify records a person's check"
description: "kmctl verify writes the verified entry a person's check earns, so a concept or docs page leaves kmctl review due; an agent runs it only on that person's confirmation, never on an audit verdict."
tags: [decision]
generated:
  by: claude-opus/5.5
  at: 2026-10-17T21:30:38Z
status: stable
---

# ADR 0023: kmctl verify records a person's check

- Status: Accepted
- Date: 2026-10-17

## Context

`kmctl review due` lists a concept with no `verified` entry, and a concept or
docs page whose source changed after its last one, or whose `stale_after`
has passed. On 2026-10-17 it listed 24 concepts in this repository, all for
`unverified`, and in an Antigravity session an agent audited one, found it
holds, and could not say how to clear it. Nothing wrote the entry: a person
had to hand-edit YAML whose shape only the okf-bundle rule described, and
neither the briefing nor `kmctl review due` named a way out.

[ADR 0005](0005-audits-report-only.md) keeps audits report only: an audit
never writes a verified stamp, and a person, or an agent the person asks,
acts on findings.

## Decision

- `kmctl verify ID --by human:<id>` appends `{by, at}` to the `verified` list
  of the concept or docs page that `ID` names, as `kmctl review due` prints
  it. `at` is the current UTC time, not a bare date, since a bare date reads
  as midnight and a source committed earlier that day would keep the id due.
  No other line of the file changes, and a concept gets a log line.
- Only a person verifies. `--by` must start with `human:`. An agent runs the
  verb only when the person it names has read the content and asked for it,
  never on an audit verdict alone. Handoffs are never verified.
- A `verified` entry does not clear `stale_after passed`. When that has
  passed, the verb refuses without `--stale-after`, which sets a new one.
- `kmctl review due` ends a listing with a `Next:` line naming the verb. The
  briefing does not: it is within a few tokens of its budget (I3), and it
  already points at `kmctl review due` (loop spikes `verify-verb/1` and `/2`).

Rejected:

- Leave it a hand edit, documented in the rule. An agent then writes YAML by
  hand, and nothing checks the time or the `human:` prefix.
- Let the audit write the entry when a concept holds. ADR 0005 rejected that
  already; the audit judges, a person confirms.
- Name the verb in the briefing. The worst-case briefing test is at 494 of
  500 tokens, and the shortest hint takes it to 505.

## Consequences

- An agent asked to clear a due concept runs one verb instead of editing
  front matter, and the okf-bundle rule and the audit skill tell it when it
  may: after the person confirms, never on its own verdict.
- ADR 0005 and I2 stand. The verb adds a way for a person to act on a
  finding; it gives the audit no new power.
- A source edited but not yet committed when the person verifies counts as
  changed again once it is committed, as before.

## Correction, 2026-10-19

`at` no longer decides what changed after a verification: `kmctl review due`
finds the commit that holds the newest entry and compares from there, and
lists a file edited after it (`edited after verification`), per
[ADR 0032](0032-kmctl-review-due-decides-by-commit-order.md). A verify on a
branch therefore survives a squash or rebase merge. `at` is still written as
the UTC time; it now identifies the entry.
