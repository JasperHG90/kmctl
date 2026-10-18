---
type: verdict
title: 'Verdict: opencode-starter reviewer round 1'
description: 'reviewer verdict for round 1 of opencode-starter: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-18T07:13:55+00:00'
slug: opencode-starter
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. In kmctl, README.md's kmctl-starter paragraph names Claude Code, Antigravity and OpenCode. In kmctl-starter, copier offers OpenCode, defaults kmctl_ref to v0.5.1 and refuses OpenCode with an older tag. The READMEs say what an OpenCode user needs and agree with kmctl's docs. The test matrix covers both OpenCode entries, and v0.3.0 is a plain tag with a release on 089df3c. Nothing blocks.

## Checked

- Gates: `loopctl gate stamp` from the worktree passed lint, format, tests, integration and eval rows r1, r2 and r3. Result: "stamp green: 67f26c3079142fd68df814c74ab8bfb42958c3b815b92a5997342ac075bb0649".
- Diff: the kmctl worktree has one uncommitted change, README.md lines 55-56. I read kmctl-starter commits 0796415 and 089df3c in full: copier.yml, README.md, template/README.md.jinja and .github/workflows/test.yml.
- r1-r3 commands: r1 looks only at the kmctl-starter paragraph. r2 checks apm.yml's targets and ref, the justfile pin and the ci.yml pin. r3 needs a non-zero copier exit whose output names v0.5.1, then a successful [claude] render at v0.5.0. I ran the refusal myself: copier exits with "Validation error for question 'kmctl_ref': OpenCode needs kmctl v0.5.1 or later ... not v0.5.0." I also checked the validator's numeric comparison at the edges: [claude, opencode] renders at v0.5.2, v0.10.0 and v1.0.0, so it compares integers, not strings.
- r4 (judgment): `gh run view 39106472889` shows headSha 089df3c, conclusion success, and all five render jobs green, [opencode] and [claude, antigravity, opencode] among them. In 089df3c the two bootstrap steps carry `if: false` under a comment saying kmctl is private and naming the lines to delete once it is public. I ran the author's run.sh myself in a fresh scratch dir for [opencode] and [claude, antigravity, opencode] against the local starter HEAD. Both bootstrapped kmctl 0.5.1 and wrote the three OpenCode agents, the four rules and kmctl.js. Doctor's only failing checks were dep.opencode for the first, and dep.opencode plus antigravity.trust for the second, all inside the filter. This host has claude and agy installed, so those two checks passed. Pass.
- r5 (judgment): the starter README's harnesses row names OpenCode (2.x only). Its AGENTS.md row says OpenCode reads AGENTS.md directly. The "needs" line adds v0.5.1 for OpenCode. The rendered README for [opencode] covers all four points: start a new session, 2.x only, all four rules load in every session, and run `just install` again after any `apm install`. Each matches kmctl's README (OpenCode section: four rules, 2.x only, new session), docs/how-to/install-kmctl-with-apm.md:92 and docs/reference/commands.md:455 (apm install puts APM's agents back). Pass.
- r6 (judgment): `git cat-file -t v0.3.0` would be `commit`; the GitHub refs API reports refs/tags/v0.3.0 -> object type commit 089df3c, so it is a plain tag like v0.1.0 to v0.2.1. The v0.3.0 release (Latest, one line of notes) was published 2026-10-18T07:07:53Z, after kmctl v0.5.1 (Latest, 05:58:34Z). `uvx copier copy --defaults ... harnesses=[opencode] gh:JasperHG90/kmctl-starter` rendered with _commit v0.3.0, targets [opencode] and ref v0.5.1. Pass.
- Consistency: kmctl README line 70 already lists OpenCode among supported harnesses, and no docs/ or .okf/ page mentions kmctl-starter, so the new wording contradicts nothing.

## Findings

None.

## Notes

The copier label is `OpenCode (2.x)`, not the plan's `OpenCode`. That is a sound departure: it puts the 2.x-only limit at the moment of choice, and the README row says the same. When copier runs with --defaults and refuses a value, it prints a Python traceback before the validator message. That is copier's own behavior, and the existing branch validator does the same.
