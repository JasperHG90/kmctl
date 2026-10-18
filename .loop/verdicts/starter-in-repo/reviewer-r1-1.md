---
type: verdict
title: 'Verdict: starter-in-repo reviewer round 1'
description: 'reviewer verdict for round 1 of starter-in-repo: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-18T10:21:57+00:00'
slug: starter-in-repo
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan says. copier.yml sits at the root with `_subdirectory: starter`. starter/ matches kmctl-starter's template/ except for the planned `exclude:` in .pre-commit-config.yaml (checked with diff -r). The validator now accepts a, b and rc tags. `release.py set` moves kmctl_ref's default, lists copier.yml among the files it wrote, and refuses without writing anything when the default is missing. release.yml stages copier.yml, and CI gains a starter job. Every eval row's test asserts its fails_when. My stamp is green. Two small doc fixes remain, neither blocking.

## Checked

- My `loopctl gate stamp` from the worktree: lint, format, tests and integration all pass, and so do eval rows r1, r2, r3, r5, r6, r7, r8 and r9. Stamp green, 3e2a643832016c0c0644674602d416ce7954e70d47d6609a75f2054313e0fd0b.
- Ran `diff -r starter /home/vscode/kmctl-starter/template`: only .pre-commit-config.yaml differs, by the exclude and its comment. copier.yml against kmctl-starter's: only the header comment, `_subdirectory`, the help sentence and the validator regex and message changed.
- Tested the `_COPIER_DEFAULT` regex against the real copier.yml. It matches only kmctl_ref's `  default:` line, and it cannot cross into another top-level key, because the lines it skips must start with whitespace. With that line removed it finds nothing, so `set` refuses.
- For pre-release tags, the validator's version check turns '0rc1' into 0 through Jinja's `int` filter. So v0.6.0rc1 passes, and an OpenCode pin on v0.5.1rc1 is refused, which is right because it comes before v0.5.1.
- Eval rows, test by test:
  - r1 compares the exact set of files a render writes against GENERATED, so a stray kmctl file fails it. It also checks targets, the apm entry, the justfile and CI pins, and that the YAML parses.
  - r2 compares the default with apm/apm.yml's version.
  - r3 checks both refusals and their messages, including that the OpenCode one names v0.5.1, and that both accepted cases render with their ref.
  - r5 checks the line-set difference, the file listing, that the refusal leaves a clean git status, and the git add line.
  - r6 checks that the lock's resolved_commit and uv's direct_url commit_id equal the clone's HEAD, so the package and the CLI provably came from the clone. It also checks that doctor's failures are limited to UNPASSABLE.
  - r7 checks the setup-uv step, the just install and the exact last command.
  - r8 checks the phrases, the links, that only the move section names the old repository, the decision schema and the decision's content. I also ran `kmctl check` (all checks passed) and okf validate --strict (conformant) myself.
- Read the release.py, conftest `tree_repo`, the CI and release workflows, the fixture changes, README, the manifesto, the overview and ADR 0025. No claim in them contradicts the code, apart from f1.

## Findings

- f1 (docs, not blocking): the docs say "`uvx copier update` then changes nothing", but update rewrites `_commit` in .copier-answers.yml. Say that a release with no template change only moves `_commit` there. The same sentence is in the how-to's "Keep a project current" section and in ADR 0025's Consequences.
- f2 (docs, not blocking): in the how-to's "What a generated project holds" table, the `.pre-commit-config.yaml` row should say that the hooks skip the agent files APM and kmctl plugin patch install.

## Notes

The starter CI job is the first CI job to run the `consumer` fixture and real uvx and APM installs. It cannot be checked until it runs on GitHub, as the plan's Done line expects. While reviewing I ran `git add -N .` in the worktree by mistake, which marks the new files intent-to-add in the index. File contents are unchanged. The review freeze stopped my `git reset`, so the implementer may want to run `git reset` before committing.
