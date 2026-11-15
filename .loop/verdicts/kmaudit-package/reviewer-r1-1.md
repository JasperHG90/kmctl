---
type: verdict
title: 'Verdict: kmaudit-package reviewer round 1'
description: 'reviewer verdict for round 1 of kmaudit-package: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-14T12:45:02+00:00'
slug: kmaudit-package
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The move itself is sound. kmaudit imports nothing from kmctl, its wheel runs
`kmaudit claims todo` in a venv without kmctl, `kmctl audit` is gone, and
every audit test moved with its test count intact. The out-of-plan
carry-over of stored answers works as claimed on the real store. One
regression blocks: CI no longer runs any audit test (f1). Two plain fixes
remain: a guard for PREVIOUS_HASHES (f2) and stale "kmctl" wording in
kmaudit's docstring, the skills and the review page (f3).

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests and
  integration pass, and eval rows r1 to r6 pass, "stamp green:
  c82a2043ba2aeb52f349239284c143345980de6179ece326eb9060b876231a30".
- r1: test_independent builds the wheel, installs it into a new uv venv,
  asserts `find_spec('kmctl')` is None, exit 0 and that the fixture's
  `tool#parts` section is printed. It matches fails_when.
- r2: an AST walk over every .py under packages/kmaudit for absolute kmctl
  imports, plus the pyproject dependency and extras check. It matches.
- r3: the command itself greps the collection for both trees. It matches.
- r4: test_no_audit asserts `kmctl audit --help` exits 2 with "No such
  command" and no audit Provides-Extra. test_apm_package pins
  `kmaudit guard --allow GROUP`. The guard's prefix check refuses anything
  that does not start with `kmaudit GROUP`, so a `kmctl audit` command is
  refused, though no test names that case.
- r5: I compared test-function counts for each renamed file against
  agent-audit. All are equal, and sections and store gained 1 and 2 tests.
  No other test file under tests/ imported the audit (test_action,
  test_starter and the rest only use the word for the Action and apm).
- r6: a git grep with the plan's exclusions. A multi-line search found one
  miss the row cannot see (f3).
- r7 (judgment): ADR 0043 says the audit left kmctl for kmaudit, a separate
  package in this monorepo with MCP as its main interface. It rejects
  keeping the audit in kmctl, moving kmctl into packages/, and a separate
  repository. It says ADR 0036 to 0042 still stand, read with `kmaudit X`
  for `kmctl audit X`, so nothing is superseded, and ADR 0036 gains a
  correction. That fits the row. `okf_validate.py .okf --strict` reports
  conformant, and `kmctl check` passes.
- The PREVIOUS_HASHES change: I confirmed that agent-audit's
  instructions.py hashes to `a006057ae74b`. I copied the real
  `.kmctl/audit.sqlite` (with sqlite backup) into a scratch git repo beside
  agent-audit's `.okf/` and ran the worktree's `kmaudit claims todo
  --json`. Result: up_to_date 207, pending, new, changed and removed all 0,
  and sections, extractions, claims and checks at 207, 1281, 1281 and 1137
  both before and after. The re-key in Store.refresh updates both
  extractions and sections inside the transaction. No other table stores
  the section key. ui and prune read pending_sections after refresh has
  run. The two new store tests cover carry-over and no carry-over.
- Read the renamed modules' diffs (instructions, store, sections, guard,
  check_instructions, feedback, ui.html), frontmatter.py, the root and
  kmaudit pyproject files, the src/kmctl/__init__.py removal (nothing in
  src/kmctl still names claims, judge, tracing or the audit dependencies),
  README, kmaudit's README, ADR 0043, the manifesto, summary, log,
  overview diagram and table, docs/reference/commands.md, and the skill
  and agent changes.

## Findings

- f1: `.github/workflows/ci.yml` runs the toiminnot pytest action with
  `directory: tests`. Only release.yml runs a bare root `uv run pytest`, so
  until a release no PR check runs claims, checks, judge, guard or UI tests.
  The loop gate runs them, but CI was the other line of defence and this
  change took it away. Make CI collect packages/kmaudit/tests too (a root
  directory, or a second step), and show that the job collects them. I
  want to see the fix because the action's `directory` meaning decides
  whether a one-word change actually works.
- f2: the tuple is right today. But GUIDANCE and PREVIOUS_HASHES now have
  to change together, and only the comment hints at it. Say so where
  GUIDANCE is defined (empty PREVIOUS_HASHES when the guidance changes),
  or pin `instructions_hash()` to a literal in a test next to the tuple so
  a guidance edit fails until someone decides.
- f3: kmaudit/__init__.py lines 3-5; apm/.apm/skills/extract-claims/SKILL.md
  and write-checks/SKILL.md line 8; ui.html lines 566-569, 581, 748, 780,
  843 and 859 (the page's user-facing text names kmctl as the actor). The
  author already changed some of these strings to kmaudit, so this is just
  finishing that job.

## Notes

kmaudit's README gives a `git+...#subdirectory=packages/kmaudit` install
line, and judge.py and steps.py print the same line. It only works once
packages/kmaudit is on main. That matches ADR 0043's note that the epic
adds an install route before main.
