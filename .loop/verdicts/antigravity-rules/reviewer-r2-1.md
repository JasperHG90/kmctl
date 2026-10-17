---
type: verdict
title: 'Verdict: antigravity-rules reviewer round 2'
description: 'reviewer verdict for round 2 of antigravity-rules: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T06:59:30+00:00'
slug: antigravity-rules
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

Both round 1 findings are fixed and the fixes broke nothing they touched. The
manifesto and the architecture overview now say that kmctl's plugin folder
carries Antigravity's rules and that kmctl deletes APM's copies (ADR 0016). The
r4 consumer test now runs kmctl init and kmctl doctor --json and asserts the
three Antigravity checks that cover the rules.

## Checked

- I ran `loopctl gate stamp` from the worktree with a scratch HOME myself.
  Result: `stamp green: 3db4a2a9fab875d412e645a5a9dbd833789c6a360307f09ac7ab5b0b19518c75`.
  Lint, format, tests and integration passed, and r1 to r6 passed. The state
  commit was deferred only because the scratch HOME has no git identity.
- I read the worktree diff against main for .okf/manifesto.md,
  .okf/architecture/overview.md and tests/test_antigravity.py.
- I looked for leftover claims that APM writes Antigravity's rules. Only ADR
  0015's title and description still say so. That is the historical record,
  and round 1 checked that it points to 0016.
- For r4 I read the doctor command and its checks. The consumer fixture limits
  PATH to uv and uvx, so dep.agy fails there and doctor exits 1 whatever the
  rules do. Asserting antigravity.files, antigravity.plugin and
  antigravity.okf-skills is the strongest check this fixture allows.
  antigravity.files is the check that would fail if doctor still expected
  kmctl's rules in .agents/rules/, and antigravity.plugin fails if the folder
  lacks a rule. So the test fails when the row's behavior breaks.

## Findings

- f1: resolved. Manifesto line 63 onward now names the knowledge rules in the
  plugin folder and cites ADR 0016. Overview.md's install row, the wheel's
  contents (now with apm/.apm/instructions/), the plugin-folder bullet and the
  rules bullet all match the code.
- f2: resolved. test_consumer_gets_skills_rules_and_the_plugin_folder runs
  `kmctl init`, then `kmctl doctor --json`, and asserts that the three
  Antigravity checks pass. See Checked for why it does not assert exit 0.

## Notes

- The row's wording, "kmctl doctor exits 0", cannot hold in this fixture
  because agy is not on PATH. The test checks the part of doctor that the row
  is about. If someone revises the row later, it could name those checks.
- The edited manifesto line runs past the wrap width of the lines around it.
  This is cosmetic.
