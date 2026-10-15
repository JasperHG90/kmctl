---
type: verdict
title: 'Verdict: adapt-copied-rules reviewer round 1'
description: 'reviewer verdict for round 1 of adapt-copied-rules: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T08:34:08+00:00'
slug: adapt-copied-rules
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. The three rules about loopctl's internals are gone, the kept rules cite only ADRs 0001 to 0009 and paths that exist or are planned, no aim-managed rule changed, and AGENTS.md drops the ticket note. Gates are green. Two kept rules make claims that do not quite square with the design or with each other; both are plain text fixes, so the label is fix.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests and eval rows r1 to r4 all pass; "stamp green: 0d6ad503e10271cc0097f4b31d672eff651bf1d0d8fd76da19c8c98ada819b69".
- Rows r1 to r4: read tests/test_rules.py. In a scratch copy I appended "loop-harness v2", "ADR 0039", a backticked `.okf/architecture/cli-and-plugin.md` and `src/loop_harness/x.py` to okf-bundle.md and the slug to AGENTS.md; r1, r2, r3 and r4 each failed on the planted defect. The tests assert the rows' fails_when.
- r5 (judgment): `git diff --cached --stat` against main touches only artifact-outputs, cli-interface, cli-version-floor, data-management, diagrams-stay-current, docs-layout, manifesto-invariants, measure-before-ticketing, okf-bundle, schema-versioning and skills-are-thin under .claude/rules/. None is listed in aim.toml. Holds.
- r6 (judgment): read every kept rule in full against .okf/manifesto.md, ADRs 0001 to 0009 and the registered plans. Verbs the rules name (`kmctl check`, `kmctl plugin install`, `kmctl decision supersede`, `--json`) are in registered tickets; the hook claims match ADR 0004, I1 and claude-plugin.md; "neither writes nor checks concept counts" matches knowledge-check.md; docs/README.md as the docs index matches new-doc-verb and scaffold-init; the log line written by verbs matches new-concept-verbs and decision-supersede. manifesto-invariants was kept rather than deleted, which the plan allowed ("likely"); its planned/enforced status matches the manifesto. okf-bundle names loopctl only as the tool that writes .loop/. Holds, apart from f1 and f2.

## Findings

- f1: the `depicts:` field is an extension field nothing in the design names. Either drop the field and say what each diagram depicts in its body, or note that it needs an ADR before a test reads it. Non-blocking: a text fix.
- f2: pick one home for a measurement spike. Either say loop spikes for a ticket go through `loopctl plan spike` and design prototypes go to .okf/prototypes/, or point measure-before-ticketing at docs-layout's prototype rule. Non-blocking: a text fix.
