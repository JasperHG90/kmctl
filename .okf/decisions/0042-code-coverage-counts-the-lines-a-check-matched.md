---
type: decision
title: "ADR 0042: Code coverage counts the lines a check matched"
description: "Each check step records the lines it matched, and kmctl audit coverage and the code view of kmctl audit ui count a line of code as covered when a stored check matched it on its last run; code is what a check may read, without tests, fixtures, evals, lock files and installed packages."
tags: [decision, audit]
generated:
  by: claude-opus/5.5
  at: 2026-11-12T12:30:00Z
status: draft
sources:
  - resource: "src/kmctl/claims/coverage.py"
  - resource: "src/kmctl/claims/steps.py"
  - resource: "src/kmctl/claims/ui.py"
  - resource: "src/kmctl/claims/ui.html"
---

# ADR 0042: Code coverage counts the lines a check matched

## Context

The audit page of
[ADR 0041](0041-people-review-claims-and-checks-on-a-local-page-and-their-feedback-goes-back-to-the-agents.md)
shows the bundle from the documents' side: which sentences have claims and
whether their checks hold. It cannot answer the other question: which code
does the knowledge say anything about? A step kept only a display string of
what it saw, capped at five matches, with line numbers for grep and code
steps alone, so no view of the code could be built from the store.

## Decision

Each step's result keeps the spans it matched, 1-based and inclusive: every
grep line, the whole node a code pattern matched, the def, class or
assignment a definition step found (from the `def` line, so decorators do
not count), and each import statement. File, query
and help steps test whole files and keep none; `check_reads` already
records the files they read.

A line of code is covered when the last run of a stored check matched it.
A file a check only reads is "read", counted apart. A run whose files have
changed since is stale, and its lines do not count until `kmctl audit
checks run` reruns it, since they may have moved. A line is marked failing
when a check that matches it fails (drift, or fails), not when its run was
skipped for a missing extra. The code is every file a check may read that
is on disk, without tests, fixtures, evals, lock files and the folders
harnesses install packages into (`.github/skills/`, `.github/agents/`,
`.agents/`, `.opencode/`); blank lines do not count. `kmctl audit coverage` prints the
share and the largest files no check matches, with `--json`, and `kmctl
audit ui` gains a code view: each file with its matched lines marked, the
claims behind a line, and links from a claim's check to the lines it
matched.

Rejected:

- **Covered when a check reads the file.** One grep for a constant would
  cover a 600-line module, and a help step reads its whole package: on this
  repository 104 of 107 code files are read by some check.
- **Covered only where a mutation trial was caught.** The most honest about
  what would notice drift, but mutations touch few lines, so most matched
  code would never count. The confidence part of each claim already shows
  the trials.
- **Only `src/` and `scripts/` as code.** Leaves out the APM package's
  skills and agents and the workflows, which many claims are about.

## Consequences

- On 2026-11-12, after `kmctl audit checks run --all` recorded the spans,
  11.4% of this repository's code lines were matched by a check (2,103 of
  18,528).
- Checks stored before this change have no spans until they run again;
  `kmctl audit checks run --all` fills them.
- A step keeps at most 200 spans, so a broad pattern cannot bloat the store.
