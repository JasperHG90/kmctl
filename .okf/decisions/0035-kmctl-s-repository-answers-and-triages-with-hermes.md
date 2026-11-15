---
type: decision
title: "ADR 0035: kmctl's repository answers and triages with Hermes"
description: "kmctl's own repository runs the toiminnot Hermes actions three ways: one workflow answers a member's /hermes comment, one posts a triage comment of under 200 tokens and labels each new issue, and the Release run rewrites the drafted release notes for users with every tool off, kept only when a script's checks pass; the knowledge audit stays on action/agent.py."
tags: [decision]
generated:
  by: process:kmctl/0.5.1
  at: 2026-10-20T08:37:12Z
status: stable
sources:
  - resource: ".github/workflows/hermes-interactive.yaml"
  - resource: ".github/workflows/hermes-issue-triage.yaml"
  - resource: "scripts/hermes_triage.py"
  - resource: ".github/workflows/release.yml"
  - resource: ".github/prompts/release-notes-system.md"
  - resource: "scripts/hermes_release_notes.py"
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
- The Release run (`.github/workflows/release.yml`,
  [ADR 0012](0012-releases-come-from-ci.md)) runs
  `JasperHG90/toiminnot/actions/hermes` at the same pin on the release
  notes `scripts/release_notes.py` drafts, added 2026-11-14 when the
  operator asked for proper release notes from the triage setup. Its prompt,
  `.github/prompts/release-notes-system.md`, asks Hermes to rewrite only the
  What changed bullets for users, keep each bullet's reference, leave a line
  that names only a ticket or finding as written, and never say work was
  deferred. Every toolset is disabled by name and `max_iterations` is 3, so
  Hermes answers from the draft alone; the step may fail
  (`continue-on-error`) and times out after 10 minutes.
- `scripts/hermes_release_notes.py` keeps the rewrite only when it is
  non-empty once cleaned, keeps the draft's headings in order, leaves
  everything after What changed as the draft wrote it, and carries exactly
  the draft's `` (`slug`) `` and `(#N)` references, one or more on each
  bullet, with no line under What changed that is not a bullet or indented
  under one, unless the draft has it too. Otherwise it prints the draft
  with a warning naming the failed check, so a Hermes failure never blocks
  a release or empties its notes.
  When the rewrite is kept, the run's summary and the version pull request's
  body show the draft's What changed section under "Draft before Hermes",
  because no check can tell whether a rewritten line kept its meaning: the
  person who merges reads each line against the one it came from.
- All three use the `OLLAMA_API_KEY` secret and an Ollama Cloud model.

Rejected:

- Port both jobs to `action/agent.py`. It gives typed output and one agent
  for every CI job, but the operator wanted the workflows as they run in
  the workspace repository.
- The starter template. The operator asked for kmctl's repository only.
- An `@hermes` trigger: it mentions another account.

## Consequences

- kmctl runs two CI agents: `action/agent.py` for the audits and Hermes for
  these three jobs. ADR 0017's reasons against Hermes still apply to the
  audit.
- A member's `/hermes` in a fork's pull request conversation runs in this
  repository with the key and checks out the fork's code, so Hermes reads
  that code with the key in its environment. The member gate is the only
  guard: a member who calls Hermes on a fork's pull request vouches for
  what it reads. Inline review comments on a fork's pull request get no
  secrets, so the job skips them.
- An issue's body reaches Hermes with the API key in its environment, as
  in the audit. Use a key scoped to these jobs, with a spending limit.
- Commit subjects from main reach Hermes in the release notes draft with the
  key in its environment, as issue bodies do. With every tool off a crafted
  subject can change only the reply, and the checks and the merging person
  catch a reply that adds, drops or twists a change.
- `tests/scripts/test_workflows.py` and `tests/scripts/test_hermes_triage.py`
  pin the triggers, the trusted checkout, the SHA pins, the cut and the
  label allowlist. `tests/scripts/test_workflows.py` also pins the release
  notes step's toolsets, turns and fallback, and
  `tests/scripts/test_hermes_release_notes.py` shows each failed check
  yields the draft byte for byte.
