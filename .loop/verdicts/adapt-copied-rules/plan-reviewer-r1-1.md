---
type: verdict
title: 'Verdict: adapt-copied-rules plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of adapt-copied-rules: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T06:03:44+00:00'
slug: adapt-copied-rules
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach works: each non-aim rule is either rewritten for kmctl or deleted, and the scope is one ticket. But the grep that defines done treats two things as wrong that are right in this repo. Globs for planned directories, and the name of the tool that runs this repo's loop, are both true here. As written, the check would push the builder to strip rule scoping, or to delete or bend rules for no reason. Both fixes are a sentence in the plan.

## Checked

- Read the plan. It has no eval and no spikes, and it lists no risks.
- Compared aim.toml with .claude/rules/. Thirteen rules are aim-managed and twelve are not (adversarial-reviews, artifact-outputs, cli-interface, cli-version-floor, data-management, diagrams-stay-current, docs-layout, manifesto-invariants, measure-before-ticketing, okf-bundle, schema-versioning, skills-are-thin).
- Grepped the twelve for loopctl, loop_harness, loop-harness, v1, v2, proposals, replay and ADR. Hits are in data-management, artifact-outputs, manifesto-invariants, cli-version-floor, cli-interface, skills-are-thin, schema-versioning, okf-bundle, diagrams-stay-current, measure-before-ticketing and docs-layout. adversarial-reviews has none.
- Listed the paths: front matter of every rule against the tree. plugin/, docs/, .github/ and src/kmctl/{cli,hooks,stores,commands,...} do not exist yet. Plans for claude-plugin, write-docs-skill and ci-action are in .loop/plans/.
- Checked that this repo uses loopctl: .loop/config.toml, AGENTS.md's Gates section, and the loop-harness plugin hooks that fire on Bash.

## Findings

- p1: the "path that does not exist here" clause collides with paths: globs for planned directories (premise).
- p2: the loopctl ban collides with this repo running on loopctl (premise).

## Notes

The rules also cite ADR numbers (0010 to 0039) that belong to loop-harness. kmctl's ADRs are 0001 to 0006, so an ADR 0002 citation could survive the grep while pointing at the wrong record. Adding "ADR" to the grep, or checking each cited ADR number against .okf/decisions/, would catch that. Another builder could miss it, but it does not break the plan, so it is a note and not a finding.
