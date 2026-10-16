---
type: verdict
title: 'Verdict: kmctl-doctor plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of kmctl-doctor: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-16T20:21:07+00:00'
slug: kmctl-doctor
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The approach holds: harness detection is settled by spike:kmctl-doctor/1, the lock records targets and hashes for both harnesses, and with an apm.yml `ref:` the lock carries `resolved_ref` for the ref check. Five risks need a revised plan, two of them best answered by a spike first (p2, p3). Fail, not reject: nothing here forces a rethink.

## Checked

- Read the plan, its eval rows r1 to r8, and the apm-only-install and antigravity-harness plans it depends on.
- Risk 1 (harness detection): spike:kmctl-doctor/1 README, stdout and run.json. Exit 0. The fresh-repo lock lists `.agents/` and `.claude/` paths with sha256 and `deployments[].target`. An existing apm.yml gets no `targets:`, which apm-only-install now writes itself. Settled.
- Lock ref field: the lock in this repo and spike:repo-uses-apm/1 record `resolved_ref` when a ref is pinned, so the ref check has a field to read.
- spike:apm-only-install/1 stdout: what the Claude install deploys, the okf MCP warning, no .mcp.json, and okf's hook integrated into .claude/settings.json.
- spike:antigravity-harness/3: where trust is recorded (`trustedWorkspaces` in ~/.gemini/antigravity-cli/settings.json), which matches the plan's antigravity.trust check.

## Findings

- p1: claude.okf-mcp checks something the Claude install never declares, so Done-when cannot be met as written.
- p2: kmctl's hook merge may change a file the lock hashes, so the sha check would fail on correct installs. This needs a spike.
- p3: the real `uv tool run ... apm --version` and `claude plugin list --json` may write under HOME or use the network, which breaks the read-only and offline promise. This needs a spike.
- p4: after a `--scope user` install, doctor reports a false failure and gives a misleading fix.
- p5: the antigravity.plugin check disagrees with antigravity-harness's folder contents and drops the per-file comparison that `plugin status` had.

## Notes

The ticket also removes `plugin status` and adds the old-plugin and trust checks. Those are still in scope for one ticket. If the p2 or p3 spikes force deeper changes, think about moving the `plugin status` removal into its own ticket.
