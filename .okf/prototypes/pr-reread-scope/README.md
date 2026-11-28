---
type: prototype
title: "PR reread scope"
description: "Counts the pages a pull request reread checks with a stable-decisions scope and with every .okf/ and docs/ page that names sources, over 15 merged pull requests."
tags: [prototype]
generated:
  by: process:kmctl/0.18.0
  at: 2026-11-27T10:43:57Z
verified:
  - by: human:jasper
    at: 2026-11-27T20:41:27Z
---

# PR reread scope

## Question

The pull request audit of ADR 0057, `okf-vs-change`, rereads only stable
decisions whose `sources` a pull request changed. Would a scope of every page
under `.okf/` and `docs/` that names sources find more pages, and of which
kind?

## Method

`scope.py REF N` walks the last N pull request merges reachable from REF
(subject `Merge pull request #` or `Merge loop/`). For each it lists the files
the pull request changed (`git diff FIRST_PARENT...HEAD`) and, at the pull
request's head, every markdown page under `.okf/` and `docs/` (handoffs left
out) whose front matter names one of them in `sources`: a file by its path, a
folder as a prefix, URL sources skipped. It counts the pages a stable-decisions
scope finds and the pages the wide scope finds (any status but deprecated or
superseded), by kind. It exits 0 when the wide scope finds more.

Run from the repository root:

```
uv run --with pyyaml python .okf/prototypes/pr-reread-scope/scope.py $(cat .okf/prototypes/pr-reread-scope/ref.txt) 15
```

`ref.txt` holds the commit it ran at; `results.txt` is its output.

## Results

Over the 15 merges from `91b5ab5a` (pull request #80) back to `6de2f9f1`
(#70), the stable-decisions scope found 64 pages and the wide scope 72. The 8
more are docs pages, 2 each in #72, #74, #77 and the loop merge behind #77.
Architecture and practices pages name no sources at that commit, so they add
none; no draft decision a pull request added named a changed file.

## Conclusion

The wide scope finds pages the decisions-only scope misses, all of them docs
pages today. ADR 0060 takes it.
