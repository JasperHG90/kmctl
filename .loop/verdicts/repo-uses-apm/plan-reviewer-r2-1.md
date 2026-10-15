---
type: verdict
title: 'Verdict: repo-uses-apm plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of repo-uses-apm: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T19:08:05+00:00'
slug: repo-uses-apm
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

The approach holds. Spike 3 shows APM 0.33.0 installs all 13 rules and 3 skills at f0813cd with the right paths, the same `paths:` scoping, upstream bodies and byte-identical skills. Two gaps could still break the result. First, the upstream merge the plan waits on is not enforced: the evals pass on a pin that drops the local python-testing text (p1). Second, tests/test_rules.py depends on aim.toml and is not in scope (p2). Both are revisions, not a rethink.

## Checked

- Spike 3 README, stdout and run.json: exit 0. All 16 items installed; `paths:` equals upstream `applyTo`; 6 unscoped rules get no front matter. The kmctl-vs-upstream diffs are as the plan states (pre-existing-issues trailing `%`, python-testing about 50 lines, rule-creator README).
- `gh pr view 139 -R JasperHG90/skills`: state OPEN, mergeCommit null.
- aim.toml and aim.lock.toml: 13 rules and 3 skills, all from jasperhg90/skills; AGENTS.md is in managed_files. AGENTS.md has the header and guidelines markers, plus the routing line 87 naming aim.toml. CLAUDE.md is a symlink to AGENTS.md.
- `git grep -w aim` outside .loop/: AGENTS.md, pyproject.toml:37, tests/test_rules.py. Nothing in .okf/ or docs/.
- tests/: only test_rules.py reads aim.toml. No test reads the name/description front matter of the upstream rules: test_rules.py checks only own rules, and test_init.py checks the packaged repo_rules. Dropping name/description breaks no test.
- .claude/skills/: only the 3 aim skills exist. generate-art appears nowhere else in the repo.
- apm_modules/ holds a .py (generate-art script), but APM gitignores it and ruff respects .gitignore. Pytest finds no test_*.py there. The lock file is a `new:` file, so it is committed as intended.

## Findings

- p1: the PR 139 merge is a prose-only precondition, and the evals accept a pin that loses the local python-testing text.
- p2: tests/test_rules.py reads aim.toml and is outside the plan's scope. Removing aim.toml breaks it, and r3 forces edits to it and pyproject.toml.

## Notes

The ticket does not need splitting. Committing apm.lock.yaml and ignoring apm_modules/ matches APM's model and the plan.
