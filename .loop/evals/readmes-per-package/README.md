---
type: eval
title: 'Eval: readmes-per-package'
description: 'Definition of done for readmes-per-package: 5 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-15T18:48:17+00:00'
slug: readmes-per-package
signoff:
  signer: delegated:jasperginn@gmail.com/implementer
  hash: dce6e90d926d13cfe0c43dab3c124dca971a3ce4a2dbad7e9d589baa10624014
  at: '2026-11-15T18:48:17+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: The root README is a short map (under 80 lines) that links packages/kmctl/README.md, packages/kmaudit/README.md and docs/, and every relative link in the three READMEs resolves.
  Fails when: the root README runs to 80 lines or more, misses a link to either package README or docs/, or any README link points at a missing file
- r2: packages/kmctl/README.md tells a user how to install and use kmctl: the CLI install line, the apm.yml entry, the harness sections, upgrade and remove, and links into docs/; the tests that read kmctl's install lines read them there.
  Fails when: kmctl's README lacks any of those, or a docs test still reads kmctl's install lines from the root README
- r3: kmaudit's command reference lives at docs/reference/kmaudit-commands.md with docs front matter, documents every kmaudit MCP tool and command, packages/kmaudit/docs/ is gone, and kmctl check passes with the indexes regenerated.
  Fails when: packages/kmaudit/docs/ remains, the page lacks a tool or command, or kmctl check reports an error or warning
- r4: release.py set pins kmctl's install lines in packages/kmctl/README.md and set --package kmaudit pins the tracing line in docs/reference/kmaudit-commands.md; release_paths gives docs pages named kmaudit-* to kmaudit and not kmctl; the release workflow stages the moved files.
  Fails when: a pin targets an old path, a kmaudit docs page counts for kmctl, or the workflow stages a path that no longer exists
- r5: The docs install-line check tells kmaudit's lines from kmctl's, and passes on a copy of the tree after set --package kmaudit 0.2.0.
  Fails when: a pinned kmaudit line is held to kmctl's subdirectory, or the check fails after a kmaudit pin
