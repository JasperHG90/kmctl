---
type: verdict
title: 'Verdict: apm-only-install reviewer round 2'
description: 'reviewer verdict for round 2 of apm-only-install: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-16T21:18:06+00:00'
slug: apm-only-install
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

f1 is fixed. The verb table row in the architecture overview now gives the same order as the code: apm uninstall of an old entry, write apm.yml, apm install through uvx, and only after that succeeds remove the old claude plugin, then the hook and .mcp.json. The gates and all eval rows pass on my own stamp. f2 stays open as non-blocking hardening, deferred to stub ticket apm-only-install-reviewer-f2.

## Checked

- Read the row at .okf/architecture/overview.md:146 against install() in src/kmctl/plugin.py (lines 862 to 917). The order matches: _preflight, remove_old_apm_entry, write_manifest, _apm_run with _require, the skip check, remove_old_plugin, merge_hook, install_mcp. The row also says it "only once that succeeds removes the old claude plugin", which matches the docstring and ADR 0014.
- The new `kmctl plugin status` row says it writes nothing and reads apm.lock.yaml and .claude/settings.json, which matches status().
- Re-ran `loopctl gate stamp` from the worktree with HOME, CLAUDE_CONFIG_DIR and XDG_DATA_HOME pointed at scratch folders: "stamp green: b85123906adf07c9368350a652e7103e74ad78e3307539ea8f150bad6d975c13". lint, format, tests, integration and rows r1 to r12 with r6b all passed. The fingerprint matches the one this round is bound to. git had no identity, as expected, so the state commit was deferred.

## Findings

- f1 (resolved): the overview's verb table row for `kmctl plugin install`, `update` now puts the old-plugin removal after a successful apm install, matching the code.
- f2 (open, hardening, non-blocking): unchanged since round 1 and not sent back this round; it is deferred to stub ticket apm-only-install-reviewer-f2.
