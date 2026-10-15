---
type: eval
title: 'Eval: claude-plugin'
description: 'Definition of done for claude-plugin: 4 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T10:57:15+00:00'
slug: claude-plugin
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: c735195ea90d7a99487460cb8d36ac2bc3d6a8668ef942cd605c2c18b611db7c
  at: '2026-10-15T10:57:15+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: The plugin declares exactly one hook, a SessionStart hook that runs kmctl briefing.
  Fails when: plugin/hooks/hooks.json has any event other than SessionStart, more than one hook, or a command that does not run kmctl briefing
- r2: Without kmctl on PATH, the hook exits 0 and prints how to install kmctl.
  Fails when: the hook command, run with a PATH that has no kmctl, exits nonzero or prints no install hint
- r3: The marketplace entry declares okf from marketplace scaccogatto and allowlists scaccogatto.
  Fails when: marketplace.json lacks the okf dependency with marketplace scaccogatto, or allowCrossMarketplaceDependenciesOn does not include scaccogatto
- r4: claude plugin validate accepts the plugin and the marketplace.
  Fails when: claude plugin validate reports an error for plugin/ or the root marketplace
