---
type: verdict
title: 'Verdict: kmaudit-package plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of kmaudit-package: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-14T11:37:41+00:00'
slug: kmaudit-package
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach works: the audit modules use kmctl only for okf.py's front matter
helpers (sections.py, lines.py) and their own modules, nothing else in kmctl
imports them, and the spike settles the risk of running both test trees in one
root pytest run. Two problems with the facts need fixing before building. The
removal of `kmctl audit` is split from the agent hooks and skills that call it,
so the outcomes cannot ship apart (p1). The grep contract in r6 catches history
notes in records that were not superseded, plus an unrelated Action message, that
the plan never lists (p2). Neither one means rethinking the plan.

## Checked

- Spike kmaudit-package/1 (README, stdout, stderr, run.json, layouts.py): exit 0.
  Layout E (`__init__.py` in kmaudit's tests/ and fixtures/, relative imports)
  collects both trees cleanly with duplicate basenames, with bare pytest and with
  both paths named. Layouts that do not work are shown failing. The evidence
  answers the listed risk. It only used dummy tests, but the mechanism under
  test (rootdir-relative package names) does not depend on how many tests there are.
- Imports: grep over src/kmctl/claims, judge.py, audit_settings.py and tracing.py
  finds kmctl.okf (split_front_matter, field, BadFrontMatter) in sections.py and
  lines.py, and kmctl.tracing only in judge.py. Outside the moved files, only
  `src/kmctl/__init__.py` imports the audit. This matches the plan's count.
- `git grep "kmctl audit"` over tracked files, read against O4's touches and r6.
- guard.py's prefix check (lines 71-74), the agents' hook front matter, and
  tests/test_apm_package.py:728-741.
- pyproject.toml: the audit extra (ast-grep-py, jmespath, langsmith, tenacity),
  the dev group, and the wheel force-include of skills and agents into kmctl.
- Facts: P1-P3, G1-G2 and O1-O4 against the prose. Apart from p1 and p2, they match.

## Findings

- p1: the removal (O3) and the agent hooks, guard prefix and skill commands
  that depend on it (O4, O1) are split across outcomes that cannot ship apart.
- p2: r6's exclusions catch untouched history notes in accepted decision records
  and the Action's own "kmctl audit:" error prefix. O4's touches leave out the
  skill evals and the two index files that r6 forces to change.

## Notes

- With kmaudit not a dependency of kmctl, a plain root `uv sync` does not install
  the workspace member, so kmaudit's tests would fail to import under r3. The
  build needs kmaudit in the root dev group as a workspace source (or
  `--all-packages` in the gates). That is a build detail, not a risk to the plan.
- O1's touches name src/kmctl/claims/store.py but not the other claims modules or
  ui.html (package data, which r1's wheel install needs). Listing the folder would
  match the prose better. Not a finding on its own.
- After this ticket the skills shipped in kmctl's wheel call `kmaudit`, which has
  no release or install route yet. That is fine on the integration branch, but
  the epic needs an install route before anything reaches main.
