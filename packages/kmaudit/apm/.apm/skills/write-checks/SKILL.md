---
name: write-checks
description: Write checks for the claims kmaudit stored, through kmaudit's MCP tools. It hands the claims that have no check to the kmaudit-check-writer agent, or works through them itself where no agent exists, so each gets a tested check kmaudit reruns with no model, then reports counts only. Use when someone asks to write, add or refresh checks for the knowledge bundle's or docs' claims, runs /write-checks, or wants the claims from /extract-claims made checkable.
---

# /write-checks: checks into the store, summaries only

kmaudit calls no model here. Whoever writes a check tests it with the
kmaudit MCP tool `checks_try` and stores it with `checks_submit`, which runs
it, refuses a weak one and keeps the rest in the folder's own store under
`.kmaudit/`. Where the `kmaudit-check-writer` agent exists (Claude Code), it
does that work and you keep only its summaries, so no claim or step fills
your context.

Pass every `folder` to the tools as an absolute path. `FOLDER` below is the
folder of markdown docs to audit (`docs`, `.okf`, or any other; the
repository root means `.okf`, the default), or one page in it if the user
named one. Each folder is its own namespace, with its own store. When the
user names no folder, call `checks_todo` on the repository root's `.okf` straight
away, without listing folders first: the tool's refusal says when it is
missing.

## 1. See what is left

Call `checks_todo` with `folder` set to `FOLDER`. Its `counts` say how many
claims are checkable and pending, and its `concepts` list each concept with
pending claims (`path`, `claims`). If it reports 0 checkable claims, there
are no claims yet: point to `/extract-claims` and stop. If nothing is
pending, say the checks are up to date, show the counts `checks_list`
returns, and stop. A tool error is a refusal: quote it and stop.

## 2. Batch by concept

Split the pending concepts into batches of about 10 claims each, never
splitting a concept.

## 3. Hand each batch to the check writer

Dispatch the `kmaudit-check-writer` agent with the repository root and the
batch's concept paths. Run batches in parallel when there are several. Each
returns a short summary.

When the agent is not available (Antigravity, OpenCode), work through each
batch yourself as the agent would: for each concept, call `checks_todo`
with `folder` set to its path (and `brief: true` after the first round),
follow the instructions it returns, test each draft with `checks_try` and
store the answers with `checks_submit`, both with `folder` set to the
repository root joined with the returned `namespace`. Fix and resubmit each
refused answer once, and keep a summary of checks stored, reasons, drift
found and claims refused.

## 4. Report

Call `checks_todo` and `checks_list` for `FOLDER` again. Show the summaries
(checks stored, reasons, drift found, claims refused with their reason),
then the counts both return. Name any drift: it is a claim the code no
longer bears out, for a person to look at. If claims are still pending, say
which and offer one more pass.
