---
type: eval
title: 'Eval: plugin-install-known-marketplace'
description: 'Definition of done for plugin-install-known-marketplace: 5 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T14:32:15+00:00'
slug: plugin-install-known-marketplace
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: db57a3644182dd839fd188bc59e9d6d9191e76fac10386cb38a1c7e58357891f
  at: '2026-10-15T14:32:15+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: The okf add argument matches a scaccogatto settings entry: repo[#ref] for github, url[#ref] for git, url for url, path for directory, and scaccogatto/okf-skills when no entry exists.
  Fails when: for any kind, with or without a ref, the argument kmctl passes to marketplace add is not the one listed, or with no entry it is not scaccogatto/okf-skills
- r2: A managed settings entry (managed-settings.json or a json file in managed-settings.d) wins over the user settings entry.
  Fails when: with entries in both, kmctl uses the user entry, or ignores a managed-settings.d file
- r3: An entry no add argument can match (a github path, headers, or an unknown kind) stops the install before claude runs, with a message naming the settings file.
  Fails when: such an entry does not raise PluginError, the message does not name the file, or claude is called
- r4: With user settings that declare scaccogatto from a git URL, kmctl plugin install succeeds at project scope with okf installed, without editing the settings.
  Fails when: in an isolated CLAUDE_CONFIG_DIR, HOME and XDG_DATA_HOME whose user settings declare scaccogatto from https://github.com/scaccogatto/okf-skills.git, kmctl plugin install exits nonzero, okf is not installed, or the user settings file changed
- r5: The other plugin install tests still pass.
  Fails when: any test in tests/test_plugin_install.py or tests/test_plugin.py fails
