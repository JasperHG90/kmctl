---
name: audit
description: Audit a repository's .okf/ knowledge for drift - architecture pages that no longer match the code, decisions a later decision or the code has overtaken, practices whose evidence is gone - and report findings without changing anything. Use when someone asks to audit, review or check the knowledge bundle, the decision log, the architecture docs or the practices, asks "is our documentation still true", or runs /audit, optionally naming one kind ("audit the architecture docs").
---

# /audit: check knowledge against reality, report only

The audit reads; it never edits `.okf/` or `docs/`, and it writes no
`verified` entry (ADR 0005). The person reading the report decides what to fix.

## 1. Get what is due

```
kmctl review due --json
```

Keep the entries in `due` whose id starts with `architecture/`, `decisions/` or
`practices/`. Other kinds (the manifesto, proposals, prototypes, handoffs) are
not audited here; mention how many you left out. An id starting with `docs/`
is a user page in `docs/`, due because its `stale_after` passed or one of its
`sources` changed; list those separately as pages for a person to check, and
do not audit them. Never run `kmctl check --fix` or anything else that writes:
it regenerates `docs/` folder indexes, and the audit changes nothing. If the user named one kind,
keep only that kind. If the user named concepts, use those whether or not
they are due. If nothing is left, say nothing in scope is due and stop.

## 2. Batch by kind

Group the concepts by kind and split each group into batches of at most ten,
so each run reads a manageable amount.

## 3. Hand each batch to the auditor

Read the review skill for the batch's kind, next to this skill in the plugin:
`../architecture-review/SKILL.md`, `../decision-log-review/SKILL.md` or
`../practices-review/SKILL.md`. Dispatch the `kmctl-auditor` agent with the
repository root, the batch (id, path and reasons from step 1) and that review
skill's text. The agent has only Read, Grep and Glob, so it cannot change
anything. Run batches in parallel when there are several.

## 4. Report

Collect the agents' JSON blocks. Show a table per kind with each concept, its
verdict and its one-line summary, `drifted` first, then `unsure`, then
`holds`, followed by the evidence for anything drifted. End with the counts and
the combined JSON block, so a script or the CI action can read it. Do not fix
anything or offer edits unless the user asks.

Then say how a concept leaves `kmctl review due`: a `holds` verdict alone
does not clear it. A drifted concept needs its body fixed first. Once the
person has read a concept and confirms it, `kmctl verify <id> --by
human:<their id>` records that, with `--stale-after 6m` for one listed as
`stale_after passed`. Run it only when they ask you to.
