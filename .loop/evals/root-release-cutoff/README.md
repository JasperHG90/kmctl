---
type: eval
title: 'Eval: root-release-cutoff'
description: 'Definition of done for root-release-cutoff: 5 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-15T05:28:15+00:00'
slug: root-release-cutoff
signoff:
  signer: delegated:jasperginn@gmail.com/implementer
  hash: 0ef1bd5ced8c0d6f2b32a7ecba5c87660d38120b6b5d8e91638a046989cbca90
  at: '2026-11-15T05:28:15+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: The pin hand-off and the plugin's hook hint build kmctl from the root for v0.12.2 and older, and from packages/kmctl for later tags, pre-releases after v0.12.2 and refs that are not release tags; both decide it through one cutoff constant in plugin.py.
  Fails when: v0.12.1 or v0.12.2 gets the subdirectory, v0.12.3rc1 or v0.13.0 lacks it, the hook hint disagrees with the hand-off, or hooks.json no longer equals the hook command
- r2: The starter renders kmctl_src without the subdirectory for kmctl_ref v0.12.1 and v0.12.2, and with it for v0.12.3rc1 and v0.13.0.
  Fails when: a render at v0.12.2 or older carries the subdirectory, or a later one lacks it
- r3: release.py set writes the subdirectory on every install line and hook hint only for a version after the cutoff, removes it when re-pinning to a version at or below it, writes it once over repeated runs, and its cutoff equals plugin.py's.
  Fails when: set 0.12.2 leaves a fragment, set 0.13.0 misses one or doubles it, or the two cutoffs differ
- r4: Every v* tag in the clone that has no packages/kmctl/pyproject.toml is at or below the cutoff, and every tag that has it is above.
  Fails when: a root-layout tag is newer than the cutoff, or a packages-layout tag is not
- r5: This branch's version files and install lines read v0.12.2, the last root release, with no subdirectory, and the docs and ADR 0044 name v0.12.2 as the cutoff.
  Fails when: a version file or install line still names v0.12.1, an install line at v0.12.2 carries the fragment, or the docs or ADR name v0.12.1 as the last root release
