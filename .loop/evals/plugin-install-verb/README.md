---
type: eval
title: 'Eval: plugin-install-verb'
description: 'Definition of done for plugin-install-verb: 6 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev1+g4552fe226.d20261015
  at: '2026-10-15T11:06:20+00:00'
slug: plugin-install-verb
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 227632f0bfcf3093c4784702fa1fc968e487e78455b7442dec9eec4134a55a67
  at: '2026-10-15T11:06:20+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: With an isolated Claude config dir, kmctl plugin install adds the scaccogatto marketplace when missing and installs kmctl's plugin with okf at the chosen scope.
  Fails when: claude plugin list --json lacks kmctl or okf at that scope afterwards, or the command exits nonzero
- r2: A second install at the same version changes nothing.
  Fails when: the second run exits nonzero, or the plugin list or the staged folder's content differs
- r3: kmctl writes its own version into the staged plugin.json, and after install claude lists that version.
  Fails when: the staged plugin.json version differs from kmctl's, or the listed version differs
- r4: kmctl plugin update after a version bump keeps the marketplace at the same path and ends with the new version listed.
  Fails when: the registered marketplace path changes, or claude plugin list --json does not show the bumped version
- r5: kmctl plugin status reports a version mismatch, and says to run kmctl plugin install when the declared marketplace path does not exist.
  Fails when: status reports no mismatch after the staged copy changes, or gives no install hint for a missing path
- r6: The wheel carries plugin/ and the marketplace file as package data.
  Fails when: a built wheel lacks the plugin manifest, hooks.json or the marketplace file
