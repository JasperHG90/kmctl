---
name: write-checks
description: Write checks for stored claims with a subagent. It hands the claims that have no check to the kmctl-check-writer agent, which tests and stores checks kmctl reruns with no model, then reports counts only. Use when someone asks to write, add or refresh checks for the knowledge bundle's claims, runs /write-checks, or wants the claims from /extract-claims made checkable.
---

# /write-checks: checks into the store, summaries only

kmctl calls no model here: the `kmctl-check-writer` agent writes each check,
and `kmctl audit checks submit` runs it, refuses a weak one and stores the
rest in `.kmctl/audit.sqlite`. You never read a claim, write a step or judge
a check yourself; keep only the agents' summaries.

## 1. See what is left

```
kmctl audit checks todo [PATH]
```

`PATH` is the repository (the default), the bundle, or one concept file if
the user named one. It prints the counts and one `pending FILE (N claims)`
line per concept. If it reports 0 checkable claims, there are no claims
yet: point to `/extract-claims` and stop. If nothing is pending, say the
checks are up to date, show `kmctl audit checks list`, and stop. Exit 1 is
a refusal: quote its line and stop.

## 2. Batch by concept

Split the pending files into batches of about 10 claims each, never
splitting a concept.

## 3. Hand each batch to the check writer

Dispatch the `kmctl-check-writer` agent with the repository root and the
batch's files. Run batches in parallel when there are several. Each returns
a short summary.

## 4. Report

Run `kmctl audit checks todo [PATH]` and `kmctl audit checks list [PATH]`.
Show the agents' summaries (checks stored, reasons, drift found, claims
refused with their refusal line), then the counts both commands print. Name
any drift: it is a claim the code no longer bears out, for a person to look
at. If claims are still pending, say which and offer one more pass.
