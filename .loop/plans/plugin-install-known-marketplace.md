---
type: plan
title: 'Plan: plugin-install-known-marketplace'
description: "kmctl plugin install adds the okf marketplace from the source the operator's user or managed settings already list, instead of failing when that source differs from scaccogatto/okf-skills."
slug: plugin-install-known-marketplace
epic: plugin
depends_on: []
priority: 5
tags:
- plan
generated:
  by: process:loopctl/2.0.1.dev86+g9641fa018.d20261015
  at: '2026-10-15T14:27:49+00:00'
---

# plugin-install-known-marketplace

Relayed from: operator, 2026-10-15, running `kmctl plugin install` on their machine:
"refused: claude plugin marketplace add scaccogatto/okf-skills --scope project failed: ✘ Failed to add marketplace: Cannot add marketplace "scaccogatto": its source doesn't match its extraKnownMarketplaces entry in user or managed settings; add it from the source that entry lists, or change the entry."

## Intent

`install()` in `src/kmctl/plugin.py` always runs `claude plugin marketplace add scaccogatto/okf-skills --scope SCOPE`. When the user's settings (settings.json in claude's config folder: the one CLAUDE_CONFIG_DIR names, else .claude in the home folder) or the managed settings already declare a marketplace named `scaccogatto` under `extraKnownMarketplaces` with another source (a git URL, another repo, a local folder), claude refuses the add and kmctl stops. Skipping the add is not enough: the install then fails with `Dependency "okf@scaccogatto" ... not found`.

kmctl reads the `scaccogatto` entry when there is one and passes the argument claude accepts for it to `marketplace add`; with no entry it adds `scaccogatto/okf-skills` as now. It never edits the operator's settings. claude compares the add argument with the whole entry (round 1 plan review), so the argument carries every field the entry has:

- github: `repo`, plus `#ref` when the entry has a `ref`;
- git: `url`, plus `#ref` when the entry has a `ref`;
- url: `url`;
- directory: `path`.

An entry with any other field (a github `path`, a url's `headers` or `headersHelper`, and so on) or any other kind has no add argument that matches it. kmctl then stops before calling claude, with a message naming the settings file, the entry, and that the operator can add the marketplace by hand or change the entry.

kmctl picks the entry claude compares against, merging as claude does (round 2 plan review, from the claude 2.1.300 binary): the user settings first, then the managed settings, later wins and replaces the whole entry. The managed settings are managed-settings.json, then the json files in managed-settings.d sorted by name with dot-files skipped, each later file winning; they live in the etc/claude-code folder on Linux and in Library/Application Support/ClaudeCode on macOS, both at the file system root. So the last managed entry wins, and any managed entry beats the user entry. MDM and server-managed policies are not files kmctl can read; an entry there gives claude's own error, which kmctl passes on as today. The kmctl marketplace cannot clash this way: claude skips the check for a folder add (round 1 plan review).

Measured with an isolated `CLAUDE_CONFIG_DIR` and `HOME` whose user settings declare `scaccogatto` from `https://github.com/scaccogatto/okf-skills.git`: the current add fails 1 of 1 times with the operator's message, skipping it fails the install on the missing dependency, and adding from the entry's URL then `claude plugin install kmctl@kmctl --scope project` succeeds with okf as a dependency (1 of 1). The repro is spike:plugin-install-known-marketplace/1.

Done when tests show the add argument for each kind with and without a `ref`, the last of two managed files winning and any managed entry beating the user entry, and `scaccogatto/okf-skills` with no entry; an entry with a github `path` or an unknown kind gives a PluginError naming the file before claude runs; a real install in an isolated config whose user settings declare scaccogatto from a git URL succeeds; and the existing plugin install tests pass.

## Could invalidate this plan

- none
