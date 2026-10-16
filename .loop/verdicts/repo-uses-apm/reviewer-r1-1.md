---
type: verdict
title: 'Verdict: repo-uses-apm reviewer round 1'
description: 'reviewer verdict for round 1 of repo-uses-apm: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-16T10:49:57+00:00'
slug: repo-uses-apm
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The switch from aim to APM does what the plan says. apm.yml lists the 13 rules and 3 skills, all pinned to 7a5e072, which is the merge commit of JasperHG90/skills PR 139 (confirmed with gh: state MERGED, mergeCommit 7a5e072). Installed rules keep their path scoping and have the upstream bodies, and the skills match upstream byte for byte. aim is gone. The only finding is one stale comment, which does not block.

## Checked

- Gates: `loopctl gate stamp` from the worktree passed: lint, format, tests, integration, rows r1, r3, r4, r5 and r6. Stamp a098c484b33e60ee1be66418d1acccc17dc8da47c09788db715c8261df4a4deb. I also ran `uv run pytest -q` (455 passed), `uv run ruff check` (clean) and `uv run ruff format --check` (85 files already formatted) myself.
- r2 (judgment): I cloned JasperHG90/skills and checked out 7a5e072. For each of the 13 rules I removed the front matter and diffed the body against the installed file: all 13 match. I compared each rule's `paths:` with `git show main:.claude/rules/<name>.md` and with upstream `applyTo`. All 9 scoped rules keep the same globs in the same order. The 4 unscoped rules (interface-audience, plain-language, pre-existing-issues, uv-installer, prek-code-quality: these 5 had no paths on main) have none now. `diff -r` of agent-creator, rule-creator and generate-art against upstream skills/tools/ shows no difference. The python-testing diff against main touches only front matter, so the local Test tiers text survives through upstream.
- apm.lock.yaml: every dependency has resolved_commit 7a5e072. I recomputed all 23 deployed_file_hashes against the files in the tree, and none differ.
- Eval tests: r1 asserts the exact set of entries, the pin on every entry, targets [claude], and the lock commit and hash format. r3 checks the missing files, the AGENTS.md markers and header, a sha256 of the guidelines text, and a regex over `git ls-files` outside .loop/. r5 asserts the heading and the three constraint tags. r6 greps test_rules.py and pyproject.toml, and test_rules.py's `_apm_managed` now reads apm.yml, so the own-rules tests run against the right set. Each test fails when its row's fails_when holds.
- `git grep -i -E '\baim\b|agent-integrations'` outside .loop/ finds only tests/test_repo_apm.py, which has to name it. CLAUDE.md is still a symlink to AGENTS.md. AGENTS.md's routing line now points at apm.yml. pyyaml is already a runtime dependency, so test_rules.py's new import is backed.

## Findings

- f1 (docs, non-blocking): tests/test_repo_apm.py:19 still says that until PR 139 merges, PINNED is the PR's head commit. The PR has merged and the pin is the merge commit, so the sentence should go. Change the comment to say PINNED is the merge commit.

## Notes

The unscoped-rule count above has a slip. There are 5 unscoped rules, not 4: interface-audience, plain-language, pre-existing-issues, uv-installer and prek-code-quality. All 5 stay unscoped, and 8 scoped rules keep their globs.
