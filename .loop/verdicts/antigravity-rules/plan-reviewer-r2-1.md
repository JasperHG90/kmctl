---
type: verdict
title: 'Verdict: antigravity-rules plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of antigravity-rules: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T06:32:44+00:00'
slug: antigravity-rules
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

The listed risk is settled. Spike 2 shows that after kmctl's rule copies are
deleted from `.agents/rules/`, a second `apm install` writes them back with no
"local files exist" skip, and `apm uninstall` exits 0 and leaves no files.
That fits the existing SKIP_LINE check in `install`. One risk the plan does
not list could still leave the main rule dead: no test has shown agy matching
a glob that goes through the hidden `.okf/` folder. That needs one live agy
check, so this verdict is fail, not reject.

## Checked

- Spikes 1 and 2 (README, stdout, the script, run.json). The empty
  "deleted:" line shows the `rm` worked before the reinstall. Spike 1 exited
  1 only because its grep counted unrelated "Skipped" info lines. Spike 2
  narrowed the grep to "local files exist" and passed.
- `src/kmctl/antigravity.py`: `plugin_files`, `write_plugin`, `agents_dir`
  and `compare_plugin`. Adding `rules/NAME.md` entries fits the folder model,
  and doctor's `antigravity.plugin` check picks them up through
  `plugin_problems` with no new code.
- `src/kmctl/plugin.py` `install`: `write_plugin` runs after APM's install
  and the skip check, so deleting kmctl's `.agents/rules/` copies there comes
  after APM has written them. `kmctl_package` gives the lock's
  `deployed_files` that the deletion needs.
- `src/kmctl/doctor.py` `_deployed`: it checks every lock path under
  `.agents/`, so once the copies are deleted, `antigravity.files` would fail
  unless it leaves out kmctl's rule paths. The plan covers this.
- `pyproject.toml` force-include ships only `_skills` and `_agents` today.
  The plan adds the instructions beside them.
- The four `apm/.apm/instructions/*.instructions.md` files: `applyTo` is
  already a comma string, there are no relative links (APM's `resolve_links`
  would have rewritten them), and no rule lacks `applyTo`.
- APM 0.33.0 `instruction_integrator.py`: both `_convert_to_windsurf_rules`
  and `_convert_to_antigravity_rules` write a YAML list for more than one
  glob, which confirms the plan's premise.
- agy docs (`plugins.md`, `rules.md`): plugin `rules/` are merged into the
  active rule set. The docs say nothing about glob syntax, so the plan's
  glob claims rest on the live run.

## Findings

- p1: `**/.okf/**` has not been shown to match through the hidden `.okf/`
  folder in agy. okf-bundle depends on it alone, and the success check would
  not catch a rule that never fires. See the claim for the question to settle
  live.

## Notes

Adding `**/` widens `README.md` to any README in the tree, and `src/**` to any
nested `src/`. That changes what the rules cover a little, but it does not
break the plan. The ticket is small enough not to split.
