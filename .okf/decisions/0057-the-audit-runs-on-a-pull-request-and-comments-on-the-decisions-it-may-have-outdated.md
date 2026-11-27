---
type: decision
title: "ADR 0057: The audit runs on a pull request and comments on the decisions it may have outdated"
description: "On a pull request from the same repository, the audit checks the decisions the change may have outdated and posts one comment; it never fails the check."
tags: [decision]
generated:
  by: process:kmctl/0.16.1
  at: 2026-11-26T08:12:01Z
status: stable
sources:
  - resource: "action.yml"
  - resource: "action/agent.py"
verified:
  - by: human:jasper
    at: 2026-11-27T09:48:51Z
---

# ADR 0057: The audit runs on a pull request and comments on the decisions it may have outdated

## Context

[ADR 0050](0050-drafts-are-settled-before-review-and-only-a-person-accepts-one.md)
makes a person accept each draft decision before review. It does not say
whether a stable decision still holds after a change. Today two things can
tell: `kmctl review due`, and the audit in the action's `mode: audit`.

`kmctl review due` lists every page that is due, from any change. In a
repository that used kmctl, it listed 48 pages, 24 of them decisions.
Nobody works through a list that long. 31 of the 36 decisions in that
repository name the code they cover in `sources`, so most of them can be
matched to the files a pull request changes.

The audit runs only on `workflow_dispatch` or `schedule`. The 2026-10-17
correction of [ADR 0005](0005-audits-report-only.md) records this, and the
"Check the event" step in `action.yml` refuses any
other event before the agent starts. The reason is that the agent sends the
repository to a model with an API key, and it can run shell commands
([ADR 0017](0017-the-ci-audit-is-a-standalone-pydanticai-agent-script.md)).
Code from a pull request must not steer an agent that holds a secret.
A scheduled audit reports on the whole bundle in one issue, after the
change that made a decision outdated has merged.

## Decision

The action's `mode: audit` also runs on a `pull_request` event, under these
rules:

- **Same repository only.** It runs only when the pull request's head
  repository is the base repository. A pull request from a fork gets no
  audit, and the action refuses it before the agent starts. GitHub gives a
  fork's `pull_request` run no secrets either.
- **Instructions from the base branch.** The prompt, the system prompt,
  the skills and the context folders come from a checkout of the base
  branch, not from the pull request. The agent reads the pull request's
  files only as the code it checks. The agent script comes from the
  action, which the workflow pins by commit.
- **No shell on a pull request.** The agent gets only its tools that read,
  search and list files. It does not get `run_shell`. A shell command can
  read the API key from the agent's own process, so text in a pull request
  that steers the agent could otherwise make it print the key.
- **Scoped to the change.** A new shipped audit checks the decisions whose
  `sources` match a file the pull request changed, compared with the base
  branch from the commit where the two split. The agent may add other
  decisions it judges the change affects, and names why for each.
- **One comment.** The publish job posts one comment on the pull request
  and replaces it on each push. It runs in a separate job with
  `pull-requests: write`, as publish mode does today for the issue. It gets
  nothing from the audit job but the report artifact, which it validates as
  a `Report`.
- **Report only.** The audit changes no file and writes no `verified`
  entry. A finding never fails the pull request's check. The audit job
  fails only when the run errors or passes its time limit, as today.
- **A person answers.** The author answers each finding: update the
  decision, supersede it, or confirm it still holds. Only on the author's
  yes does their coding agent run `kmctl verify`
  ([ADR 0023](0023-kmctl-verify-records-a-person-s-check.md)).

### How this amends ADR 0005

- Today: the LLM audit is opt-in, reports only, never writes a `verified`
  entry, and runs only on `workflow_dispatch` or `schedule`.
- Changes: it may also run on `pull_request`, under the rules above, and it
  can report in a pull request comment as well as an issue.
- Stays: opt-in, report only, no `verified` entry from an audit, and the
  two tiers (free checks on every pull request, the model audit only where
  a repository turns it on).

### How this amends ADR 0017

- Today: `action/agent.py` is one standalone script. It refuses to start
  when it could read a GitHub token. Publish mode runs in a separate job and
  posts one issue.
- Changes: publish mode can post one pull request comment instead of an
  issue. On a pull request, the audit job's prompt, system prompt, skills
  and context folders resolve against a checkout of the base branch, and
  the agent runs without `run_shell`. A fourth shipped audit checks the
  decisions a change touches.
- Stays: one standalone script, no GitHub token in the agent's job, a
  separate publish job that shares only the artifact, and a validated
  `Report`.

Rejected:

- **`pull_request_target` with the pull request's code checked out.** That
  event runs with the base branch's secrets and a write token, also for a
  fork. A workflow that checks out the fork's code there lets that code
  steer a job that holds both. Checking out untrusted code under
  `pull_request_target` is the known way to leak a repository's secrets.
- **A finding fails the check.** ADR 0005 keeps audits to reports. A model's
  judgment would then block merges. People would also confirm findings
  without reading them, to get the check green.
- **Keep the audit on a schedule only.** The weekly issue covers the whole
  bundle. By the time it lists a decision, the author of the change that
  outdated it has moved on, and nobody owns the finding.
- **One review comment per finding, inline on the diff.** Each push would
  add more comments, and old ones would stay after the code moved. One
  comment, replaced on each push, always shows the current findings.

## Consequences

- A repository that turns this on adds a workflow with two jobs, the audit
  and the publish, and a secret that holds the model's API key. Use a key
  scoped to the audit, with a spending limit.
- Prompt injection is the remaining risk. The agent reads the pull
  request's files, and text in them can steer what the agent writes in its
  report. Without `run_shell`, the agent cannot read the API key from its
  own process ([ADR 0017](0017-the-ci-audit-is-a-standalone-pydanticai-agent-script.md)),
  so the report cannot contain the key. Same-repository only means the
  author of that text already has write access to the repository, and
  could change the workflow anyway. Branch protection and review guard
  against that, not this record.
- On a pull request, the audit cannot run the scripts a skill ships. The
  audit that checks the decisions a change touches must work with the
  read, search and list tools alone.
- Each push costs one model run. Scoping to the changed files keeps it
  small, and a repository can run it only on `ready_for_review` and later
  pushes.
- A pull request from a fork gets the free checks only.
- When this is built, ADR 0005 and ADR 0017 each get a correction that
  points here, and the comment in `.github/workflows/knowledge-audit.yml`
  that says the audit never runs on a pull request changes.
- Nothing is built until this record is accepted.

## Correction, 2026-11-26

This record was accepted before its review was answered. This section
answers it. The text above stands, apart from what this section changes,
and the no-shell rule stays in force.

**Why the audit keeps its own matcher.**
[ADR 0055](0055-one-verify-for-the-pages-a-branch-made-due.md) added
`kmctl review due --base REF`, which lists what a branch made due, and
kmctl's CI action shows that list on every pull request. It does not find
the decisions a change may have outdated. It compares a page's `sources`
with the diff only when the page has a `verified` entry, and no decision in
this repository has one. Over pull requests #60 to #75, 86 times a pull
request changed a file that a stable decision names in `sources` (20
distinct decisions), and `review due --base` listed none of the 86 for that
reason ([prototype](../prototypes/pr-audit-scope/README.md)). Even for a
verified decision, `--base` says only that a source changed. Whether the
decision still holds after the change takes reading it against the new
code, which is what the audit does. So the audit matches `sources` itself:
a file source by its path, and a folder source, such as `packages/kmctl/`,
as a prefix.

**The audit's name and history.** The shipped audit that checks the
decisions a change touches is `okf-vs-change`, next to the three in
`AUDITS` in `action/agent.py`. Its merge base needs the branch's history,
which audit mode has already, since it asks for a checkout with
`fetch-depth: 0`.

**A fork is skipped, not refused.** The action does not refuse a fork pull
request with a failed check. The workflow puts the same-repository condition
on both the audit job and the publish job, so GitHub skips both and shows
them as skipped. As a backstop, the action's event check skips a fork pull
request with a notice and exits 0 before the agent starts. When there is
no report, publish posts nothing and exits 0, whether it would have posted
an issue or a pull request comment, so a skipped or failed audit never also
fails publish.

**What the base checkout protects.** On a `pull_request` event GitHub runs
the workflow file from the pull request itself, so a same-repository author
can change that workflow, and with it what the audit loads. The base-branch
checkout does not stop that. It makes loosening the audit a visible change:
a pull request cannot quietly edit the prompt to skip a decision or soften
a finding, it has to change the workflow, which review and branch protection
see. The key stays out of reach of text in the pull request because the
agent runs without `run_shell`, as the rule above decides, not because of
the checkout. A `--context` folder that git does not track, one an earlier
step fetched, is not in the base checkout, so it stays in the working tree;
an instruction path git tracks comes from the base checkout.

**Where it belongs.**
[ADR 0046](0046-kmctl-works-from-code-toward-knowledge-and-kmaudit-from-knowledge-toward-code.md)
puts a feature in the package whose direction it shares. `okf-vs-change`
starts from each decision's `sources` and checks the decision against the
changed code, so it works from knowledge toward code, kmaudit's direction.
The shipped audits live in the action today (`action/agent.py` and
`action/prompts/`), outside both packages, and `okf-vs-change` joins them
there. If the shipped audits move into kmaudit, it moves with them.

## Correction, 2026-11-27

[ADR 0060](0060-the-ci-agent-only-rereads-the-pages-a-pull-request-changed.md) widens and simplifies the pull request audit. It rereads every page
under `.okf/` and `docs/` whose `sources` the pull request changed, not only
stable decisions: drafts the pull request adds, architecture pages, practices
and docs pages too. Over the last 15 merged pull requests that added 8 docs
pages to 64 decisions ([prototype](../prototypes/pr-reread-scope/README.md)).
With nothing in scope it calls no model. The repository supplies no prompt,
context or skills any more, since the one prompt ships with the action, so
the base-branch checkout is gone. The same-repository rule, no shell, one
comment replaced on each push, report only and the author's answer stand.

## Correction, 2026-11-27, the shipped audits

The 2026-11-26 Correction's "The audit's name and history" and "Where it
belongs" describe a shipped audit that no longer exists.
[ADR 0060](0060-the-ci-agent-only-rereads-the-pages-a-pull-request-changed.md)
removed `okf-vs-change`, the `AUDITS` list in `action/agent.py`, the other
three shipped audits and `action/prompts/`. The action's one audit is the
pull request reread, whose task ships in `action/prompt.md`. The reasoning
under "Where it belongs" still holds for it: it starts from each page's
`sources` and checks the page against the changed code, kmaudit's direction,
and it lives in the action, outside both packages.

## Correction, 2026-11-27, verified decisions and the pinned script

The 2026-11-26 Correction says no decision in this repository has a
`verified` entry. That is no longer true: every stable decision now has a
`verified` entry, so `kmctl review due --base` compares their `sources` with
the diff. The audit keeps its own matcher for the reason that Correction
also gives: `review due --base` says only that a source changed, not whether
the page still holds.

The Decision says the agent script comes from the action, which the
workflow pins by commit. That holds for a repository that uses the action at
a release. This repository's workflow runs the pull request's own
`action/agent.py` and `action/prompt.md`, so a same-repository pull request
here can change what the audit does; review and branch protection see that
change.
