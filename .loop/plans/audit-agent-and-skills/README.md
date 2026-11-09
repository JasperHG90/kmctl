---
type: plan
title: 'Plan: audit-agent-and-skills'
description: "An audit agent with three review skills (architecture, decision log, practices) that report findings and never write knowledge (ADR 0005, I2)."
slug: audit-agent-and-skills
epic: plugin
depends_on: [claude-plugin, review-due]
priority: 8
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T05:10:22+00:00'
---

# audit-agent-and-skills

Relayed from: none

## Intent

Adds to the plugin an `audit` skill, a `kmctl-auditor` agent, and three review skills the agent follows:

- `architecture-review`: does each `.okf/architecture/` page still match the code;
- `decision-log-review`: does each decision still hold, or has a later decision or the code overtaken it;
- `practices-review`: does each practice still have the count or code site it cites.

**Reports only (I2), by the tool list alone.** The agent's `tools` are `Read, Grep, Glob`: no Bash, no Edit, no Write. Bash limited to kmctl would not do, because `kmctl new`, `kmctl init` and `kmctl decision supersede` write knowledge. So the `audit` skill, which runs in the user's session, runs `kmctl review due --json` itself and passes the due concepts (and anything the user names) to the agent in its prompt. The agent reads, judges, and returns findings; the skill shows them. Nothing in the audit writes a file.

**Findings shape**, which ci-audit parses: the agent ends with one fenced `json` block, a list of objects with `concept` (concept id), `path`, `review` (`architecture`, `decision` or `practice`), `verdict` (`holds`, `drifted` or `unsure`), `summary` (one sentence) and `evidence` (a list of `path:line` strings). An empty list means nothing was due.

**Where it is tried.** This repository's bundle has decisions and a manifesto only, so the architecture and practices reviews are tried on loop-harness, checked out at /home/vscode/workspace, whose bundle has both. That run also counts real and false drift, the risk the operator accepted.

Done when a test checks the agent's tools are exactly Read, Grep and Glob and fails if any other is added, a test checks the findings shape against a sample the agent produced, and the skill-creator runs (on this repository and on /home/vscode/workspace) report findings in that shape.

Every skill and the agent are made with the skill-creator skill (ADR 0007), and their test prompts and results are kept beside them.

## Could invalidate this plan

- An audit may find little or a lot of false drift. Before tuning the skills, run the architecture review once on loop-harness, whose bundle is larger, and count real and false findings.
