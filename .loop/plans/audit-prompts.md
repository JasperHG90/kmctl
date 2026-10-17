---
type: plan
title: 'Plan: audit-prompts'
description: Three audit prompts (docs against code, .okf against code, .okf against docs) shipped as files, run as separate jobs in the workflow.
tags:
- plan
slug: audit-prompts
status: draft
epic: null
depends_on: [real-audits]
priority: null
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T14:22:38+00:00'
---

# audit-prompts

Relayed from: none

## Intent

Today's default prompt runs kmctl's audit skill, which checks only the
`.okf/` concepts that are due, and never `docs/`. Replace it with three
audits, each a prompt file the agent runs separately:

- `new:action/prompts/docs-vs-code.md`: every page in `docs/` against the
  code it describes (commands and options against the source that defines
  them, how-tos against `action.yml` and the workflows, paths and defaults
  against the files).
- `new:action/prompts/okf-vs-code.md`: every concept in `.okf/` (not
  handoffs or the log) against the code; all concepts, not only those due.
  Every option, default and number, Correction sections included, is a
  claim of its own. `run`'s default.
- `new:action/prompts/okf-vs-docs.md`: `docs/` against `.okf/`, for places
  where the two disagree (a decision says one thing, a how-to another).

`run` gains `--audit NAME` (one of the three; `okf-vs-code` when no prompt
option is given), which reads the prompt from the script's own
`action/prompts/`, so a workflow names an audit without a path into the
action's checkout. It cannot be combined with `--prompt` or
`--prompt-file`, and `--help` lists the names. The old default prompt (the
audit skill with the auditor's instructions inlined) goes; the skills stay
available to the agent.

`action.yml` gains an `audit` input passed as `--audit`.
`.github/workflows/knowledge-audit.yml` runs the audit and publish jobs as
a matrix over the three, each with its own artifact (`agent-report-NAME`)
and issue title ("Docs audit", "Knowledge audit", "Docs and knowledge
audit"). Section 5 of `docs/how-to/install-the-plugin-and-the-ci-action.md`
names the three audits and stops saying the default checks only concepts
that are due; the tutorial
`docs/tutorials/audit-your-repository-with-the-agent.md` (landed, it
teaches a custom prompt) gains a line pointing at `--audit`. ADR 0017 gets
a correction and `.okf/architecture/overview.md` shows the prompts.

Done when the offline tests show `--audit` picks each shipped prompt, the
default is `okf-vs-code`, and the workflow runs all three; the live
planted-drift runs are spike:audit-prompts/1 and spike:audit-prompts/2.

## Could invalidate this plan

- A Flash-class model may miss planted drift in one run over a whole
  folder; then the plan needs runs per page or a stronger default model.
  Settled by spike:audit-prompts/1 and spike:audit-prompts/2: the drafts
  caught 8 of 9 plants (docs-vs-code 3/3, okf-vs-docs 3/3, okf-vs-code
  2/3, missing a default in a Correction); with okf-vs-code saying every
  option, default and number, Correction sections included, is a claim of
  its own, it caught 3/3 in 135 of 200 requests. The 8 findings that were
  not plants are real drift on main; no false positives.
- The evidence check (real-audits) accepts only lines read or found by
  search, not shell output, so docs-vs-code cannot cite the CLI's `--help`
  directly; its findings must cite the source line that defines a flag.
  If that makes the docs audit miss real drift, the check needs a way to
  cite command output. Settled by spike:audit-prompts/3 (on spike 1's run): a flag renamed in
  `docs/reference/commands.md` was caught, cited against the source in
  `src/kmctl/__init__.py`.
