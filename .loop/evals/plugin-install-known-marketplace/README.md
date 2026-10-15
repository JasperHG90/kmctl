---
type: eval
title: 'Eval: plugin-install-known-marketplace'
description: 'Definition of done for plugin-install-known-marketplace: 4 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T14:28:52+00:00'
slug: plugin-install-known-marketplace
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: 6fe0b461d4699f9dc727dbb841fa164077047619b77919c0d4bcce8ca1e6726a
  at: '2026-10-15T14:28:52+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmctl picks the okf marketplace source from a scaccogatto entry in the user or managed settings: repo for github, url for git and url, path for directory, and scaccogatto/okf-skills when no entry exists.
  Fails when: for any of those kinds, in the user settings or the managed settings file, the source kmctl passes to marketplace add is not the entry's own value, or with no entry it is not scaccogatto/okf-skills
- r2: A scaccogatto entry of a source kind kmctl cannot pass stops the install with a message naming the settings file.
  Fails when: such an entry does not raise PluginError, or the message does not name the settings file
- r3: With user settings that declare scaccogatto from a git URL, kmctl plugin install succeeds at project scope with okf installed, without editing the settings.
  Fails when: in an isolated CLAUDE_CONFIG_DIR, HOME and XDG_DATA_HOME whose user settings declare scaccogatto from https://github.com/scaccogatto/okf-skills.git, kmctl plugin install exits nonzero, okf is not installed, or the user settings file changed
- r4: The other plugin install tests still pass.
  Fails when: any test in tests/test_plugin_install.py or tests/test_plugin.py fails
