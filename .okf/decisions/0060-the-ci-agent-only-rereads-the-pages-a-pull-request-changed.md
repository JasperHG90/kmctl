---
type: decision
title: "ADR 0060: The CI agent only rereads the pages a pull request changed"
description: "On a same-repository pull request the CI agent rereads every .okf/ and docs/ page whose sources the pull request changed and posts one comment; the whole-repository audits, issue publishing, the shell and the repository's own prompts go."
tags: [decision]
generated:
  by: process:kmctl/0.18.0
  at: 2026-11-27T10:43:30Z
status: draft
sources:
  - resource: "action/agent.py"
  - resource: "action/prompt.md"
  - resource: "action.yml"
  - resource: ".github/workflows/knowledge-audit.yml"
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
