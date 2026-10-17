---
type: plan
title: 'Plan: agent-publish'
description: A publish command in action/agent.py that opens or updates one issue only when the report has a finding at or above a severity, and @-mentions the CODEOWNERS owners.
tags:
- plan
slug: agent-publish
status: draft
epic: null
depends_on:
- standalone-agent
priority: null
generated:
  by: process:loopctl/2.1.1.dev213+ge1bc3680f.d20261016
  at: '2026-10-17T06:59:56+00:00'
---

# agent-publish

Relayed from: none

## Intent

Add `publish` to `action/agent.py`. It reads the `report.json` that `run`
wrote and posts it to GitHub with `gh`. It runs in a separate job from the
agent (decided 2026-10-17, from plan round 1, finding p1). The agent's shell
runs as the runner's user, so any later step in the same job can run code
the agent changed: the checkout, the uv cache, anything on PATH. A
GitHub-hosted runner gives each job a fresh machine, so the publish job
starts from a clean checkout of the action and gets only the `agent-report`
artifact, which it treats as data and validates as a `Report`. Nothing else
may carry over between the jobs (plan round 2, p1): setup-uv caches by
default, saving the uv cache after the agent ran and restoring it in the
next job, so every setup-uv in the audit job and audit mode sets
`enable-cache: false`, and so does the publish job and publish mode. Neither
job uses any other cache. The publish job checks out the repository (with
`persist-credentials: false`) only to read CODEOWNERS. When the audit job
fails, the publish job is skipped and an open issue stays as it was.

`publish`:

- Above the threshold (a finding at or above `--min-severity`: info, low,
  medium or high; default high), it creates the one issue titled `--title`
  (default "Knowledge audit") when none is open. When one is open, it
  replaces the body and adds a comment that names the owners and the
  counts, because GitHub notifies a mention when it is posted, not when a
  body is edited (finding p2).
- Below the threshold, it closes an open issue with a comment saying the
  latest run found nothing at or above the threshold, and otherwise posts
  nothing (finding p3).
- The body is the rendered report, a link to the workflow run (where the
  artifact is) when `GITHUB_RUN_ID` is set, and a line that @-mentions the
  owners.
- The owners come from the last `*` rule in CODEOWNERS (`.github/`, the root
  or `docs/`, in GitHub's order). `--mention` (repeatable) replaces them.
  With neither, it mentions no one.
- It exits 1 when `gh` fails and 2 for a bad option or a report that does
  not validate.

`action/knowledge-audit-issue.sh` goes. `action.yml` gains `mode: publish`,
which downloads the `agent-report` artifact and runs `publish` with the
token, plus `min_severity`, `mention` and `issue_title` inputs. Audit mode
no longer posts and needs no token. `.github/workflows/knowledge-audit.yml`
becomes two jobs: `audit` (contents: read) runs the agent and uploads the
artifact, and `publish` (needs: audit; contents: read, issues: write)
downloads it and runs `publish`. ADR 0017 gets a correction saying the
isolation holds on GitHub-hosted runners, not on a self-hosted runner that
reuses its machine. `docs/how-to/install-the-plugin-and-the-ci-action.md`
and `.okf/architecture/overview.md` change to match.

The outcome: tests with a stub `gh` show that a report above the threshold
creates the issue, or edits the open one and comments with the owners
mentioned; that a report below it closes an open issue and otherwise posts
nothing; and that the workflow and `action.yml` give the token only to a
job or mode that runs no agent.

## Could invalidate this plan

- none
