---
type: decision
title: "ADR 0057: The audit runs on a pull request and comments on the decisions it may have outdated"
description: "On a pull request from the same repository, the audit checks the decisions the change may have outdated and posts one comment; it never fails the check."
tags: [decision]
generated:
  by: process:kmctl/0.16.1
  at: 2026-11-26T08:12:01Z
status: draft
sources:
  - resource: "action.yml"
  - resource: "action/agent.py"
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
  and context folders resolve against a checkout of the base branch. A
  fourth shipped audit checks the decisions a change touches.
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
  request's files, and a shell command can read the API key from the
  script's own process ([ADR 0017](0017-the-ci-audit-is-a-standalone-pydanticai-agent-script.md)).
  Same-repository only means the author of that text already has write
  access to the repository, and could change the workflow anyway. Branch
  protection and review guard against that, not this record.
- Each push costs one model run. Scoping to the changed files keeps it
  small, and a repository can run it only on `ready_for_review` and later
  pushes.
- A pull request from a fork gets the free checks only.
- When this is built, ADR 0005 and ADR 0017 each get a correction that
  points here, and the comment in `.github/workflows/knowledge-audit.yml`
  that says the audit never runs on a pull request changes.
- Nothing is built until this record is accepted.
