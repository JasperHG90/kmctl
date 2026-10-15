---
type: plan
title: 'Plan: review-hardening'
description: "Four small robustness fixes the implementation reviews deferred: non-UTF-8 kept files in kmctl init, out-of-range timestamps, link forms kmctl check misreads, and the write-docs grader's hard-coded run names."
slug: review-hardening
epic: cli
depends_on: []
priority: 12
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev77+gbd4712cf8.d20261015
  at: '2026-10-15T11:55:06+00:00'
---

# review-hardening

Relayed from: scaffold-init-reviewer-f5, handoffs-list-reviewer-f3, link-check-reviewer-f4 and write-docs-skill-reviewer-f3, folded into one ticket because each is a few lines.

## Intent

- **kmctl init** (`src/kmctl/scaffold.py`): a kept `.okf/index.md` or `.okf/log.md` that is not UTF-8 no longer crashes init after it wrote other files. The warning check reads the file as UTF-8 and, when it cannot, warns that the kept file is not UTF-8 instead.
- **Timestamps** (`src/kmctl/okf.py`): `as_datetime` returns None instead of raising OverflowError for a value at the edge of the datetime range (for example `0001-01-01T00:00:00+01:00`), so `kmctl handoffs` and `kmctl review due` never crash on one.
- **Link forms** (`src/kmctl/checks.py`), for both the index check and the link check: a target is percent-decoded and loses its `?query` before it is resolved, so `my%20page.md` and `file.md?plain=1` resolve as GitHub renders them; an `<angle bracket>` target (spaces allowed) is read without its brackets; a title in single quotes is allowed after the target; and reference-style definitions (`[ref]: path`) are checked like inline links.
- **write-docs grader** (`plugin/skills/write-docs/evals/grade.py`): each eval in `evals.json` gets a `name` and a `doc_type`, and the grader reads the run folder's type from there instead of a hard-coded table, so a fresh skill-creator run is graded without editing the script.

Done when each fix has a test that failed before it: a non-UTF-8 kept index, an overflowing timestamp in a handoff, each link form in docs/ and in an index, and the grader on runs named only in `evals.json`.

## Could invalidate this plan

- none
