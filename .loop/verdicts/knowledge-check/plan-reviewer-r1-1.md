---
type: verdict
title: 'Verdict: knowledge-check plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of knowledge-check: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T08:13:02+00:00'
slug: knowledge-check
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach works and the ticket is the right size, but the plan leaves undefined the contract that other tickets build on. It never says what an index entry is (p1). It has a clause about the okf validator that, read literally, removes half its own done criterion for `.okf/` (p2). It is silent on the root index count, which the repository's rules require and a later verb writes (p3). None of these needs a spike. Each is a sentence in the plan.

## Checked

- Read the plan, its empty eval, the ticket state, and the placeholder r1 verdict. This is round 1, so no earlier ids exist.
- Read `.okf/manifesto.md`, ADR 0005, `.okf/index.md`, `.okf/decisions/index.md`, `.claude/rules/docs-layout.md` and `.claude/rules/okf-bundle.md`. docs/ has one index, `docs/README.md`. Each `.okf/` section has an `index.md`. The root index carries a prose count.
- Read the plans that depend on this check or feed it: link-check, prototype-check, new-doc-verb, new-concept-verbs, scaffold-init, ci-action and review-due.
- Read `okf_validate.py` from okf 0.10.1 in the plugin cache. Broken bundle-internal links are warnings that become fatal under `--strict` (check_links, around line 407). It does not check that every concept is listed in an index.
- `src/kmctl/__init__.py` holds only the Typer root and `--version`, so this ticket also sets the pattern later checks extend.

## Findings

- p1: the format of an index entry is a contract with new-doc-verb, new-concept-verbs and scaffold-init, and the plan does not state it.
- p2: the 'does not repeat the okf validator' clause conflicts with checking `.okf/` entries that have no file, and kmctl never runs the validator at runtime or in CI.
- p3: the root index count is in the repository's rules and a later verb writes it, but this plan neither takes it in nor rules it out.

## Notes

The eval has no rows. The builder will meet two edge cases quickly, so they are not findings. First, this repository has no `docs/`, and ci-action runs `kmctl check` here, so a missing `docs/` (or a missing `.okf/`) has to pass or be skipped rather than fail. Second, files inside a prototype folder other than its `README.md` are not concepts to index; prototype-check owns that folder's rule. The `--json` shape is read by ci-action and extended by link-check and prototype-check, so a per-check list of findings with file and reason will save a reshape later.
