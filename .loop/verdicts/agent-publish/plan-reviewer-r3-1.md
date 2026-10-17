---
type: verdict
title: 'Verdict: agent-publish plan-reviewer round 3'
description: 'plan-reviewer verdict for round 3 of agent-publish: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T07:45:45+00:00'
slug: agent-publish
pass: plan-reviewer
round: 3
body_schema: verdict/1
---

## Summary

Pass. p1 is closed. With the cache off on both sides and the publish job on a
fresh GitHub-hosted machine, the only thing the agent's job hands to the
publish job is the `agent-report` artifact. The publish job reads that as data
and validates `report.json` as a `Report`. Nothing else found that would break
the plan.

## Checked

- uv cache: setup-uv no longer saves or restores it, and r5 tests that.
- Checkout: the publish job checks out the commit again with
  `persist-credentials: false`. The audit job's token is `contents: read`, so
  the agent cannot push a changed CODEOWNERS or code for that checkout to pick up.
- Artifact: the agent can put any bytes in `agent-report`. It can even upload
  that artifact itself, using the runtime token it can read from the runner
  process (the runner user has passwordless sudo on hosted runners). Publish
  only reads and validates `report.json`, so the worst case is a misleading
  issue body. That is the trust ADR 0017 already accepts for the report.
- Audit job token: an agent with sudo can read the job's GITHUB_TOKEN from
  the runner's memory even if no step uses it. Job-level `contents: read`
  without `issues: write` makes that token harmless. r5 checks that the
  agent's job lacks `issues: write`.
- A failed audit skips publish. The plan says this.

## Findings

- p1 (resolved): the cache is off on every setup-uv in the workflow and action.yml, no actions/cache is used, and r5 checks both.
- p2 (resolved): an update adds a comment that mentions the owners.
- p3 (resolved): below the threshold, publish closes the open issue with a comment.

## Notes

- Builder: download the artifact into `$RUNNER_TEMP`, not the workspace.
  Otherwise a file in the artifact could shadow one in the checkout, such as
  CODEOWNERS.
- Outside this ticket: `release.yml` and `release-tag.yml` run setup-uv with
  `enable-cache: true`. Today the audit job's setup-uv saves its cache on main
  after the agent ran, and those workflows may restore it. Turning the cache
  off in the audit job, as this plan does, closes that direct path. An agent
  that steals the runtime token can still write cache entries on main, though.
  This is a separate hardening ticket (no cache in release jobs, or ADR 0005
  noting the risk), not a reason to change this plan.
