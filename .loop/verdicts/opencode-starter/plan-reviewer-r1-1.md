---
type: verdict
title: 'Verdict: opencode-starter plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of opencode-starter: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-18T05:57:54+00:00'
slug: opencode-starter
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

Nothing found could break this plan. The two risks the plan leans on without listing them both hold. A copier validator on `kmctl_ref` can see `harnesses` and compare versions as numbers, and APM's `opencode` target installs on a machine with no OpenCode. The plan lists no risks ("none"), and that is fair for a template change this small.

## Checked

- Copier validator can see another answer and compare versions. In a scratch copy of kmctl-starter with copier 9.19.1, I added `OpenCode: opencode` and an `elif 'opencode' in harnesses and (kmctl_ref[1:].split('.') | map('int') | list) < [0, 5, 1]` branch to the validator. `copier copy --defaults --data 'harnesses=[opencode]' --data kmctl_ref=v0.5.0` exits 1 with the validator's message. v0.5.1 renders `targets: [opencode]`. `[claude]` with v0.5.0 still renders. Plain Jinja gives v0.10.0 ok and v0.4.9 old with this comparison, so the numeric split avoids the string-compare trap (a plain `kmctl_ref < 'v0.5.1'` would wrongly refuse v0.10.0).
- CI bootstrap on a runner with no OpenCode. spike:opencode-harness/4 and /6 ran `apm install` with apm-cli 0.33.0 and `targets: [opencode]` with no OpenCode binary. APM wrote `.opencode/agents/` and the `mcp` entry in `opencode.json`. The doctor checks for opencode (`opencode.agents`, `opencode.rules`, `opencode.okf-mcp`, `opencode.hook` in src/kmctl/doctor.py:592-671) read files only. Only `dep.opencode` needs the binary, and the plan leaves that check out of test.yml's filter. The plan's done-when (render plus `just bootstrap` locally and on GitHub) settles anything else.
- bump-kmctl.yml with a hand-set default. Its sed only rewrites the `  default: v...` line inside the `kmctl_ref:` block, so the new validator and help lines are untouched. Once v0.5.1 is the Latest GitHub Release (release-tag.yml publishes one, as for v0.5.0), the bump is a no-op, and later bumps raise the default above the v0.5.1 floor.
- template/justfile.jinja, apm.yml.jinja, README.md.jinja, test.yml and README.md match the plan's description of what each needs.

## Findings

None.

## Notes

- Order matters: push kmctl-starter's main only after v0.5.1 is the Latest release on JasperHG90/kmctl. If it lands while v0.5.0 is still Latest, test.yml on main fails (no v0.5.1 tag). The daily bump-kmctl would also open a PR that moves the default back to v0.5.0, because its sed writes whatever is Latest, even an older tag. The done-when (test workflow green on GitHub against v0.5.1) already forces this order.
- kmctl-starter's README still says "It needs kmctl v0.4.0 or later". Name the v0.5.1 floor for OpenCode there too, next to the `harnesses` row the plan already changes.
