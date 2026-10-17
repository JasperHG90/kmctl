---
type: verdict
title: 'Verdict: antigravity-rules plan-reviewer round 3'
description: 'plan-reviewer verdict for round 3 of antigravity-rules: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T06:35:51+00:00'
slug: antigravity-rules
pass: plan-reviewer
round: 3
body_schema: verdict/1
---

## Summary

p1 is resolved. Spike 3 ran agy 1.4.0 live against plugin rules in
`.agents/plugins/kmctl/rules/` and showed `**/.okf/**` firing for
`.okf/index.md` while `.okf/**` did not, so `**` does enter the hidden
folder. The same run backs the other glob claims the plan rests on. I found
no new risk that could break the plan, so this is a pass.

## Checked

- Spike 3: README outcome, the copied script, stdout, empty stderr and
  run.json (exit 0, no timeout). The script writes six rules with distinct
  secret words into the plugin's `rules/` folder, asks agy to view one file
  and name the secret words it sees, and checks the expected hits and misses.
  Output: `.okf/index.md -> OKFSTAR`, `docs/guide/intro.md -> DOCSLIST`,
  `README.md -> DOCSLIST`. That settles: `**/.okf/**` fires, `.okf/**` and
  `docs/**` do not, a comma string fires for both its globs, the brace form
  does not, and a non-matching `**/src/**` stays quiet (a control against
  the model echoing every word).
- The four `apm/.apm/instructions/*.instructions.md` `applyTo` values. Each
  glob becomes a `**/`-prefixed form of a shape the spike tested
  (`**/.okf/**`, `**/docs/**`, `**/README.md`) or the same shape for other
  folders (`**/src/**` etc.), plus `**/.okf/manifesto.md`, which is a plain
  file path under the tested `**/.okf/` prefix.
- `src/kmctl/plugin.py`: `HARNESSES` is only claude and antigravity, so no
  other harness reads `.agents/rules/`, and deleting kmctl's copies there
  harms nothing else. `install` runs `write_plugin` after APM, where the
  deletion fits.
- `src/kmctl/antigravity.py` `plugin_files`/`compare_plugin` and
  `pyproject.toml` force-include (skills and agents only today): adding
  rules and shipping the instructions fits the existing pattern, as round 2
  also found.
- Spike 2 still settles the listed risk about deleting APM's copies.

## Findings

- p1: resolved by spike:antigravity-rules/3, as above.

## Notes

The spike tested one model (`gemini-3.8-flash-high`) reporting what is in
its context. That is the plan's own test setup and is enough to settle the
matcher question. The ticket stays small enough not to split.
