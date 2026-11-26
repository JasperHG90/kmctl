---
type: verdict
title: 'Verdict: okf-vs-change-audit reviewer round 1'
description: 'reviewer verdict for round 1 of okf-vs-change-audit: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-26T21:36:39+00:00'
slug: okf-vs-change-audit
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The audit, the matcher, the event check, the PR comment and the missing-report path all do what the plan says, and the gates are green. Two security holes block the change. Both let a same-repository pull request get around the guarantees ADR 0057 and its Correction give without touching the workflow: a symlink in place of a tracked instruction path gets past the base checkout and can expose the API key, and a uv.toml in the pull request controls what `uv run` installs and runs in the steps that hold the key and the token. Two small non-blocking findings sit on the comment marker and on a weak assertion in r7's test.

## Checked

- Gates: I ran `loopctl gate stamp` from the worktree. Result: "stamp green: 0a8fa71453ff5f018dd6e3c43d0d4b543993f988fd29795806c6320bd53e7634". lint, format, tests, integration and every command row (r1 to r28, r22 prek included) pass.
- Diff: `git diff --cached main` for action.yml, action/agent.py, action/prompts/okf-vs-change.md, the workflow, the ADR 0005 and 0017 Corrections, the architecture overview, the three docs pages and both test files. I read action.yml and the new prompt in full, and the agent.py hunks with the Workspace guard around them.
- Matcher: source_matches and changed_decisions follow the prototype's scope.py rule (lstrip "/", a trailing "/" is a prefix, otherwise the exact path or path + "/"). Drafts, unparseable front matter and URL sources are skipped. `--relative` together with args.repo "." in inputs.path keeps it at the bundle root, and the subfolder prefix lands on --instructions-root through `git rev-parse --show-prefix`.
- Security, f1: I built a repository where a tracked `.github/audit.md` becomes a symlink to /proc/self/environ and `ctxlink` a symlink to /proc/self, then called agent.instruction_path against a base folder. `--prompt-file` resolved to /proc/PID/environ, and its text held the SECRET_KEY value I set. `--context` resolved to /proc/PID. The cause is that `tracked()` resolves the path before `git ls-files`, so a path outside the repo errors out, is taken as untracked and stays in the working tree. Contexts and skills become Workspace roots, so the guard in Workspace.resolve does not catch it.
- Security, f2: in a folder holding a uv.toml with `[[index]] url = "http://127.0.0.1:9/simple" default = true`, `uv run --script` on a script outside that folder tried to resolve from that index (connection refused), so uv 0.13.7 applies working-directory config to script runs. `uv tool install` ignored it, so the install step is not affected. The agent step and the publish step both run with `working-directory: inputs.path`, which is the pull request's tree. `--no-config` (or UV_NO_CONFIG=1) on those two `uv run` calls closes it.
- No shell: make_tools drops run_shell, and the system prompt swaps SHELL_LINE for NO_SHELL_LINE, which says a skill's scripts cannot run (a plan reviewer's build note). The action passes --no-shell only on pull_request. Shipped prompts and the default skills come from github.action_path. No token reaches the agent step: refuse_tokens is unchanged, and the base worktree needs none.
- Event step: a fork compares head.repo.full_name with github.repository; Dependabot is matched on github.actor. Both write run=false and a ::notice::, and exit 0. The agent step is gated on steps.event.outputs.run. Everything else exits 1. The upload uses `if-no-files-found: ignore`, and the download in both action.yml and the workflow has continue-on-error.
- Publish: a missing report exits 0 before any gh call. In --pr mode the code lists comments with `--paginate --slurp` and flattens the pages, PATCHes the marked comment or creates one, and when nothing reaches the threshold it writes "found nothing" over an earlier comment, or posts nothing if there is none.
- Eval rows: each test asserts its row's fails_when. r11 checks the notice, exit 0, run=false and the gate in the agent step's `if`. r13, r16 and r28 run the real step scripts with stub uv and git. r14's fake gh keeps comment state and checks there is one comment with the new body. r15 checks for no gh call in both modes. r26 checks exit 2 and the message. r27 checks the tools and the prompt text both ways. r7 is weak on skills (f4).
- r21 (judgment): action/prompts/okf-vs-change.md says "Report only: never change, commit or push a file", says not to rely on a shell or a skill's scripts and to use the read, search and list tools, and asks for a reason for each decision the agent adds beyond the list ("Say for each one why the change affects it"). It also says a decision is never edited in its body. It passes.
- Plan build notes: the how-to says a PR that adds a new prompt_file exits 2 until it merges, and that a run with no report leaves the last comment as it was. The subfolder prefix and the bundle root were covered above.
- Docs: the ADR 0005 and 0017 Corrections, the overview, the how-to, the explanation and the tutorial match the code. I chose not to raise f1 and f2 as docs findings. The explanation and how-to claims ("text in the pull request cannot make it read the key", "the pull request cannot quietly loosen the audit") are what ADR 0057 decides, and they become true once f1 and f2 are fixed.

## Findings

- f1 (bug, blocking): `tracked()` in action/agent.py calls `path.resolve()` before `git ls-files`. With a symlink that leaves the repository, ls-files fails, the path counts as untracked, and `instruction_path` returns the resolved outside target. The same thing happens for a symlink into an untracked part of the repo such as `.git`. That breaks the Correction's claim that "a pull request cannot quietly edit the prompt", and ADR 0057's claim that "the report cannot contain the key". The fix: when `root` is set, ask git about the raw relative path, unresolved, so a tracked symlink counts as tracked and resolves under the base checkout. Also refuse, or resolve under root, a path whose working-tree resolution leaves the repository. Add a test with a tracked symlink to an outside file for --prompt-file and --context. It is blocking because a wrong fix keeps the key reachable.
- f2 (bug, blocking): uv config discovery in the PR checkout gives the pull request code execution in the audit step, which holds the API key, without changing the workflow. That is more than the shell ADR 0057 takes away. Run `uv run --no-config --script ...` in the agent step and the publish step (at least on pull_request), and add an action test that the agent step's uv arguments carry it on a pull request.
- f3 (hardening, not blocking): match the marked comment only when its author is the token's bot user, so a quoted marker cannot break publish.
- f4 (test-strength, not blocking): give the base tree's skill a different name or description from the head tree's, and assert the system prompt lists the base one, so r7 fails when --skills resolves against the current folder.

## Notes

`git worktree add` to the fixed `$RUNNER_TEMP/kmctl-base` fails when one job runs the action in audit mode twice on a pull request. The docs show a matrix, which runs one job per audit, so nothing documented hits this. A unique folder (mktemp -d under RUNNER_TEMP) would remove the limit.
