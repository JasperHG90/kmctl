---
type: plan
title: 'Plan: knowledge-check'
description: "kmctl check fails when an index disagrees with its folder in docs/ or an .okf/ section."
slug: knowledge-check
epic: cli
depends_on: []
priority: 6
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T05:10:21+00:00'
---

# knowledge-check

Relayed from: none

## Intent

`kmctl check` reports, with a non-zero exit when any fails, that every index agrees with its folder. This ticket defines the index format that every kmctl verb writing an index follows (scaffold-init, new-concept-verbs, new-doc-verb):

- **Which index:** docs/README.md for every page under docs/; each `.okf/` section's `index.md` for the concepts in that section; the root `.okf/index.md` for the sections.
- **An entry** is a markdown list item whose first link is a relative link to a page in that folder or below. For `.okf/prototypes/`, the page is a prototype's `README.md`; other files in a prototype folder are not concepts. External links and anchors are not entries.
- **Counts:** kmctl neither writes nor checks concept counts. They are prose that no script can keep right, and an index's links already say what it holds.

Checks: every page or concept is an entry in its index; every entry's file exists; every section folder is linked from the root index. A missing `docs/` or `.okf/` is skipped and reported as skipped, not failed, so a repository with only one of them passes.

kmctl checks index entries itself even in `.okf/`, because kmctl does not run the okf validator (the validator is a test-only copy here). It does not repeat what the validator checks about front matter and spec conformance. General link checking is link-check's.

`--json` prints a list of findings, each with check, file, line and message, so link-check and prototype-check add their own check names to the same list.

Done when tests cover a passing and a failing fixture for a missing entry, an entry with no file, and a section not linked from the root, plus a repository with no docs/ folder.

## Could invalidate this plan

- none
