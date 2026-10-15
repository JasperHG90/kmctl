---
type: verdict
title: 'Verdict: audit-any-provider plan-reviewer round 3'
description: 'plan-reviewer verdict for round 3 of audit-any-provider: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T14:44:38+00:00'
slug: audit-any-provider
pass: plan-reviewer
round: 3
body_schema: verdict/1
---

## Summary

The revision settles p1 and p2. The plugin is now plain Python with its own handlers, Hermes 0.19.0's plugin API supports that, and the rows match the done-when items. One gap remains (p3): an in-process regex search can hang the whole Hermes process, nothing inside the process can stop it, and the workflow has no timeout. The fix is one line in the script or workflow plus a row check. It needs a revision, not a rethink.

## Checked

- Read the revised plan, the re-signed rows r1 to r8, the round 2 verdict and the spike 1 outcome.
- Hermes 0.19.0 plugin API (hermes_cli/plugins.py PluginContext.register_tool, tools/registry.py dispatch): register_tool(name, toolset, schema, handler, check_fn=None, ...) takes any callable. dispatch calls handler(args, **kwargs), normalizes a str or dict result, and turns any exception into {"error": ...}. So a plugin can supply its own schema dict and handler without importing Hermes internals, and check_fn is optional. The spike plugin reused Hermes' handlers only by choice.
- Mapped the done-when items to rows: stub config to r1, -t and plugin install to r2, toolset contents, root refusals, dash patterns and no shell imports to r3, prompt and findings to r4, workflow steps to r5, the spike to r8. r6 and r7 cover regressions and the ADR. Every item has a row.
- Regex hazard probes (review-aap-plan-r3/bt.py, bt2.py): a catastrophic pattern in a worker thread blocked a 2-second future timeout and the main thread too, so the process had to be killed from outside. signal.alarm on the main thread did interrupt re after 2 s. Hermes uses worker threads for concurrent tool calls.
- Grepped .github/workflows/knowledge-audit.yml, action.yml and action/knowledge-audit.sh for a timeout: none.

## Findings

- p1 (resolved): the root guard on the plugin's own tools, plus r3's refusal cases, answers round 1.
- p2 (resolved): no program is ever started, so a pattern cannot become a flag; r3 checks both the source and the behaviour.
- p3 (open): a catastrophic regex hangs the run, and only an external timeout stops it. Details in the front matter.

## Notes

- Build details, not findings: when the search walks the tree, check each file it opens against the root as well, not just the starting path. os.walk does not follow directory symlinks, but a symlinked file listed in a folder still opens its target. Read files in binary with a byte cap and decode with errors='replace' (or skip files with NUL bytes), so huge or binary files cannot flood the context or raise mid-walk. Hermes caps tool result size, but only after the handler has read the whole file.
- Since this is the last round before the cap, the p3 fix is small enough to check quickly: one timeout on hermes (or on the step) and one r2 condition for it.
