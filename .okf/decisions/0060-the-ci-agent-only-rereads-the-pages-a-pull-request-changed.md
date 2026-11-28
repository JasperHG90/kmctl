---
type: decision
title: "ADR 0060: The CI agent only rereads the pages a pull request changed"
description: "On a same-repository pull request the CI agent rereads every .okf/ and docs/ page whose sources the pull request changed and posts one comment; the whole-repository audits, issue publishing, the shell and the repository's own prompts go."
tags: [decision]
generated:
  by: process:kmctl/0.18.0
  at: 2026-11-27T10:43:30Z
status: stable
sources:
  - resource: "action/agent.py"
  - resource: "action/prompt.md"
  - resource: "action.yml"
  - resource: ".github/workflows/knowledge-audit.yml"
verified:
  - by: human:jasper
    at: 2026-11-27T20:41:20Z
---

# ADR 0060: The CI agent only rereads the pages a pull request changed

## Context

The CI agent in `action/agent.py` grew into two products.
[ADR 0017](0017-the-ci-audit-is-a-standalone-pydanticai-agent-script.md)
made it a general agent: three whole-repository audits (`docs-vs-code`,
`okf-vs-code`, `okf-vs-docs`) run by hand or weekly and posted to one issue,
any task from a prompt or a file, context and skill folders from the
repository, a shell to run a skill's scripts, and Langfuse tracing.
[ADR 0057](0057-the-audit-runs-on-a-pull-request-and-comments-on-the-decisions-it-may-have-outdated.md)
added a fifth path: on a pull request, check the stable decisions whose
`sources` the change touched, without a shell, with the repository's
instructions read from a base-branch checkout.

Only the pull request check does something nothing else in kmctl does.
`kmctl review due --base` lists the pages a branch made due, and only those
with a `verified` entry. It cannot say whether a page still holds after the
change. Reading each page against the new code answers that, and it is all
the agent needs to do. The weekly audits report after the change has merged
and its author has moved on, and the author's own coding agent can run the
`/audit` skill locally.

The decisions-only scope also misses pages that name sources. Over the last
15 merged pull requests it found 64 pages, and every page under `.okf/` and
`docs/` with sources would have found 72: the 8 more are docs pages
([prototype](../prototypes/pr-reread-scope/README.md)).

## Decision

The CI agent does one thing. On a pull request from the same repository it
lists every page under `.okf/` and `docs/` whose `sources` name a file the
pull request changed, compared with the base branch from the commit where the
two split, rereads each against the changed code, and reports which still
hold and which the change may have outdated. The publish job posts the report
as one comment on the pull request and replaces it on each push.

- **Every page kind.** Decisions (stable, and drafts the pull request adds),
  architecture pages, practices and docs pages. A deprecated or superseded
  decision, handoffs and the log stay out.
- **No model call when nothing is in scope.** The agent writes an empty
  report and exits 0.
- **One shipped prompt, inside the action.** The task and system prompt ship
  in `action/`, pinned with the action's commit. The repository supplies no
  prompt, context or skills, so nothing needs a base-branch checkout.
- **Read-only tools.** `read_file`, `search_files` and `list_files`. No
  shell. The agent still refuses a job where it could read a GitHub token:
  `read_file` reaches `.git/config`.
- **The prompt carries the rules the agent cannot load.** A new decision is a
  draft the author accepts ([ADR 0050](0050-drafts-are-settled-before-review-and-only-a-person-accepts-one.md)),
  a page that holds is confirmed with `kmctl verify`
  ([ADR 0055](0055-one-verify-for-the-pages-a-branch-made-due.md)), and a
  Correction is followed by `kmctl summary ack`
  ([ADR 0056](0056-the-ci-action-fails-a-pull-request-whose-summary-is-behind.md)).
- **Report only.** A finding never fails the check
  ([ADR 0005](0005-audits-report-only.md)).

Removed: the three whole-repository audits and `okf-vs-change`; scheduled
and manual runs; publishing to an issue and its CODEOWNERS mentions; the
`audit`, `prompt`, `prompt_file`, `system_prompt_file`, `context`, `skills`
and `mention` inputs; `run_shell`; the base-branch checkout; and tracing.
The `issue_title` input is now `title`, the comment's heading.

Rejected:

- **Keep the weekly audits beside the pull request check.** They cost a model
  run over the whole repository each week and report after the fact. The
  `/audit` skill does the same check in a coding session when someone wants
  it.
- **Keep `okf-vs-change` as it was.** It misses docs pages, other concept
  kinds and drafts, which the same matcher finds.
- **Build the scope on `kmctl review due --base`.** It lists only pages with
  a `verified` entry, so a page nobody has verified would never be reread.

## Consequences

- A repository that used the scheduled audit, issue publishing or a removed
  input breaks on upgrade. kmctl is pre-1.0, its install lines pin a
  release, and the release notes list what went.
- The agent and the action are smaller: one task, one prompt, three tools.
- This repository's `knowledge-audit.yml` runs the reread on its own pull
  requests.
- ADR 0005, ADR 0017 and ADR 0057 each get a Correction that points here.

## Correction, 2026-11-27

The publish job posts the comment only when a finding is at or above the
action's `min_severity` input, or when an earlier comment exists, which it
then replaces with one saying the latest run found nothing at that level.
The first live run, on pull request #83, found three real mistakes and
posted none, because `min_severity` defaulted to `high` and the agent's
rubric rated a claim the code contradicts as medium or low. `min_severity`
now defaults to `low`, so the comment lists every finding but notes, and
the system prompt rates a finding by what a reader would get wrong: high
when the page would lead them to act wrongly, low when it is wrong but they
would still act correctly. Over the 4
live pull request runs so far, a comment at `low` would have held 1 to 6
findings.

## Correction, 2026-11-27, scope and review due

Three statements above are narrower than the code:

- The Context says `kmctl review due --base` lists only the pages with a
  `verified` entry. It also lists the pages the branch edited, and it
  compares a docs page's `sources` with the diff without a `verified` entry.
  It still cannot say whether a page holds after the change, which is the
  reread's job, so the decision stands.
- The Decision says the task ships pinned with the action's commit. That
  holds for a repository that uses the action at a release. This
  repository's own workflow runs the pull request's own `action/agent.py`
  and `action/prompt.md`, so a pull request here can change them; review
  sees that change, as ADR 0057's Correction says of the workflow.
- The scope lists decisions, architecture pages, practices and docs pages.
  The code takes every markdown page under `.okf/` and `docs/` except
  handoffs, `.okf/log.md` and the `index.md` pages, with any status but
  deprecated or superseded, so a draft counts wherever it came from.

The comment is now short: a count, one bullet per finding at or above
`min_severity`, the pages that still hold, and the fixes and evidence folded
away. It says how many findings below `min_severity` it left out.

## Correction, 2026-11-27, the previous report

Each run now starts from its previous report. Rereading every page from
scratch let each run notice different things: over the 6 runs on pull
request #83, 5 findings landed on pages the run before had passed. A
`previous` job, with `pull-requests: read` and `actions: read`, follows the
audit comment's run link and hands that run's report to the audit job as an
artifact, so the audit job still holds no token. The agent answers each
earlier finding by id, still open or fixed, and the run sends back a report
that leaves one unanswered or raises a new finding on a page unchanged since
the previous report's commit, with its sources. The report records the pull
request's head commit, since the merge commit a `pull_request` checkout
builds is not fetched again. The comment opens with what is fixed, still
open and new.

## Correction, 2026-11-27, on demand

The reread no longer runs on every `pull_request` push.
[ADR 0061](0061-the-reread-runs-on-demand-on-a-ready-pull-request.md) runs
it on `workflow_dispatch`, started on a ready pull request's branch, with a
check a repository can require.
