---
type: verdict
title: 'Verdict: kmaudit-package plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of kmaudit-package: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-14T11:39:57+00:00'
slug: kmaudit-package
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

Both round 1 findings are fixed and I found no new risk that could break the plan. O3 now removes the group and, in the same outcome, moves the agents' hook, the guard prefix, the skill and agent command text, the skill evals.json files and the hook-pinning test to `kmaudit`, so no state leaves a hook calling a missing command. r6 now leaves out `.okf/decisions/` and the Action's refusal text, and every other tracked file that says `kmctl audit` is either moved code or listed in O3's or O4's touches. The spike still settles the one listed risk.

## Checked

- Ran `git grep -l -e "kmctl audit" -e "kmctl\[audit\]"` minus r6's exclusions. Every hit is one of three kinds: moved code (src/kmctl/claims/, judge.py, audit_settings.py, tracing.py, the group in __init__.py), audit tests that move (tests/test_audit_*.py, test_claims_cli.py, test_checks_cli.py, test_judge.py, fixtures/audit_repo.py), or a file in O3's or O4's touches (agents, SKILL.md, evals.json, results.md, commands.md, manifesto, the three architecture files, test_apm_package.py). action.yml and the install how-to are excluded only for the Action's own refusal.
- Imports: kmctl.okf is used only in claims/sections.py and lines.py (split_front_matter, field, BadFrontMatter); kmctl.tracing only in judge.py and in the `audit judge` command body in __init__.py, which leaves with the group. briefing.py, doctor.py, plugin.py and tests/conftest.py do not use the audit modules. pyproject's only audit entry is the extra.
- Every kmctl test that imports `fixtures.audit_repo` is an audit test that moves, so after the move kmctl's tests/ no longer need that fixture. The spike's layout E (with `__init__.py` files and relative imports in kmaudit's tests) holds either way.
- Spike kmaudit-package/1 README outcome, already checked in round 1. It answers the listed risk.
- Facts against prose: P1-P3, G1-G2, O1-O4. The `needs` chain (O2, O3 on O1; O4 on O3) matches the prose. O1 is the one behaviour that ships alone. O2 and O3 depend on it.
- Eval rows r1-r7 against the outcomes: r4 covers O3's hook and guard change, and r6 matches O4's check.

## Findings

- p1: resolved. O3 holds the removal together with everything that calls the removed command, and r4 checks the hook and the guard.
- p2: resolved. r6 leaves out decision records and the Action's refusal, and O4's touches list results.md, the architecture index and overview, and the new ADR.

## Notes

- O1's touches name the source files that move but not the test files leaving tests/ (test_audit_*.py, test_claims_*.py, test_checks_cli.py, test_judge.py, fixtures/audit_repo.py). No other outcome touches them, so this does not change any split decision. It is a gap to keep in mind while building, not a finding.
- The `kmctl audit` group body uses kmctl CLI helpers (`_refuse`, INSTALL text naming `kmctl[audit]`). kmaudit's CLI needs its own copies, and the install hint must name kmaudit. r6's grep catches any `kmctl[audit]` text left behind.
- The skills and agents shipped in kmctl's wheel will call `kmaudit guard`, which users cannot install yet. The plan accepts this for the integration branch only.
