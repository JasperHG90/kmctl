---
type: verdict
title: 'Verdict: plugin-patch plan-reviewer round 3'
description: 'plan-reviewer verdict for round 3 of plugin-patch: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T12:59:45+00:00'
slug: plugin-patch
pass: plan-reviewer
round: 3
body_schema: verdict/1
---

## Summary

p3 is resolved. Spike apm-hands-back/5 shows that at user scope, once kmctl's
unrecorded hook group and the stale okf-bundle are removed, a second
`apm install -g --target claude` writes exactly one APM-recorded SessionStart
hook into CLAUDE_CONFIG_DIR/settings.json and the package's okf-bundle into
CLAUDE_CONFIG_DIR/.claude.json, and leaves other servers alone. That is the
cleanup-then-reinstall order patch depends on. The plan now runs the old-form
check before the "no kmctl package" refusal. No open risk could break the
plan.

## Checked

- The plan, its eval folder, and my round 2 verdict (plan-reviewer-r2-1.md).
- Spike apm-hands-back/5: README outcome, run.json (exit 0, not timed out),
  stdout.txt and files/spike-user.sh. The script sets HOME and
  CLAUDE_CONFIG_DIR to scratch, seeds a kmctl-style user install (a matcher-less
  hook group and an older-pin okf-bundle next to another server), runs
  `apm install -g`, removes the old hook and okf-bundle, and installs again.
  stdout shows "kmctl hooks: 1 | recorded by APM: True | okf-bundle: package |
  mine: True" after the second install.
- Spike plugin-patch/1 still covers the same order at project scope (p1).
- The plan's Intent now says patch "first checks for an older entry form, and
  then refuses ... when the lock lists no kmctl package", which settles my
  round 2 note.

## Findings

- p1 (resolved): spike:plugin-patch/1, unchanged.
- p2 (resolved): unchanged.
- p3 (resolved): spike:apm-hands-back/5 shows APM writes the hook and
  okf-bundle at user scope after patch's cleanup.

## Notes

The same spike shows `apm uninstall -g` leaves okf-bundle in
CLAUDE_CONFIG_DIR/.claude.json, unlike project scope, where uninstall removes
it. The plan's removal steps (`apm uninstall`, `kmctl plugin patch --undo`)
would leave that server behind at user scope. That does not break the plan:
the "It worked when" check is in a project-scope consumer, and the build can
handle it in the README's removal section (for example, a
`claude mcp remove --scope user okf-bundle` line) or leave it as a known APM
gap. The eval has rows now; the build should make sure one covers the
project-scope "no kmctl file left" check.
