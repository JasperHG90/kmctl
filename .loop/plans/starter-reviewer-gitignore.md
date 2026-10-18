---
type: plan
title: 'Plan: starter-reviewer-gitignore'
description: The starter template offers the adversarial reviewer agent and writes the adversarial-review rule into AGENTS.md, and its .gitignore covers common paths.
tags:
- plan
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T18:15:44+00:00'
slug: starter-reviewer-gitignore
epic: null
depends_on: []
priority: 2
---

# starter-reviewer-gitignore

Relayed from: none

## Intent

The operator asked (2026-10-18): "The copier project should offer to
optionally install the adversarial reviewer and adversarial review rule in
the project -- add the latter to AGENTS.md" (ask
j-20261018T181315+0000-0c9cd23e), and "add a .gitignore to the copier
template with common paths to ignore (include .DS_Store)" (ask
j-20261018T181513+0000-0c8443e9).

Measured: `README.md`'s "Works better with an adversarial reviewer" section
tells every user to add the reviewer and the rule to `apm.yml` by hand, and a
project generated from `copier.yml` at v0.6.0 gets neither (rendered from
gh:JasperHG90/kmctl, 2026-10-18). Its `starter/.gitignore` ignores one path,
`apm_modules/`, so `.DS_Store`, `.venv/`, `__pycache__/` and editor folders
show up in `git status` of every generated project.

What changes:

- **A question.** `copier.yml` gains `adversarial_review` (bool, default
  yes): "Add an adversarial reviewer and the rule that calls it after each
  task".
- **The rule goes in AGENTS.md.** When yes, `starter/AGENTS.md.jinja` writes
  the rule's text, taken from jasperhg90/skills
  rules/adversarial-reviews.instructions.md at commit 41f49502, as its own
  section. AGENTS.md is the file all three harnesses read (Claude Code
  through the CLAUDE.md that `kmctl init` writes, `@AGENTS.md`), so the rule
  needs no install per harness. The rule already says to use a general
  sub-agent briefed to review skeptically when no specialized one exists.
- **The agent comes from APM, for Claude Code.** When yes and `claude` is
  one of the harnesses, `starter/apm.yml.jinja` adds
  `jasperhg90/skills/agents/adversarial-reviewer.agent.md#41f495021f3b264992c8fa764d58565c1184ab91`
  (pinned, as kmctl's own `apm.yml` pins its rules). APM 0.33.0 refused the
  file as agents/adversarial-reviewer.md (spike 1), so jasperhg90/skills
  #142 renamed its agents to `.agent.md`, merged as 41f49502. Installed for
  each target alone from that name: Claude Code gets
  `.claude/agents/adversarial-reviewer.md`; OpenCode gets a copy in Claude
  Code's format, which it skips (ADR 0024); Antigravity gets nothing. So
  only Claude Code projects get the agent; on the other two the rule falls
  back to a general sub-agent, which the rule already allows.
- **A .gitignore.** `starter/.gitignore` keeps `apm_modules/` and adds common
  paths: `.DS_Store`, `Thumbs.db`, `.venv/`, `__pycache__/`, `*.pyc`,
  `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `node_modules/`,
  `.env`, `.idea/`, `.vscode/`, `*.swp`. It must not ignore anything APM or
  kmctl installs and the project commits.
- **Tests and docs.** `tests/test_starter.py` checks both answers of the new
  question in the render, and the bootstrap test runs with it on. The
  how-to's question table and `README.md`'s reviewer section say the
  template asks.

Done when: a render with the default writes the rule section in AGENTS.md
and the agent in apm.yml, a render with `adversarial_review=false` writes
neither, the bootstrap test passes with it on, and the .gitignore holds the
paths above.

Out of scope: translating the reviewer for OpenCode or Antigravity in
`kmctl plugin patch`.

## Could invalidate this plan

- APM 0.33.0 may refuse a single-file agent dependency pinned to a commit, or
  `apm install` / `kmctl plugin patch` / `kmctl doctor` may fail when the
  agent is installed for the opencode or antigravity target, which would
  leave no way to offer the agent from apm.yml on those harnesses.
  spike:starter-reviewer-gitignore/1 (refused as .md; /2: the pinned rule
  installs, so pins work)
- With the `.agent.md` entry and `claude` among several harnesses, APM also
  copies the agent into `.opencode/agents/`; `kmctl plugin patch`,
  `kmctl doctor` or the generated project's hooks may fail on that copy,
  which would break `just bootstrap` for [claude, antigravity, opencode].
  spike:starter-reviewer-gitignore/3
