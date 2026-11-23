---
type: prototype
title: "Bookkeeping merge conflicts"
description: "On a repository where about ten people open pull requests against one bundle, replays past merges and pairs of open pull requests to count the conflicts in log.md, summary.md and the index files, and what stops them."
tags: [prototype]
generated:
  by: process:kmctl/0.14.0
  at: 2026-11-19T09:07:20Z
---

# Bookkeeping merge conflicts

## Question

Pull requests against one bundle keep conflicting in `.okf/log.md`,
`.okf/summary.md` and the `.okf/` index files. How many merges conflict only
in those files, and how many of those conflicts go away when the files are
merged by rule?

## Method

The scripts ran on a private repository that runs kmctl 0.13.0, where about
ten people open pull requests against one bundle. Its name and its raw rows
are left out: `results/` is git-ignored, because the rows name its files and
pull requests.

`scripts/measure.py` replays two sets of merges with `git merge-tree`, which
merges two commits without a working tree.

- **History.** Every commit in which a branch merged `main` into itself. The
  script merges the two parents again, so it sees the conflicts the author
  had to resolve.
- **Open pull requests.** Every pair of open pull requests. A pair that
  conflicts means: after one is merged, the other has to be updated by hand.

Each merge runs three times:

- `git`: git as it is, which is also how GitHub merges. GitHub does not read
  a repository's `.gitattributes` when it merges.
- `union`: `.okf/log.md` and the index files use git's built-in `union`
  merge, which keeps the lines of both sides.
- `union+driver`: also `.okf/summary.md` uses `scripts/merge_summary.py`, a
  merge driver that merges the `checked` block and leaves every other line
  to git. It shows how many summary conflicts are in that block alone.

`scripts/decision_numbers.py` counts the pull requests that add a decision
record, and how many of them were open at the same time as another one.

`scripts/log_lines.py` reads the lines each merged pull request added to
`.okf/log.md`, and counts the pull requests that would still write to the log
if it held lifecycle events only.

Run them from the root of the repository to measure, after
`git fetch origin`. The first two need the GitHub CLI:

```sh
python3 PATH/TO/kmctl/.okf/prototypes/bookkeeping-merge-conflicts/scripts/measure.py
python3 PATH/TO/kmctl/.okf/prototypes/bookkeeping-merge-conflicts/scripts/decision_numbers.py
python3 PATH/TO/kmctl/.okf/prototypes/bookkeeping-merge-conflicts/scripts/log_lines.py
```

## Results

Run on 2026-11-19, with 10 open pull requests.

History, a branch merged `main` into itself, 66 merges:

| | git | union | union+driver |
|---|---|---|---|
| Merges with a conflict | 33 | 26 | 16 |
| ... only in bookkeeping files | 20 | 13 | 3 |
| ... only in `.okf/log.md` and `.okf/summary.md` | 15 | 13 | 3 |
| ... in `.okf/log.md` | 18 | 0 | 0 |
| ... in `.okf/summary.md` | 14 | 14 | 3 |
| ... in an `.okf/` index file | 5 | 0 | 0 |
| ... in any other file | 13 | 13 | 13 |

Open pull requests, every pair, 45 merges:

| | git | union | union+driver |
|---|---|---|---|
| Merges with a conflict | 31 | 31 | 19 |
| ... only in bookkeeping files | 14 | 14 | 2 |
| ... only in `.okf/log.md` and `.okf/summary.md` | 8 | 14 | 2 |
| ... in `.okf/log.md` | 22 | 0 | 0 |
| ... in `.okf/summary.md` | 28 | 28 | 2 |
| ... in an `.okf/` index file | 18 | 0 | 0 |
| ... in any other file | 17 | 17 | 17 |

The bookkeeping files are `.okf/log.md`, `.okf/summary.md` and the `.okf/`
index files. A row can grow from one column to the next: when a fix removes
the index conflict of a merge, that merge moves to the row for the files
that still conflict.

Lines in `.okf/log.md` on `main`, by first word, 321 lines:

| First word | Lines |
|---|---|
| Added | 74 |
| Updated | 71 |
| Verified | 62 |
| Wrote | 15 |
| Review | 12 |
| any other word | 87 |

Decision numbers:

| | Pull requests |
|---|---|
| Merged or open | 86 |
| ... that add a decision record | 20 |
| ... and were open at the same time as another one that adds a decision record | 17 |

Log lines by merged pull request, from `scripts/log_lines.py`, run on
2026-11-23 over 81 merges on `main`:

| | Pull requests | Lines |
|---|---|---|
| Wrote to `.okf/log.md` | 52 | 397 |
| ... a lifecycle event: a concept created, renamed, superseded, deprecated, removed, accepted or verified | 34 | 216 |

So 18 of the 52 pull requests wrote only lines about edits.

All 18 pairs of open pull requests that conflicted in an index conflicted in
`.okf/decisions/index.md`, and 2 of them in `.okf/proposals/index.md` too.
Decision records are numbered, so two new records are always the last two
entries of the index, whatever order kmctl writes the entries in.

Four open pull requests had all added a record numbered 0030. With two such
records in one checkout, `kmctl check` and the strict OKF validation both
passed. `kmctl mv` renamed one of them in under a second.

## Conclusion

- **Half of the merges of `main` into a branch conflicted, and most of those
  needed no judgment.** 33 of 66 merges had a conflict. In 20 of the 33,
  every conflicting file was a bookkeeping file.
- **The summary is the largest part.** 28 of the 31 conflicting pairs of
  open pull requests conflict in `.okf/summary.md`, and 26 of those 28
  conflict only in the `checked` block that `kmctl summary ack` writes.
  [ADR 0048](../../decisions/0048-kmctl-summary-ack-writes-one-file-per-ack-so-branches-merge-without-a-conflict.md)
  follows from that number.
- **The log and the indexes conflict because every change adds a line at
  their end.** 62 of the 321 log lines say that a page was verified, which
  the page's `verified` front matter already records.
- **A git setting does not reach GitHub.** A union merge or a merge driver
  ends these conflicts in a local merge. GitHub still reports them, so only
  a change in what kmctl writes ends them there.
- **A double decision number is common and never reported.** 17 of the 20
  pull requests that added a decision were open next to another one that
  did, and no check reports two records with one number.
