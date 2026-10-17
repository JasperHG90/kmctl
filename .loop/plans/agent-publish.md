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
wrote and, in its own step, the only one given the GitHub token, posts it
with `gh`:

- It opens or updates the one open issue titled `--title` (default
  "Knowledge audit") only when a finding's severity is at or above
  `--min-severity` (info, low, medium or high; default high). Otherwise it
  posts nothing and says so.
- The body is the rendered report, a link to the workflow run (where the
  `agent-report` artifact is) when `GITHUB_RUN_ID` is set, and a line that
  @-mentions the owners.
- The owners come from the last `*` rule in CODEOWNERS (`.github/`, the root
  or `docs/`, in GitHub's order). `--mention` (repeatable) replaces them.
  With neither, the issue mentions no one.
- It fails (exit 1) when `gh` fails, and exits 2 for a bad option or a
  report that does not validate.

`action/knowledge-audit-issue.sh` goes. `action.yml`'s audit mode and
`.github/workflows/knowledge-audit.yml` run `publish` in the issue step;
`action.yml` gains `min_severity`, `mention` and `issue_title` inputs.
ADR 0017 gets a correction, and `docs/how-to/install-the-plugin-and-the-ci-action.md`
and `.okf/architecture/overview.md` change to match.

The outcome: tests with a stub `gh` show a report with no finding at the
threshold opens no issue, and one with such a finding creates the issue,
or edits the open one, with the CODEOWNERS owners or the `--mention` names
in its body.

## Could invalidate this plan

- none
