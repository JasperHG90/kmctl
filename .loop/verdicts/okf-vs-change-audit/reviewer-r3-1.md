---
type: verdict
title: 'Verdict: okf-vs-change-audit reviewer round 3'
description: 'reviewer verdict for round 3 of okf-vs-change-audit: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-26T22:12:03+00:00'
slug: okf-vs-change-audit
pass: reviewer
round: 3
body_schema: verdict/1
---

## Summary

f1 is fixed. `instruction_path` now asks the base checkout first: if the base has the path and it resolves inside the base, the base's copy is used, whatever the pull request did to the file or any parent folder. A path the pull request tracks that the base lacks exits 2. Any other path must have no symlink in it and stay inside the repository. I attacked it with parent symlinks, `..` segments, trailing slashes, doubled slashes, empty and `.` paths, symlinks out of the repository, and the subfolder case. Each attack either got the base's copy or failed with exit 2. The gates are green. The only open finding is f3, hardening deferred to its own ticket, so the verdict is pass.

## Checked

- Gates: `loopctl gate stamp` from the worktree gave "stamp green: 592dcaedece208d595241db32085a57d69cf52bbbca6187dbd899e44e4147fb2". Lint, format, tests, integration and every eval row r1 to r28 passed, including r22 (`prek run --all-files`).
- f1, attacked again: I built a scratch repository with a base worktree. The pull request replaced `.github` and `.okf` with tracked symlinks to `evil/`, added a tracked `newdir/`, an untracked `fetched/` and an untracked symlink `lnk -> ../outside` (probe: /tmp/claude-1000/-home-vscode-workspace/55c11e59-8512-407e-a916-04be246551c4/scratchpad/r3/probe.py). Results:
  - Got the base's copy: `.github/audit.md`, `./.github//audit.md`, `.github/audit.md/`, `evil/../.github/audit.md`, `.github/../.github/audit.md`, `.okf/decisions` and `sub/.github/a.md`.
  - Exit 2: `evil/audit.md` and `newdir` (tracked by the pull request, missing from the base), `lnk` and `lnk/s.md` (through a symlink), `../outside/s.md` and `fetched/../../outside/s.md` (outside the repository).
  - Stayed in the working tree: `fetched` and `fetched/../fetched`.
- Base-side symlinks: only the base's tree can hold them, and a base path that resolves outside the base falls through to the tracked or refused rules. Paths that start with `..` from a subfolder `path` input land outside `root` or `repo` and are refused.
- The cwd and the repository: with `working-directory: sub`, `git rev-parse --show-prefix` makes the root `$checkout/sub/`, `tracked()` runs git in the cwd, and `repo` is the subfolder. A pull request that turns `sub` itself into a symlink changes the prefix to the symlink's target. The base lacks that folder, so tracked paths exit 2 and the run fails closed.
- Case tricks: GitHub's Linux runners have case-sensitive file systems. On a case-insensitive file system, a different case still finds the base's file, so it fails safe.
- Getting text from the pull request into the agent: the system prompt is the shipped one or the base's file, and the skills list comes from the base's or the action's skills folders. `Workspace.resolve` follows symlinks and refuses anything outside the roots, and `files()` skips file symlinks that point outside the roots, so a tracked symlink to `/proc/self/environ` cannot be read without a shell. The okf-vs-change scope list carries the names of the changed files and decisions, which the pull request writes. That fits the design, because the agent reads the pull request's code anyway. The how-to and the explanation page say a same-repository author can still edit the workflow itself, which is the honest limit.
- `git worktree add` uses the repository's own `.git/config` and hooks, which the pull request does not control.
- Tests: the new tests (tests/test_agent.py:1507, :1547, :1574) fail against the round 2 rule. The `--context` variant asserts that `repo/evil` is not among the roots and that the base skill is listed. The deleted-file test asserts "base task". The round 1 symlink tests still pass.
- Eval rows: I checked that r1 to r16, r24 and r26 to r28 assert their `fails_when`. They check prompt contents, exit codes with flag names in stderr, the comment count and body through a stateful fake `gh`, no `gh` calls when the report is missing, the step outputs and `if` gates, and uv's arguments from running the real step scripts with stub `uv` and `git`. r17, r19, r20 and r25 are greps that match their rows.
- r21 (judgment): I read action/prompts/okf-vs-change.md. It says report only ("never change, commit or push a file"; a decision is never edited in its body). It names only the read, search and list tools and says not to rely on a shell or a skill's scripts. It asks for a reason for each added decision ("Say for each one why the change affects it"). Row holds.
- Consistency: ADR 0005 and ADR 0017 Corrections, `.okf/architecture/overview.md`, action.yml input descriptions, the agent's docstring and `--help`, the workflow comments, the how-to and the explanation page all match the code. That includes the exit 2 for a new prompt file and fetched folders staying in the workspace.
- f2 and f4: unchanged since round 2 and still covered (test_action_runs_the_agent_script_without_uv_config; `{word}-skill` in the `instructed` fixture).

## Findings

- f1 (resolved): `instruction_path` in action/agent.py prefers the base checkout's copy, refuses a new path the pull request tracks, and refuses a fetched path that runs through any symlink. Tested at tests/test_agent.py:1507 to :1590.
- f2 (resolved): `uv run --no-config --script` in both steps of action.yml.
- f3 (open, hardening, not blocking): deferred to stub ticket okf-vs-change-audit-reviewer-f3, not part of this round.
- f4 (resolved): skill names differ per tree in the `instructed` fixture.

## Notes

The round 2 note about a deleted prompt file raising FileNotFoundError is gone: the base's copy is now used. One small wording point in the how-to: "the publish job keeps `!cancelled()` too" assumes the matrix variant, since the single-audit example has no `if` on publish. The snippet shown is still correct to copy.
