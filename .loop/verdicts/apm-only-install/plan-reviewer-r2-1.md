---
type: verdict
title: 'Verdict: apm-only-install plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of apm-only-install: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-16T20:29:48+00:00'
slug: apm-only-install
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

Round 1's two migration gaps are closed. Spikes 6 and 7 answer them, and the plan follows what the spikes found. The new okf MCP item works for the plan's own install path. There okf is a transitive dependency, so APM writes no okf server (spike:apm-only-install/1 printed only the transitive-MCP warning), and kmctl's `okf-bundle` is the only one. One gap remains, and it is the double-server case the operator asked about. Repositories that followed today's APM how-to have okf-skills as a direct dependency. APM already gives them a `bundle` server, the migration leaves it, and kmctl adds a second one. The plan needs a revision, not a rethink.

## Checked

- Spike apm-only-install/6 (README and run.json, exit 0). `apm uninstall` before the swap leaves 0 SessionStart entries, and exactly 1 after the new install and a re-install. Swapping the entry or running prune leaves 2. The plan's step (b) matches the route that worked.
- Spike apm-only-install/7 (exit 0). After the kmctl uninstall, okf stays enabled and claude names `claude plugin prune`. Uninstalling okf and removing the kmctl marketplace leaves nothing enabled. The plan uses prune where the spike ran an explicit okf uninstall. claude's own message names prune for this exact case, so I leave that to the build. r6 tests the order of the three commands.
- okf-skills' apm.yml (cached copy at the pinned commit) declares one MCP server named `bundle` with `${CLAUDE_PLUGIN_ROOT}/servers/okf_mcp.py`. The old okf plugin's .mcp.json has the same `bundle`. spike:kmctl-doctor/3 shows that with okf-skills as a direct dependency, APM writes `bundle` into .mcp.json with a rewritten apm_modules path.
- APM's Claude adapter (apm_cli/adapters/client/claude.py) merges into `mcpServers` and keeps entries it did not write. A later `apm install` therefore keeps kmctl's `okf-bundle`, just as hook_integrator keeps kmctl's hook.
- spike:antigravity-harness/1: `uv run <raw URL> <bundle>` starts the server and lists its three tools. When the bundle cannot be found, the server still starts but every tool call fails, which is why the plan adds the walk-up launcher.
- docs/how-to/install-kmctl-with-apm.md lines 17 to 20 tell users to add okf-skills directly. That is the source of p3.

## Findings

- p1: resolved by spike apm-only-install/6 and the apm-uninstall-first step.
- p2: resolved by spike apm-only-install/7 and the uninstall, prune and marketplace-remove steps.
- p3: open. When okf-skills is a direct dependency, which today's APM how-to recommends, the migration leaves APM's `bundle` server next to kmctl's `okf-bundle`, so the repository gets two okf MCP servers. The plan must say how install handles this, and r6b must test it.

## Notes

- At user scope, the `okf-bundle` server runs in every Claude session, including folders with no `.okf/` above them. The plan does not say what the launcher does then (exit, so Claude shows a failed server, or start the server without a bundle). The build can settle this, but the install how-to should mention it.
- A user who enabled the okf plugin on purpose keeps it after prune, so its `bundle` server runs next to `okf-bundle`. This is rarer than p3 and could take the same report-or-skip handling.
- The ticket grew with the MCP item, but it still has one contract, and only one risk is open. I do not recommend a split.
