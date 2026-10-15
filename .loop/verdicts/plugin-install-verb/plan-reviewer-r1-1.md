---
type: verdict
title: 'Verdict: plugin-install-verb plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of plugin-install-verb: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T08:19:37+00:00'
slug: plugin-install-verb
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The spike's evidence is sound for what it tested: at user scope, the install fails until the scaccogatto marketplace is added, then pulls okf and is idempotent. The plan is not ready for two reasons. The project scope that the done-when test uses is untested (p1). And the plan never says where kmctl's own marketplace comes from, which decides whether "same release" holds and what idempotence and status mean (p2). Neither forces a rethink, so the verdict is fail, not reject.

## Checked

- Read the plan, the empty eval rows, and spike plugin-install-verb/1 (README outcome, stdout.txt, run.json, files/cross-mkt.sh). The stdout backs the outcome: exit 1 with "Is the scaccogatto marketplace added?" before the add, then "(+ 1 dependency: okf)", then "already installed". Every install in the script used --scope user.
- Read ADR 0001 and 0003 and the claude-plugin plan this ticket depends on (plugin/ and the root marketplace are not built yet).
- Checked claude 2.1.300 help. `plugin install` has --scope user|project|local, --json, and --marketplace <source>, which adds a missing marketplace at user scope only. `plugin marketplace add` has --scope and --json. `plugin list` has --json, so status can parse it.
- pyproject.toml: a uv_build wheel with no plugin data packaged.

## Findings

- p1: project scope is untested, and the done-when test runs at project scope. Spike question stated in the claim.
- p2: the source of kmctl's marketplace (GitHub HEAD, a wheel path, or a git ref) is undecided. That choice decides the same-release contract, idempotence, and status. Spike question stated in the claim if a pinned ref is chosen.

## Notes

The eval has no rows yet. The done-when sentence (okf installed, second run a no-op) maps to rows the plan should add. One ticket is still the right scope; two risks do not call for a split.
