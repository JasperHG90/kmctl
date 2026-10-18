---
type: plan
title: 'Plan: opencode-starter'
description: kmctl-starter offers OpenCode as a harness, pinned to the first kmctl release that supports it.
tags:
- plan
slug: opencode-starter
epic: multi-harness
depends_on:
- opencode-harness
priority: 2
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-18T04:13:13+00:00'
---

# opencode-starter

Relayed from: none

## Intent

The operator asked (2026-10-17) to "also update kmctl-starter" when OpenCode
became a harness, chose to make it its own ticket after opencode-harness,
and on 2026-10-18 to push main and cut the release it needs. kmctl-starter
(/home/vscode/kmctl-starter, a separate git repository, committed and pushed
there as repo-rename did) is the copier template `README.md` points new
repositories at. Its `harnesses` question offers Claude Code and
Antigravity, and `kmctl_ref` defaults to v0.5.0, which predates OpenCode
support. The first kmctl release with it is v0.5.1, cut from main after
opencode-harness and opencode-harness-reviewer-f6 landed.

What changes, in kmctl-starter:

- copier.yml: `harnesses` gains `OpenCode: opencode`. `kmctl_ref`
  defaults to v0.5.1. Its validator also refuses a tag older than v0.5.1
  when opencode is picked, naming v0.5.1, so an old pin cannot install
  agents OpenCode skips. Its help says so.
- README.md's `harnesses` row names OpenCode (2.x only); the
  `AGENTS.md` row says OpenCode reads `AGENTS.md` directly.
- template/README.md.jinja, for an OpenCode project: start a new OpenCode
  session after `just bootstrap`; kmctl supports OpenCode 2.x only; every
  kmctl rule loads in every session; run `just install` (apm install, then
  kmctl plugin patch) again after any `apm install`.
- .github/workflows/test.yml: the matrix gains `[opencode]` and
  `[claude, antigravity, opencode]`; the doctor filter leaves out
  `dep.opencode`, since the runner has no OpenCode.
- README.md's "needs kmctl v0.4.0 or later" also says OpenCode needs
  v0.5.1 or later.
- A release tag, v0.1.2, on the commit that holds this. `uvx copier copy
  gh:JasperHG90/kmctl-starter` renders the newest tag (v0.1.1 today), so
  without it no one gets the OpenCode choice. The commit and tag are pushed
  only after kmctl v0.5.1 is its Latest release, so the starter's test.yml
  and bump-kmctl.yml both see v0.5.1.

In kmctl: README.md's kmctl-starter paragraph names the harnesses it sets
up, OpenCode among them.

Measured on 2026-10-18: harness choices the starter offers, 2 of the 3
kmctl supports; after, 3 of 3. A project rendered today with opencode
cannot exist (copier refuses the choice).

Done when: in kmctl-starter, copier renders and `just bootstrap` succeeds
for `[opencode]` and `[claude, antigravity, opencode]` against v0.5.1 with
`kmctl doctor` failing only on `dep.opencode` (the same steps as its
test.yml, run locally), copier refuses opencode with kmctl_ref v0.5.0, and
the starter's test workflow passes on GitHub for every matrix entry, and
`uvx copier copy gh:JasperHG90/kmctl-starter` offers OpenCode (tag v0.1.2).

## Could invalidate this plan

- none
