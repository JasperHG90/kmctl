---
type: decision
title: "ADR 0051: kmctl init sets a union merge for the log and the indexes"
description: "kmctl init writes merge=union for .okf/log.md and the .okf/ indexes to .gitattributes, so a local merge keeps the lines both branches added."
tags: [decision]
generated:
  by: process:kmctl/0.15.0
  at: 2026-11-24T08:42:29Z
status: stable
sources:
  - resource: "packages/kmctl/src/kmctl/scaffold.py"
---

# ADR 0051: kmctl init sets a union merge for the log and the indexes

## Context

Every pull request that adds a concept appends a line to `.okf/log.md` and an
entry to an index. Two open pull requests therefore change the same place
at the end of each file, and git stops on it.
[ADR 0049](0049-the-log-records-lifecycle-events-only.md) makes fewer pull
requests write to the log, but two that each create a concept still
conflict there, and two that each add a decision always conflict in
`.okf/decisions/index.md`: both new records are the last entries.

Git's built-in union merge (`merge=union` in `.gitattributes`) keeps the
lines of both sides. In the repository we measured ([Bookkeeping merge
conflicts](../prototypes/bookkeeping-merge-conflicts/README.md)), it took the
pairs of open pull requests that conflict in `.okf/log.md` from 22 of 45 to
0, and in an index from 18 to 0. That repository set the lines by hand.
`kmctl init` did not write them, so every other repository that uses kmctl,
kmctl's own included, still stops on these files in a local merge.

## Decision

`kmctl init` gives `.okf/log.md`, `.okf/index.md` and `.okf/*/index.md` a
union merge in `.gitattributes`:

- with no `.gitattributes`, it writes one with a comment and the three
  lines;
- a kept `.gitattributes` gets, after its own text, only the lines for the
  patterns it gives no `merge` attribute, so a driver the user chose stays;
- a second run changes nothing, and `kmctl update` after an upgrade adds the
  lines to a repository set up before this decision.

kmctl's own repository carries the same lines.

Rejected:

- **A merge driver of kmctl's own** that sorts the entries or rebuilds the
  indexes. A driver needs a `git config` entry on every clone, which init
  cannot set for others, and the union merge already ends these conflicts.
- **Only documenting the lines.** Each team would have to find the page and
  copy three lines by hand. init already writes the files those lines are
  for, so it can write the lines in the same run.
- **A `kmctl doctor` check instead.** It would report the missing lines but
  leave the conflict until someone acts; init can just write them.

## Consequences

- **A local merge keeps both sides' log lines and index entries.**
  `git merge origin/main` no longer stops on these files.
- **GitHub still reports the conflict.** GitHub does not read
  `.gitattributes`, so a pull request page can show a conflict that a local
  merge settles. The comment init writes says so.
- **A union merge never drops a line, and never checks one.** Two branches
  that each change the same index entry keep both versions. `kmctl check`
  still reports a link that no longer resolves, and two decision records
  with the same number.
- **init now changes one more kept file.** It adds lines to a kept
  `.gitattributes`, and touches nothing else in it.
