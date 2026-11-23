---
type: decision
title: "ADR 0049: The log records lifecycle events only"
description: "kmctl and its rules write a line to .okf/log.md only when a concept is created, renamed, superseded, deprecated, removed, accepted or verified, not when it is edited."
tags: [decision]
generated:
  by: process:kmctl/0.15.0
  at: 2026-11-23T08:18:19Z
status: stable
sources:
  - resource: "packages/kmctl/apm/claude/.apm/instructions/okf-bundle.instructions.md"
  - resource: "packages/kmctl/apm/antigravity/.apm/instructions/okf-bundle.instructions.md"
  - resource: "packages/kmctl/src/kmctl/concepts.py"
---

# ADR 0049: The log records lifecycle events only

## Context

kmctl's knowledge rules asked for a line in `.okf/log.md` for every concept a
change touched, edits included (constraint `every-touched-concept-is-logged`).
The reason was a measurement: in the repository the rules came from, 43 of 53
commits that changed a concept left at least one of them out of the log, so
the log read as complete and was not. `kmctl new handoff --key` followed the
same rule and logged each update of a handoff.

Every one of those lines is appended at the end of the log. Two open pull
requests that both append a line therefore conflict there. A union merge
(`merge=union` in `.gitattributes`) settles that in a local merge, but GitHub
does not read `.gitattributes`, so the pull request page still reports a
conflict.

We measured it in a repository where about ten people open pull requests
against one bundle ([Bookkeeping merge
conflicts](../prototypes/bookkeeping-merge-conflicts/README.md)):

- 22 of 45 pairs of open pull requests conflicted in `.okf/log.md`.
- 52 of 81 merged pull requests wrote to the log. 18 of the 52 wrote only
  lines about edits. Of the 397 lines the 52 added, 181 were about edits.

OKF and the okf-skills plugin that kmctl installs already list what belongs in
the log: a concept created, deprecated or superseded, regenerated, or a
verification. Routine edits are left to git history and the concept's own
`generated` field.

## Decision

The log records lifecycle events only, as OKF says.

- **A lifecycle event gets a line.** A concept created, renamed, superseded,
  deprecated or removed, a decision accepted (`draft` to `stable`), or a
  concept verified. The line names each concept by its id, in backticks, as
  before.
- **An edit gets no line.** The rule constraint is now
  `the-log-records-lifecycle-events-only`, in the rules kmctl installs for
  Claude Code and Antigravity and in this repository's own rule.
- **`kmctl new handoff --key` no longer logs an update.** Updating a handoff
  in place is an edit. Creating one still writes `Added`.
- **The other verbs are unchanged.** `kmctl new`, `kmctl init`, `kmctl mv`,
  `kmctl decision supersede` and `kmctl verify` each record a lifecycle event
  and keep their line.

Rejected:

- **Keeping a line per edit.** It is the cause of the conflicts, and git
  history records the same edit with its author and date.
- **Dropping the verify line as well.** It would remove 86 more lines from the
  measured history. But OKF lists a verification as a lifecycle event, and a
  verify is rarer than an edit. Keeping it keeps kmctl in line with the spec
  it builds on.
- **Rebuilding the `.okf/` indexes from their folder, and adding entries in
  sorted order.** All 18 measured pairs that conflicted in an index conflicted
  in `.okf/decisions/index.md`. Decision records are numbered, so two new ones
  are always the last two entries, sorted or not, and they would still
  conflict. A union merge already settles them locally.

## Consequences

- **Fewer pull requests touch the log.** In the measured history, 18 of the 52
  pull requests that wrote to the log would not have, and the log would have
  grown by 216 lines instead of 397.
- **Two pull requests that both create or verify a concept still conflict in
  the log on GitHub.** A union merge settles it locally, as before.
- **The log no longer lists every changed concept.** To find what changed a
  concept, read its git history. A reader who relied on the log for that has
  to switch.
- **Existing lines stay.** The log is append-only, so the lines written for
  edits before this decision stay where they are.
- **The decision index still conflicts** when two pull requests each add a
  decision. This decision does not change that.
