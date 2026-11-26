---
type: prototype
title: "PR audit scope"
description: "Measures whether kmctl review due --base finds the decisions whose sources a merged pull request changed, against a plain sources matcher, over 15 merged pull requests."
tags: [prototype]
generated:
  by: process:kmctl/0.17.1
  at: 2026-11-26T13:01:21Z
---

# PR audit scope

## Question

ADR 0057 scopes an audit on a pull request to the decisions the change may
have outdated. Does `kmctl review due --base REF` (ADR 0055) already find
those decisions, or does the audit need its own match of each decision's
`sources` against the changed files?

## Method

`scope.py` takes a commit and a count. For each of the last 15 pull request
merges reachable from that commit (subject `Merge pull request #` or
`Merge loop/`), it checks out the pull request's head in a throwaway
worktree and compares two lists:

- what `kmctl review due --path WT --base FIRST_PARENT --json` lists, run
  with this checkout's kmctl;
- the stable decisions at the head whose `sources` match a file in
  `git diff FIRST_PARENT...HEAD --name-only`, a file by its path and a folder
  as a prefix.

The run measured `ref.txt` (main at 5ae5e535, pull requests #60 to #75):

```
uv run python .okf/prototypes/pr-audit-scope/scope.py "$(cat .okf/prototypes/pr-audit-scope/ref.txt)" 15 > .okf/prototypes/pr-audit-scope/results.txt
```

It exits 1 when `review due --base` misses a decision the matcher finds.

## Results

`results.txt` holds the per pull request lists and the totals.

- The matcher found 86 hits: a pull request that changed a source of a
  stable decision, counted once per pull request and decision. They cover
  20 distinct decisions.
- `review due --base` listed 11 of the hits, none for a changed source: each
  was listed as `unverified` because the pull request edited the record.
- It missed 75: 59 matched by a file source, 16 by a folder source.
  ADR 0046's folder source `packages/kmctl/` matched in 15 of the 16.
- All 75 misses have one cause. No decision in `.okf/decisions/` has a
  `verified` entry, and `packages/kmctl/src/kmctl/review_due.py` compares
  sources only for a page that has one. For a page without one it keeps
  `unverified` only when the branch changed the page itself.

The path for a verified decision whose source changed is untested here,
since no decision is verified.

## Conclusion

`review due --base` cannot scope the audit while decisions go unverified:
it listed none of the 86 hits for a changed source. ADR 0057 keeps its own
`sources` matcher. A first run of the same script over first-parent
merges, which took in two merges that were not pull requests, gave none of
82.
