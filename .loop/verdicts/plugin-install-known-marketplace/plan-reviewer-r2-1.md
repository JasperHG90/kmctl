---
type: verdict
title: 'Verdict: plugin-install-known-marketplace plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of plugin-install-known-marketplace: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T14:36:44+00:00'
slug: plugin-install-known-marketplace
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

The revision fixes all three round 1 findings: `#ref` is carried for github and
git, any extra field or kind stops before claude runs, and the managed files are
named. Managed over user is the order claude uses. One part of the precedence is
wrong, though. Inside the managed files claude lets the last file win, not the
first (p4). This is a one-line change to the plan and its eval row, not a
rethink.

## Checked

Read from the claude 2.1.300 binary (`~/.local/share/claude/versions/2.1.300`).
I did not touch the real ~/.claude or /etc.

- The refusal is `dnt` calling `bnt(addedSource, declared)`, where `declared` is
  `xw()[name].source`. `xw` walks the operator sources in `Es` order (user, flag,
  policy; project and local are dropped through `qp`) and merges them with
  `LUt(a, b) = {...a, ...b}`. Later wins, and the entry for one name is replaced
  whole. So a managed entry replaces the user entry, and claude compares against
  the managed one. The plan's managed-before-user order is right.
- `UDo` (file-based managed settings): it reads `managed-settings.json` first,
  then `readdirSync(managed-settings.d)` filtered to non-dot `*.json` files (or
  symlinks), sorted by name, and merges each one into the result with
  `qj(merged, s, A3)`. A3 shallow-merges `extraKnownMarketplaces` with LUt. So
  the effective entry comes from the last sorted d-file that names scaccogatto,
  or from managed-settings.json when no d-file does.
- Paths: `tb()` gives `/etc/claude-code` (Linux), `/Library/Application
  Support/ClaudeCode` (macOS), and `C:\Program Files\ClaudeCode` (Windows). This
  matches the plan.
- `bnt`: the check is skipped when the added source is a directory or file
  (`If(e)`). url, git and npm use a full-equality `Un`. github requires the
  declared entry to be github too and compares with the repo lowercased. So the
  rule "every field must match" holds, and extra fields stop the add.
- A url entry with headers does exist. The url source schema has `url`, an
  optional `headers` ("Custom HTTP headers (e.g., for authentication)") and an
  optional `headersHelper`. Either one makes the bare-url add fail `Un`, so
  kmctl must stop on `headersHelper` as well as `headers`. The plan's
  "any other field" rule covers both.
- The name lookup `i_` is an exact `hasOwn`, so matching on the key
  `scaccogatto` alone is right.
- The policy tier (`MO`) uses the highest present managed source (remote, then
  MDM, then file) unless `managedSourcesBehavior` is "merge". The plan already
  says it passes claude's own error through for MDM and server-managed policy.

## Findings

- p1 resolved: github and git carry `#ref`.
- p2 resolved: a github `path`, `headers` or any other field, or any other kind,
  raises PluginError before claude runs.
- p3 resolved: the managed files and both OS folders are named, and MDM and
  server-managed policy are addressed.
- p4 (open): the plan says to use "the first scaccogatto entry it finds" across
  managed-settings.json and managed-settings.d. Claude does the opposite. A
  d-file overrides managed-settings.json, and a later d-file in sorted name
  order overrides an earlier one. The plan should say: within the managed files,
  the last of managed-settings.json then sorted d/*.json wins; then managed over
  user. Row r2 should check this. Its fails_when catches a d-file being ignored,
  but not the wrong one of two being chosen.

## Notes

This is an edge case: when server-managed or MDM policy is present, claude
ignores the managed files. kmctl may then build its argument from a file entry
that claude never reads. If the user settings declare scaccogatto too, claude
refuses, and that error passes through as it does today. If they do not, nothing
is declared and the add works. Either way the plan does not break. It is worth a
line in the PluginError or the docs, but it is not a finding.
