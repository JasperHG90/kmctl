---
type: verdict
title: 'Verdict: agent-publish plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of agent-publish: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T07:44:14+00:00'
slug: agent-publish
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

Fail on one point. p2 and p3 are settled. p1 is mostly settled by the
separate job, but setup-uv's default cache carries files the agent can write
from the audit job into the publish job, so the token step can still run code
the agent changed. The fix is a plan revision (disable the uv cache in the
audit job and audit mode, and test for it), not a rethink.

## Checked

- setup-uv v6 action.yml: enable-cache defaults to "auto", save-cache to
  "true", prune-cache to "true", with a post step that saves the cache.
  Fetched from the v6 tag.
- action/agent.py keeps HOME and PATH for run_shell (SHELL_ENV_KEEP) and
  writes report.json, so publish can validate it as a Report.
- The current workflow and action.yml both use setup-uv@v6 with no cache
  settings.
- Eval rows r1 to r3 match the revised p2 and p3 behaviour. r5 checks for
  tokens and job split but not for a shared cache.

## Findings

- p1 (open): setup-uv@v6's default cache is saved by the audit job after the agent ran and restored by the publish job, so the token step can run code the agent wrote into the uv cache. Disable the cache in the audit job and audit mode, and add it to r5.
- p2 (resolved): an update now adds a comment that mentions the owners.
- p3 (resolved): below the threshold, publish closes the open issue with a comment.

## Notes

- Not a finding, but the builder will hit it: the publish job needs a checkout
  of the repository to read CODEOWNERS, and action.yml's publish mode should
  say so. A fresh checkout is fine, because the agent has no write token.
- With `needs: audit`, publish is skipped when the audit job fails, so a
  stale issue stays open after a failed run. That is acceptable, but say so
  in the docs.
- One ticket is enough. The open risk is narrow.
