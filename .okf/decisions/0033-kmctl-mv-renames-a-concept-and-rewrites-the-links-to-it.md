---
type: decision
title: "ADR 0033: kmctl mv renames a concept and rewrites the links to it"
description: "kmctl mv OLD NEW renames a concept within its folder, rewrites the links to it in .okf/ and docs/, renumbers a decision title, and lists the lines elsewhere it did not rewrite."
tags: [decision]
generated:
  by: process:kmctl/0.11.0
  at: 2026-10-19T19:49:49Z
status: stable
sources:
  - resource: "src/kmctl/mv.py"
---

# ADR 0033: kmctl mv renames a concept and rewrites the links to it

- Status: Accepted
- Date: 2026-10-19

## Context

kmctl had no verb to rename a concept (issue #36). A rename by hand is a
`git mv` plus edits in several places: the section's `index.md` entry,
every link to the concept in `.okf/` and `docs/`, a decision's `ADR NNNN`
in its `title` and `#` heading, the summary's `checked.against`
([ADR 0027](0027-the-bundle-opens-with-a-summary-that-kmctl-keeps-in-step.md)),
and paths outside the bundle such as `AGENTS.md` and skills. Renumbering
the decision log of dlx-internal/dlx took a script that rewrote about 25
files and a second one to check them, and it still shipped three wrong
titles. `kmctl check` leaves links inside `.okf/` to the okf validator,
which only warns on a missing target.

## Decision

- `kmctl mv OLD NEW` takes two concept ids, as `kmctl review due` prints
  them, in the same folder. It renames the file (a prototype's folder),
  rewrites every link to it in `.okf/` and `docs/` the way `kmctl check`
  finds links (outside code, anchor kept), and writes a `log.md` line that
  names each concept it touched. `log.md` itself is history and is never
  rewritten.
- For a decision whose number changes, it writes the new number in the
  record's `title` and `#` heading and in the `ADR NNNN` text of each link
  to it. It writes the new id into the summary's `checked.against`.
- It refuses when `NEW` exists, leaves the folder, is not kebab-case, or,
  in `decisions/`, has no four-digit number or one another record holds.
  A run of decisions is renumbered one move at a time from the lowest
  free number upward, so no step ever needs a number that is taken.
- It does not rewrite text outside `.okf/` and `docs/`, or prose and code
  inside them; it lists each line that still holds the old id, file name
  or `ADR NNNN`, for a person or agent to fix or keep.

Rejected:

- `kmctl decision renumber`, a verb for decisions only. Renaming a
  practice, proposal or prototype needs the same link rewriting, and a
  renumber is a rename whose new name has another number.
- Leave renames to `git mv` and `kmctl check`. `kmctl check` does not
  check links inside `.okf/`, so a missed link passes, and nothing checks
  a title against its file name: that is how the dlx renumbering shipped
  wrong titles.
- Rewrite every mention, in prose and outside the bundle. Prose such as
  "unlike ADR 0007" or a path in a script may mean the old record or may
  not, and a wrong rewrite is silent; a listed line costs a look.
- Swap or shift numbers in one call (a batch mode). Moving from the lowest
  free number upward does a run with the one-step verb, and a batch would
  need a plan for every partial failure.

## Consequences

- A rename or renumber is one command per concept, and `kmctl check` and
  the okf validator pass after it when every link was a markdown link.
- The lines it lists still need a person or an agent; for a renumbered
  decision in a large bundle that can be many, since prose cites decisions
  as `ADR NNNN`.
- A concept cannot change folder or section with it: that changes what
  the concept is, not its name.
- The move is a plain rename, not `git mv`: `git status` shows a deleted
  file and an untracked one until both are staged, and a rename after.
