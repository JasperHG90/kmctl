---
name: extract-claims
description: Extract the claims a folder of markdown docs (an .okf/ bundle, docs/) makes about its repository, through kmaudit's MCP tools. It hands the sections whose text changed since the last pass to the kmaudit-claims-extractor agent, or works through them itself where no agent exists, and reports counts only. Use when someone asks to extract, refresh or list the claims the knowledge bundle or docs make, runs /extract-claims, or wants claims ready before writing checks.
---

# /extract-claims: claims into the store, summaries only

Your model does the reading here; kmaudit has no model of its own.
Whoever reads a section gives its verdicts and
stores them with the kmaudit MCP tool `claims_submit`, which validates them
and keeps them in the folder's own store under `.kmaudit/`. Where the
`kmaudit-claims-extractor` agent exists (Claude Code), it does that reading
and you keep only its summaries, so no claim text fills your context.

Pass every `folder` to the tools as an absolute path. `FOLDER` below is the
folder of markdown docs to audit (`docs`, `.okf`, or any other; the
repository root means `.okf`, the default), or one page in it if the user
named one. Each folder is its own namespace, with its own store. When the
user names no folder, call `claims_todo` on the repository root's `.okf` straight
away, without listing folders first: the tool's refusal says when it is
missing.

## 1. See what is left

Call `claims_todo` with `folder` set to `FOLDER`. Its `counts` say how many
sections are pending and its `concepts` list each concept with pending
sections (`path`, `sections`). If nothing is pending, say the claims are up
to date, show the counts `claims_list` returns, and stop. A tool error is a
refusal: quote it and stop.

## 2. Batch by concept

Split the pending concepts into batches of about 15 sections each, never
splitting a concept.

## 3. Hand each batch to the extractor

Dispatch the `kmaudit-claims-extractor` agent with the repository root and
the batch's concept paths. Run batches in parallel when there are several.
Each returns a short summary.

When the agent is not available (Antigravity, OpenCode), work through each
batch yourself as the agent would: for each concept, call `claims_todo`
with `folder` set to its path, follow the instructions it returns, and pass
your answers to `claims_submit` with `folder` set to the repository root
joined with the returned `namespace`. Fix and resubmit each refused section
once, and keep a summary of sections stored, claims per kind and sections
refused.

## 4. Report

Call `claims_todo` and `claims_list` for `FOLDER` again. Show the summaries
(sections stored, claims per kind, sections refused with their reason),
then the counts both return. If sections are still pending, say which and
offer one more pass.
