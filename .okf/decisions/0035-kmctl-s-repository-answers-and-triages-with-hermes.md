---
type: decision
title: "ADR 0035: kmctl's repository answers and triages with Hermes"
description: "Two workflows in kmctl's own repository run the toiminnot Hermes actions: one answers a member's /hermes comment, the other posts a triage comment of under 200 tokens and labels each new issue; the knowledge audit stays on action/agent.py."
tags: [decision]
generated:
  by: process:kmctl/0.5.1
  at: 2026-10-20T08:37:12Z
status: stable
sources:
  - resource: ".github/workflows/hermes-interactive.yaml"
  - resource: ".github/workflows/hermes-issue-triage.yaml"
  - resource: "scripts/hermes_triage.py"
---

# ADR 0035: kmctl's repository answers and triages with Hermes

- Status: Accepted
- Date: 2026-10-20

## Context

The operator's workspace repository runs two Hermes workflows: one answers
a member's comment on an issue or pull request, the other comments on and
labels each new issue. On 2026-10-20 they asked for both in kmctl's own
repository, not in the starter. The triage comment Hermes posted there ran
to 8467 characters, about 2100 tokens, so they asked to keep it under 200
tokens. Calling the agent `@hermes` mentions a GitHub account outside the
repository, so the trigger is `/hermes`.

[ADR 0017](0017-the-ci-audit-is-a-standalone-pydanticai-agent-script.md)
replaced Hermes with `action/agent.py` for the knowledge audit. The operator
chose to keep the `JasperHG90/toiminnot` Hermes actions for these two jobs
rather than port them.

## Decision

- `.github/workflows/hermes-interactive.yaml` runs
  `JasperHG90/toiminnot/actions/hermes-interactive` when a member, owner or
  collaborator writes `/hermes` in a comment. It reads its system prompt,
  `.github/prompts/interactive-system.md`, and the okf skill in
  `.github/skills/` from a second checkout of the default branch, so a pull
  request cannot rewrite the instructions of the agent that holds the key.
  It answers in a comment and never pushes.
- `.github/workflows/hermes-issue-triage.yaml` runs
  `JasperHG90/toiminnot/actions/hermes` on each new issue, on a member's
  `/triage` comment, or by hand. Its prompt,
  `.github/prompts/issue-triage-system.md`, asks for five short lines under
  200 tokens and a `hermes-triage` trailer with the priority and labels.
- The Hermes action has no output limit, so `scripts/hermes_triage.py`
  enforces one. It strips the trailer, cuts the comment at the last line
  break within 800 characters (about 200 tokens) with a note, and applies
  only the type, `area/*` and `priority/*` labels the workflow allows. The
  areas are kmctl's top-level folders, with `okf` for `.okf/` and `ci` for
  `.github/`.
- Both use the `OLLAMA_API_KEY` secret and an Ollama Cloud model.

Rejected:

- Port both jobs to `action/agent.py`. It gives typed output and one agent
  for every CI job, but the operator wanted the workflows as they run in
  the workspace repository.
- The starter template. The operator asked for kmctl's repository only.
- An `@hermes` trigger: it mentions another account.

## Consequences

- kmctl runs two CI agents: `action/agent.py` for the audits and Hermes for
  these two jobs. ADR 0017's reasons against Hermes still apply to the
  audit.
- A member's `/hermes` in a fork's pull request conversation runs in this
  repository with the key and checks out the fork's code, so Hermes reads
  that code with the key in its environment. The member gate is the only
  guard: a member who calls Hermes on a fork's pull request vouches for
  what it reads. Inline review comments on a fork's pull request get no
  secrets, so the job skips them.
- An issue's body reaches Hermes with the API key in its environment, as
  in the audit. Use a key scoped to these jobs, with a spending limit.
- `tests/scripts/test_workflows.py` and `tests/scripts/test_hermes_triage.py`
  pin the triggers, the trusted checkout, the SHA pins, the cut and the
  label allowlist.
