---
type: decision
title: "ADR 0005: Audits report only, and CI runs them in two tiers"
description: "The audit agent and its review skills report findings and never write knowledge or verified stamps; the reusable GitHub Action runs free deterministic checks on every PR and an opt-in LLM audit."
generated:
  by: claude-opus/5.5
  at: 2026-10-15
tags: [adr, decision]
status: stable
verified:
  - by: human:jasper
    at: 2026-11-27T09:48:51Z
  - by: human:jasper
    at: 2026-11-27T20:41:20Z
---

# ADR 0005: Audits report only, and CI runs them in two tiers

- Status: Accepted
- Date: 2026-10-15

## Context

Knowledge drifts and no deterministic check catches all of it, so an agent
has to judge. An agent that both judges and edits the knowledge can quietly
make it agree with itself.

## Decision

- One audit agent uses three skills: architecture review (does the design
  match the code), decision-log review (does each decision still hold, or has
  a later one or the code overtaken it) and practices review (does each
  practice still have the evidence it cites).
- It reports findings. It never edits .okf/ or docs/ and never writes a
  verified stamp. A person, or an agent the person asks, acts on them.
- The reusable GitHub Action has two tiers: the deterministic checks on every
  pull request, at no model cost, and the LLM audit only when a repository
  opts in. Both report as a job summary or comment.

Rejected:

- The audit writes verified stamps when a concept passes. The operator chose
  report only.

## Correction, 2026-10-15

The record had no Consequences section; this adds it.

### Consequences

- The audit skill, its three review skills and the kmctl-auditor agent
  write no knowledge; a person or an agent they ask acts on the findings.
- Nothing is ever marked verified by an audit, so a concept stays due until
  a person checks it.
- The GitHub Action runs `kmctl check` and `kmctl review due` and fails
  when `kmctl check` fails or `kmctl review due` crashes; due concepts are
  reported, never failed.
- The action's opt-in `mode: audit` runs the auditor through headless
  Claude Code with only Read, Grep, Glob and Agent, on workflow_dispatch or
  schedule only, and reports in the job summary and one "Knowledge audit"
  issue. It never edits or pushes. It fails when Claude Code errors or
  returns no findings, never because a concept drifted.

## Correction, 2026-10-15

The last Consequence above is out of date. The action's `mode: audit` now
runs the auditor through Hermes Agent against any OpenAI-compatible
provider, with only kmctl's three read tools (`kmctl_read_file`,
`kmctl_search_files`, `kmctl_list_files`), which refuse any path outside the
repository. It fails when Hermes errors, runs past its time limit or returns
no findings, never because a concept drifted. Why is
[ADR 0010](0010-the-ci-audit-runs-hermes-agent-against-any-openai-compatible-provider.md).
The report-only rule and the two tiers stand.

## Correction, 2026-10-17

The 2026-10-15 correction above is out of date. The action's `mode: audit`
now runs `action/agent.py`, a standalone PydanticAI agent, against any
provider. It reads the repository and the context and skill folders it is
given, and can run shell commands so skills' scripts work. Its system prompt
says never to change, commit or push a file, and nothing it changes is
committed or pushed: the checkout holds no credentials and the GitHub token
reaches only the later issue step. It fails when the run errors or passes
its time limit, never because a concept drifted. It still runs only on
`workflow_dispatch` or `schedule`: `action.yml` refuses any other event
before the agent starts. Why is
[ADR 0017](0017-the-ci-audit-is-a-standalone-pydanticai-agent-script.md).
The report-only rule and the two tiers stand.

## Correction, 2026-11-26

The 2026-10-17 correction above says audit mode runs only on
`workflow_dispatch` or `schedule`. It now also runs on a `pull_request`
from the same repository, as [ADR 0057](0057-the-audit-runs-on-a-pull-request-and-comments-on-the-decisions-it-may-have-outdated.md) decides. A pull request from a fork or
from Dependabot gets a notice and no audit, and the check still passes.
`action.yml` refuses every other event. On a pull request the agent runs
without `run_shell` and can report in one pull request comment, replaced on
each push, instead of an issue. The audit stays opt-in and report only: it
writes no `verified` entry, and a finding never fails a check. The two tiers
stand.

## Correction, 2026-11-27

[ADR 0060](0060-the-ci-agent-only-rereads-the-pages-a-pull-request-changed.md) narrows the CI audit to one job: on a pull request from the same
repository, reread the pages under `.okf/` and `docs/` whose `sources` the
pull request changed, and post one comment. The CI audit no longer runs by
hand or on a schedule, and no longer posts an issue. What this record decides
still holds: audits report only, write no `verified` entry, and a finding
never fails a check. The `/audit` skill still checks the bundle in a coding
session.
