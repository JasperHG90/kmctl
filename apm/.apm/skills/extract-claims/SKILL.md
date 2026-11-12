---
name: extract-claims
description: Extract a bundle's claims with a subagent. It hands the .okf/ sections whose text changed since the last pass to the kmctl-claims-extractor agent, which stores the claims through kmctl audit claims, and reports counts only. Use when someone asks to extract, refresh or list the claims the knowledge bundle makes, runs /extract-claims, or wants claims ready before writing checks.
---

# /extract-claims: claims into the store, summaries only

kmctl calls no model here: the `kmctl-claims-extractor` agent reads each
section and submits its verdicts, and `kmctl audit claims submit` validates
and stores them in `.kmctl/audit.sqlite`. You never read a section, write a
verdict or look at a claim yourself; keep only the agents' summaries.

## 1. See what is left

```
kmctl audit claims todo [PATH]
```

`PATH` is the repository (the default), the bundle, or one concept file if
the user named one. It prints the counts and one `pending FILE (N
sections)` line per concept. If nothing is pending, say the claims are up
to date, show `kmctl audit claims list`, and stop. Exit 1 is a refusal: quote
its line and stop.

## 2. Batch by concept

Split the pending files into batches of about 15 sections each, never
splitting a concept.

## 3. Hand each batch to the extractor

Dispatch the `kmctl-claims-extractor` agent with the repository root and
the batch's files. Run batches in parallel when there are several. Each
returns a short summary.

## 4. Report

Run `kmctl audit claims todo [PATH]` again and `kmctl audit claims list
[PATH]`. Show the agents' summaries (sections stored, claims per kind,
sections refused with their refusal line), then the counts both commands
print. If sections are still pending, say which and offer one more pass.
