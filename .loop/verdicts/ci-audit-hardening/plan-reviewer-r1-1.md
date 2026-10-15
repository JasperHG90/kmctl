---
type: verdict
title: 'Verdict: ci-audit-hardening plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of ci-audit-hardening: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T13:19:56+00:00'
slug: ci-audit-hardening
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

The f4 half is sound. The f3 half rests on a wrong premise. Unsetting or renaming the token inside the script leaves it readable in the parent processes' /proc/PID/environ (p1). The checkout step also leaves the same token in the audited repository's git config (p2). Both can be fixed inside this ticket, so the verdict is fail, not reject.

## Checked

- Plan, eval rows r1 to r3, ci-audit reviewer verdict r1-1, action.yml, action/knowledge-audit.sh, .github/workflows/knowledge-audit.yml, and the test harness in tests/test_ci_audit.py.
- Ran a local check in the scratchpad (parent.sh, child.sh, run.sh): a token exported to a parent bash, then unset there, with the child started under `env -u`, is gone from the child's env but still shows in /proc/$PPID/environ.
- No spike folder exists for this ticket. The plan's risk list says 'none'.

## Findings

- p1: unset or env -u in the script does not hide the token from claude, because /proc/PID/environ of the ancestor processes still holds it. Move the gh work into a separate composite step.
- p2: actions/checkout persists the same token in the audited repository's git config, where Read can reach it.

## Notes

Does claude need a GitHub token? No. It runs with `--strict-mcp-config` and no MCP config, so there is no GitHub MCP server. It loads the plugin from the local `KMCTL_PLUGIN_DIR`, its only tools are Read, Grep, Glob and Agent, and it authenticates with ANTHROPIC_API_KEY. Only the gh calls and `git fetch --unshallow` need GitHub credentials, and the fetch uses git's credentials, not GH_TOKEN. So keeping the token from claude costs nothing.

Can the script give gh the token while claude goes without? In the child's own environment, yes: `GH_TOKEN="$tok" gh ...` with `env -u` on claude works. That is not enough, though, because ancestor processes still expose it (p1). Splitting the token-holding work into its own composite step fixes this and keeps the script testable: the script can take a phase argument, or the issue write can move to a second small script.

The f4 half of the plan is sound. Checking the exit status of `gh issue list` before the python filter (or using `set -o pipefail` around that pipeline) works as described, and r2 tests it directly.

The plan lists no risks ('none'). p1 and p2 are the two that could break f3, and the revision should name them.
