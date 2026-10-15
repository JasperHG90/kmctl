---
type: verdict
title: 'Verdict: new-doc-verb plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of new-doc-verb: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T08:10:24+00:00'
slug: new-doc-verb
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

No open risk could break this plan. It is a small file-writing verb whose only outside contract, the docs/README.md entry format, is owned by `kmctl check`, and the plan lists knowledge-check as a dependency, so that format will exist in code before this ticket is built.

## Checked

- The plan, its empty eval, and the plans it touches: scaffold-init (creates docs/README.md only, leaves Diataxis folders to the verb that adds their first page, which matches this plan), knowledge-check (owns the index check), new-concept-verbs (shares the `kmctl new` group; `new doc TYPE TITLE` fits beside `new decision TITLE` as a Typer subcommand), and write-docs-skill (calls `kmctl new doc TYPE TITLE`, same signature).
- The manifesto names the four folders `tutorials/`, `how-to/`, `reference/`, `explanation/`; the plan's type names map to them.
- The repo: src/kmctl/__init__.py holds only the Typer root and `--version`, so there is no existing code the plan's claims could contradict.
- "Could invalidate this plan: none" holds; there is nothing here a spike needs to settle.

## Findings

None.

## Notes

knowledge-check says each page must be listed in "its index" without saying whether that is docs/README.md alone or a per-folder index. This plan assumes docs/README.md alone, which matches scaffold-init. If knowledge-check is built with per-folder indexes, this verb must write there instead; that is a build-time adjustment, not a plan break, since the dependency is built first. The plural type `tutorial` maps to folder `tutorials/` while `how-to`, `reference`, `explanation` do not pluralise; the builder needs that mapping, nothing more.
