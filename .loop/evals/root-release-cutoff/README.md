---
type: eval
title: 'Eval: root-release-cutoff'
description: 'Definition of done for root-release-cutoff: 6 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-15T05:33:15+00:00'
slug: root-release-cutoff
signoff:
  signer: delegated:jasperginn@gmail.com/implementer
  hash: 4a0e305f74a5998f8aebe004d88550f77155c8641894bb2f041cb728b2e0768d
  at: '2026-11-15T05:33:15+00:00'
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
- r5: The README, docs and hook hints install v0.12.2, the last root release, with no subdirectory, and every install line carries the subdirectory exactly when its ref is after v0.12.2.
  Fails when: an install line still names v0.12.1, a line at v0.12.2 carries the fragment, or a line after the cutoff lacks it
- r6: Every release.py test passes with the cutoff, including set's version, docs, copier and hook pinning.
  Fails when: any release.py test fails
