---
type: plan
title: 'Plan: okf-vs-change-audit'
description: Build draft ADR 0057 on PR 71, a shipped okf-vs-change audit that the action runs on a same-repository pull request and reports in one replaced comment.
tags:
- plan
generated:
  by: process:loopctl/2.4.0
  at: '2026-11-26T13:13:05+00:00'
slug: okf-vs-change-audit
epic: null
depends_on:
- adr-0057-pr-audit
priority: null
schema_version: '2.0'
---

# okf-vs-change-audit

Relayed from: none

## Intent

Build what draft ADR 0057,
`new:.okf/decisions/0057-the-audit-runs-on-a-pull-request-and-comments-on-the-decisions-it-may-have-outdated.md`,
decides, on PR 71's branch `adr/audit-pull-requests`, so the record and its
code are reviewed together.

- `action/agent.py` gets a fourth shipped audit, `okf-vs-change`, in `AUDITS`,
  with its prompt in `new:action/prompts/okf-vs-change.md`. `run --audit
  okf-vs-change --base REF` lists the stable decisions under `.okf/decisions/`
  whose `sources` match a file changed between the merge base of `REF` and
  `HEAD` (a file source by its path or as a folder, a source ending in `/` as
  a prefix; URL sources skipped), the same rule as the prototype's
  scope.py in the prototype `.okf/prototypes/pr-audit-scope/` on PR 71, and puts that list in the
  task. The agent may add decisions it judges the change affects, with a
  reason each. The matcher needs only git and PyYAML, which the script uses
  already, so it stays the standalone script of ADR 0017
  (`.okf/decisions/0017-the-ci-audit-is-a-standalone-pydanticai-agent-script.md`).
- `run --instructions-root DIR` resolves `--prompt-file`,
  `--system-prompt-file`, `--context` and `--skills` against `DIR` instead of
  the current folder, for each path the base branch tracks in git. A
  `--context` folder git does not track (one an earlier step fetched) stays
  in the working tree, so fetched context keeps working on a pull request;
  the operator chose this on 2026-11-26, and ADR 0057's instructions rule
  gets a sentence saying so. Shipped prompts and the default skills already come from
  the action's own checkout, which the workflow pins.
- `action.yml`'s "Check the event" step lets a `pull_request` run when the
  head repository is the base repository; a fork pull request gets a notice,
  exit 0, and no agent run. `pull_request_target` and every other event stay
  refused. On a pull request the audit step makes a checkout of
  `origin/$GITHUB_BASE_REF` from the `fetch-depth: 0` history (no token
  needed) and passes it as `--instructions-root`, with `--base` set to that
  ref.
- `publish --pr N` posts one comment on the pull request, marked so the next
  push finds and replaces it, instead of the issue; `action.yml`'s publish
  step passes it on a `pull_request` event. With no report, publish posts
  nothing and exits 0, in issue mode too: the operator chose this on
  2026-11-26, and ADR 0057's amendment of ADR 0017 already says it without
  a condition. A finding never fails a check.
- ADR 0005 (`.okf/decisions/0005-audits-report-only.md`) and ADR 0017 each get
  a `## Correction` section pointing to ADR 0057; the comments in
  `.github/workflows/knowledge-audit.yml` that say the audit never runs on a
  pull request, and that a missing report fails publish, change;
  `docs/how-to/install-the-plugin-and-the-ci-action.md` and
  `docs/explanation/why-one-hook-and-report-only-audits.md` describe the new
  event, audit and comment. ADR 0057's instructions rule gets the sentence
  on fetched context folders, and its last Consequence, "Nothing is built
  until this record is accepted.", changes to say the code lands in the same
  pull request and the record is accepted before it merges. The record stays
  `status: draft`: only a person accepts one (ADR 0050).
- Out of scope: a pull request workflow for kmctl's own repository. ADR 0057
  decides what the action allows, not that this repository turns it on, so
  `knowledge-audit.yml` keeps its `workflow_dispatch` and `schedule` triggers.

Measured effect (`.claude/rules/measure-before-ticketing.md`): over the 15
pull request merges #60 to #75, the prototype's matcher found 86 hits; every
pull request changed a source of at least 3 stable decisions (3 to 14, most
often 5), so `okf-vs-change` would have run with a non-empty scope on 15 of
15. The scope is 3 to 14 of the 49 stable decisions that `okf-vs-code` reads
on every run. `kmctl review due --base` listed 0 of the 86 for a source change
(spike:adr-0057-pr-audit/1).

Delivery: a ticket worktree branches from main. This one merges
`origin/adr/audit-pull-requests`, after ticket `adr-0057-pr-audit` has pushed
to it, with `--no-commit`, builds, commits it all as one stamped `Loop-Ticket`
merge commit, pushes to `adr/audit-pull-requests` as a fast-forward, and
closes with `loopctl ticket done`; `loopctl ticket land` runs only after PR 71
merges.

It worked when, on PR 71's head, `just test` passes with new tests that run
the scope matcher against a git fixture, run the event step for a same-repo
and a fork pull request, and replace one PR comment through a fake `gh`.

## Problems

- P1: No shipped audit checks only the decisions a change touches: `AUDITS` in `action/agent.py` holds three bundle-wide audits, and over pull requests #60 to #75 every one changed a source of 3 to 14 stable decisions that nothing checked before merge.
- P2: The "Check the event" step in `action.yml` refuses `pull_request` with exit 1, so no repository can run the audit on a pull request, and nothing tells a fork pull request apart to skip it.
- P3: `--prompt-file`, `--system-prompt-file`, `--context` and `--skills` resolve against the working tree, which on a pull request is the pull request's own code, so a pull request could loosen the audit that checks it.
- P4: `publish` posts only to an issue, and fails when there is no report (the artifact download fails, and an unreadable report exits 2).
- P5: ADR 0005, ADR 0017, `.github/workflows/knowledge-audit.yml` and two `docs/` pages say the audit runs only by hand or on a schedule, and ADR 0057 says nothing is built before it is accepted.

## Goals

- G1: The author of a same-repository pull request sees, in one comment replaced on each push, which stable decisions their change may have outdated, before it merges.
- G2: The records and user docs describe the action as built.

## Outcomes

### O1: `run --audit okf-vs-change --base REF` checks the stable decisions whose sources the change touched
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `action/agent.py`, `new:action/prompts/okf-vs-change.md`, `tests/test_agent.py`
- checked by: tests in `tests/test_agent.py` over a git fixture: a file source, a folder source as a prefix, a draft decision and a URL source left out, the matched list in the user message, `okf-vs-change` in `--help` and `AUDITS`, and `--audit okf-vs-change` without `--base` exiting 2
- seen by: operator

### O2: `run --instructions-root DIR` reads the task, system prompt, context and skills from DIR
- kind: support
- goal: G1
- fixes: P3
- needs: none
- touches: `action/agent.py`, `tests/test_agent.py`
- checked by: tests in `tests/test_agent.py` where a relative `--prompt-file`, `--system-prompt-file`, `--context` and `--skills` that git tracks resolve under DIR and not the current folder, an untracked `--context` folder stays in the working tree, and the defaults are unchanged without the flag
- seen by: calling code

### O3: The action runs the audit on a same-repository pull request with base-branch instructions and skips a fork with exit 0
- kind: behaviour
- goal: G1
- fixes: P2
- needs: O1, O2
- touches: `action.yml`, `packages/kmctl/tests/test_action.py`
- checked by: tests in `packages/kmctl/tests/test_action.py` that run the event step for `workflow_dispatch`, `schedule` and a same-repo `pull_request` (runs), a fork `pull_request` (exit 0 with a notice, agent step skipped), and `pull_request_target` and `push` (refused), and that the agent step passes `--instructions-root` and `--base` only on a pull request
- seen by: operator

### O4: `publish --pr N` posts or replaces one pull request comment, and publish with no report posts nothing and exits 0
- kind: behaviour
- goal: G1
- fixes: P4
- needs: none
- touches: `action/agent.py`, `action.yml`, `tests/test_agent.py`, `packages/kmctl/tests/test_action.py`
- checked by: tests in `tests/test_agent.py` with a fake `gh` that see a first run create the marked comment, a second run edit that comment and post no other, and a missing report exit 0 with no `gh` call; a test in `packages/kmctl/tests/test_action.py` that the publish step passes `--pr` on a `pull_request` event and tolerates a missing artifact
- seen by: operator

### O5: ADR 0005, ADR 0017, ADR 0057, the audit workflow's comments and the docs describe the built action
- kind: support
- goal: G2
- fixes: P5
- needs: O3, O4
- touches: `.okf/decisions/0005-audits-report-only.md`, `.okf/decisions/0017-the-ci-audit-is-a-standalone-pydanticai-agent-script.md`, `new:.okf/decisions/0057-the-audit-runs-on-a-pull-request-and-comments-on-the-decisions-it-may-have-outdated.md`, `.github/workflows/knowledge-audit.yml`, `docs/how-to/install-the-plugin-and-the-ci-action.md`, `docs/explanation/why-one-hook-and-report-only-audits.md`
- checked by: `prek run --all-files` green, and eval rows that grep each ADR for a dated Correction linking ADR 0057, ADR 0057 for `status: draft`, the fetched-context sentence and the new last Consequence, the workflow for no "never on a pull request" comment, and the how-to page for a pull request workflow example with the same-repository condition on both jobs
- seen by: operator

## Could invalidate this plan

- 1. Delivery to PR 71: the work goes to `adr/audit-pull-requests`, not main. spike:adr-0057-pr-audit/2 settled that a `loop/SLUG` worktree cut from main can merge that branch with `--no-commit` and push back as a fast-forward, and that `loopctl ticket done` closes a ticket without `loopctl ticket land`. This ticket waits on `adr-0057-pr-audit` (front matter `depends_on`) so it merges the revised record.
- 2. The PR comment: if a job on a same-repository `pull_request` event with `permissions: pull-requests: write` (and no `issues: write`) cannot list the pull request's comments, create one and edit it by id with `GITHUB_TOKEN`, publish cannot keep one replaced comment as ADR 0057 decides, and the publish design (or the ADR's permission) changes. spike:okf-vs-change-audit/1 settled it from GitHub's "Permissions required for GitHub Apps" table, which the workflow syntax docs name for `GITHUB_TOKEN`: listing, creating and editing an issue comment each accept Pull requests permission, so `pull-requests: write` is enough. Limit: docs, not a live run; the first real pull request run is the true test.
- 3. The base-branch checkout: if a `persist-credentials: false`, `fetch-depth: 0` checkout on a `pull_request` event (which checks out `refs/pull/N/merge`) has no `origin/$GITHUB_BASE_REF` to make a base tree from without a token, or the merge base of that ref and `HEAD` does not give the pull request's changed files, both the base-branch instructions and the scope need another source. spike:okf-vs-change-audit/2 settled it by repeating actions/checkout v7.0.1's fetch-depth 0 steps (read from its source at the pinned sha) against a local stand-in remote: `origin/<base>` is always there, `git worktree add --detach DIR origin/<base>` works with no token or network, and `git diff --name-only origin/<base>...HEAD` listed exactly the pull request's files in all three cases, including main moving before and after the merge ref.
