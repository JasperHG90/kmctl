---
type: plan
title: 'Plan: commit-apm-installs'
description: A decision records that projects commit the files APM and kmctl plugin patch deploy and gitignore only apm_modules/.
tags:
- plan
generated:
  by: process:loopctl/2.2.1.dev16+g27435b040.d20261017
  at: '2026-10-19T08:03:00+00:00'
slug: commit-apm-installs
epic: null
depends_on: []
priority: 2
---

# commit-apm-installs

Relayed from: none

## Intent

The operator (2026-10-19, ask j-20261019T080230+0000-d025c97e) closed PR #16
and issue #15, which would have gitignored every file `just bootstrap`
installs, with "Ok close it. Ensure that apm_modules is gitignored", then
"Update OKF maybe?".

APM's guide says to commit the deployed harness folders (`.github/`,
`.claude/`, `.agents/`) and to ignore only `apm_modules/`. Ignoring the
deployed files would also hide shared project config (`.claude/settings.json`,
.mcp.json, opencode.json, .agents/hooks.json, .agents/mcp_config.json)
and leave a fresh clone, or a cloud agent that only clones, without skills,
rules or the briefing hook.

What changes: one new decision, `new:.okf/decisions/0030-projects-commit-what-apm-deploys.md`,
records that rule, the rejected alternative (PR #16) and why. `kmctl new
decision` writes it and links it from `.okf/decisions/index.md` and
`.okf/log.md`; `.okf/summary.md` cites it where it describes installs if the
word limit allows. No code changes: `starter/.gitignore` already ignores
`apm_modules/` and `tests/test_starter.py` checks it.

The outcome that shows it worked: the decision exists, the index links it,
and `kmctl check` and strict OKF validation pass.

## Could invalidate this plan

- none
