---
type: eval
title: 'Eval: repo-rename'
description: 'Definition of done for repo-rename: 4 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.2.1.dev14+g22f6ca3aa.d20261017
  at: '2026-10-17T18:53:02+00:00'
slug: repo-rename
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 2e698b52ccee749a0c9faefcc9cda852f451c1c87b30479a5ab2823f1850c543
  at: '2026-10-17T18:53:02+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: outside .okf/decisions/ and .loop/, the old repository name appears only in src/kmctl/plugin.py, tests, and as the old package name JasperHG90/Knowledge-management/apm in docs/how-to/install-kmctl-with-apm.md and docs/reference/commands.md
  Fails when: git ls-files lists another file whose text contains jasperhg90/knowledge-management in any case, or one of those two docs pages names it other than as JasperHG90/Knowledge-management/apm
- r2: the apm.yml entry kmctl suggests, the hooks' install lines and the release script's install and uses: patterns name JasperHG90/kmctl
  Fails when: new_entry()'s git is not https://github.com/JasperHG90/kmctl.git, either harness's hook command lacks git+https://github.com/JasperHG90/kmctl, or release.py set does not move a uv tool install or uses: line naming JasperHG90/kmctl
- r3: kmctl plugin patch still recognises an install made from the old name: a v0.3.0-layout lock and a hand-written JasperHG90/Knowledge-management/apm entry are refused with the apm uninstall to run, as they are from the new name
  Fails when: patch on a v0.3.0-layout lock, or on an apm.yml string entry, from either repository name does not raise PluginError naming apm uninstall
- r4: release.py set leaves the Older installs example's JasperHG90/Knowledge-management/apm#v0.3.0 entry as it is and does not refuse for want of an APM pin
  Fails when: after set_version on a copy of the repository, docs/how-to/install-kmctl-with-apm.md no longer holds JasperHG90/Knowledge-management/apm#v0.3.0, or set_version raises ReleaseRefused
