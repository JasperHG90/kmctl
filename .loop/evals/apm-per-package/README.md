---
type: eval
title: 'Eval: apm-per-package'
description: 'Definition of done for apm-per-package: 7 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-15T05:39:14+00:00'
slug: apm-per-package
signoff:
  signer: delegated:jasperginn@gmail.com/implementer
  hash: 82a68c91bc941e3c752fa394dbde2881c076d109b9079c83e44b4008b5efd1c2
  at: '2026-11-15T05:39:14+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl's APM package lives in packages/kmctl/apm (with its claude and antigravity sub-packages), kmaudit's version lives in packages/kmaudit/apm/apm.yml, and neither apm/ at the root nor packages/kmaudit/VERSION remains; both wheels build at the version their apm.yml names, kmctl's with its skills, agents and rules.
  Fails when: apm/ or packages/kmaudit/VERSION still exists, a wheel's version differs from its apm.yml, or kmctl's wheel lacks _skills, _agents or _rules
- r2: release.py reads kmctl's version from packages/kmctl/apm/apm.yml and kmaudit's from packages/kmaudit/apm/apm.yml, set writes them and pins the moved hook hints, and manifest falls back to apm/apm.yml on a commit from before the move; the release workflow stages the moved files and release-tag triggers on both apm.yml paths.
  Fails when: a version is read from or written to the old place, manifest fails on a pre-move commit, or a workflow names apm/apm.yml or packages/kmaudit/VERSION as a current path
- r3: new_entry writes path packages/kmctl/apm for this CLI; plugin patch and doctor recognise kmctl's entry and its sub-packages under path apm and packages/kmctl/apm; doctor's update fix for a project with {path: apm, ref: v0.12.2} names path packages/kmctl/apm and this CLI's ref.
  Fails when: an entry under either path goes unrecognised, new_entry writes path apm, or the update fix gives only a ref
- r4: The starter renders path apm for kmctl_ref v0.12.2 and older and path packages/kmctl/apm after it, and just bootstrap in a project generated at a release after the cutoff installs the package from packages/kmctl/apm with doctor passing.
  Fails when: a render names the wrong path for its ref, or the bootstrap fails
- r5: Every v* tag after the cutoff has packages/kmctl/apm/apm.yml and packages/kmctl/pyproject.toml and no apm/apm.yml; every older tag the reverse.
  Fails when: a tag's layout disagrees with the cutoff for either move
- r6: The Antigravity rules hook's files: pattern and scripts/sync_antigravity_rules.py work on packages/kmctl/apm, and the APM package, Antigravity and OpenCode tests read the moved package.
  Fails when: the hook's pattern does not match a rule under packages/kmctl/apm, the sync reads or writes apm/, or any of those tests fails
- r7: The repository's skills and audit tests read the skills and agents from packages/kmctl/apm.
  Fails when: any of those tests fails or still reads apm/
