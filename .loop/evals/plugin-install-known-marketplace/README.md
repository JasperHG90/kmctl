---
type: eval
title: 'Eval: plugin-install-known-marketplace'
description: 'Definition of done for plugin-install-known-marketplace: 5 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T14:37:10+00:00'
slug: plugin-install-known-marketplace
signoff:
  signer: delegated:jasperginn@gmail.com/claude-opus-5-5
  hash: eba5e65606e4b3c2b0d456362a5c2f84530733ca58a5287923fd49ab4f1865a4
  at: '2026-10-15T14:37:10+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: The okf add argument matches a scaccogatto settings entry: repo[#ref] for github, url[#ref] for git, url for url, path for directory, and scaccogatto/okf-skills when no entry exists.
  Fails when: for any kind, with or without a ref, the argument kmctl passes to marketplace add is not the one listed, or with no entry it is not scaccogatto/okf-skills
- r2: kmctl picks the entry claude compares against: managed-settings.json, then managed-settings.d/*.json sorted by name with dot-files skipped, the last one winning, and any managed entry over the user entry.
  Fails when: with entries in managed-settings.json and a managed-settings.d file, kmctl uses the earlier one; with two managed-settings.d files it uses the one that sorts first; it reads a dot-file; or with a managed and a user entry it uses the user one
- r3: An entry no add argument can match (a github path, a url's headers or headersHelper, or an unknown kind) stops the install before claude runs, with a message naming the settings file.
  Fails when: such an entry does not raise PluginError, the message does not name the file, or claude is called
- r4: With user settings that declare scaccogatto from a git URL, kmctl plugin install succeeds at project scope with okf installed, without editing the settings.
  Fails when: in an isolated CLAUDE_CONFIG_DIR, HOME and XDG_DATA_HOME whose user settings declare scaccogatto from https://github.com/scaccogatto/okf-skills.git, kmctl plugin install exits nonzero, okf is not installed, or the user settings file changed
- r5: The other plugin install tests still pass.
  Fails when: any test in tests/test_plugin_install.py or tests/test_plugin.py fails
