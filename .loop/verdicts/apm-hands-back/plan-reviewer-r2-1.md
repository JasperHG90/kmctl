---
type: verdict
title: 'Verdict: apm-hands-back plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of apm-hands-back: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T13:00:02+00:00'
slug: apm-hands-back
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

p1 is resolved. Spike 5 shows that `apm install -g --target claude`, with a
split package named in ~/.apm/apm.yml, writes the recorded SessionStart hook
and the package's okf-bundle into $CLAUDE_CONFIG_DIR. Over a user install
written by today's kmctl it leaves the same duplicates as at project scope,
and the plan's migration step clears them. The plan now says all of this,
including the `apm uninstall -g` gap. I found no other risk that could break
the plan. Verdict: pass.

## Checked

- Spike 4: rc 1 from APM because the spike's antigravity sub-package had no
  `.apm/` folder. The script diff against spike 5 is only that folder and one
  rule file, so spike 4 failed because of the spike's own setup, not because
  of APM. It also shows APM resolves every sub-package even with `--target
  claude`, which the plan now folds in ("each sub-package keeps an `.apm/`
  folder").
- Spike 5 (script, stdout, run.json, exit 0): the first `install -g` over a
  kmctl-written user install gave 2 kmctl hooks (one recorded by APM), kept
  the stale okf-bundle ("already configured") and kept the user's other
  server. After removing kmctl's unrecorded group and the stale okf-bundle, a
  second install left 1 recorded hook and the package's okf-bundle. `apm
  uninstall -g` removed the hook and skill but left okf-bundle. This matches
  the plan's fourth risk entry and its migration paragraph.
- The spike used kmctl's own `plugin.hook_entry()` and
  `plugin.okf_mcp_launcher()`, and the same `install --target claude -g`
  shape that `apm_install_args` builds (src/kmctl/plugin.py:613), so the
  evidence matches what kmctl will run.
- `Scope` is only project or user (src/kmctl/plugin.py:33), so no third scope
  is left uncovered.
- Spike 1 stdout: "left after uninstall: 0" after the project-scope
  uninstall, which settles my round 1 note on project-scope MCP cleanup.

## Findings

- p1: resolved by spike 5 and the plan's new user-scope sentences.

## Notes

- Today `install_mcp` and `merge_mcp` (src/kmctl/plugin.py:841, 873) add no
  okf-bundle when the user already has another okf server under a different
  name. APM will add okf-bundle anyway, so such a user ends up with two okf
  servers. This changes behaviour but does not break the plan. Doctor or the
  new ADR could name it. It is a build-time detail.
- The `allowExecutables` note from round 1 still applies: such a consumer
  gets no hook or server from APM. Worth a line in the new ADR.
- The eval still has no rows.
