---
type: verdict
title: 'Verdict: claude-plugin reviewer round 1'
description: 'reviewer verdict for round 1 of claude-plugin: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T11:00:00+00:00'
slug: claude-plugin
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The plugin, marketplace and hook do what the plan asks. One SessionStart hook relays `kmctl briefing` and always exits 0. The marketplace entry declares okf@scaccogatto and allowlists scaccogatto, as ADR 0003 says. `claude plugin validate` accepts both manifests. The one real defect is that the install hint names `kmctl plugin install`, which does not exist yet. Dropping that clause fixes it, so it does not need another round. The other two findings ask for a stronger test and a hook timeout.

## Checked

- The staged change in the worktree (it is staged, not committed): every file read in full.
- `loopctl gate stamp` from the worktree: lint, format and tests pass, eval rows r1 to r4 pass, "stamp green: d60c1b0b...".
- I ran `claude plugin validate plugin` and `claude plugin validate .` myself (Claude Code 2.1.300). Both pass.
- r1: the test checks that the only event is SessionStart, that there is exactly one entry and one hook (through the list unpacking in `_hook_command`), and that the command contains `kmctl briefing`. This matches fails_when, with the gap noted in f2.
- r2: the test runs the real command under /bin/sh with PATH=/usr/bin:/bin and checks exit 0 and the "uv tool install" hint. If kmctl were in /usr/bin, the hint check would fail rather than pass by mistake.
- r3: the test asserts the exact dependency object, the allowlist and the source.
- r4: the test is real, but it skips when no claude CLI is on PATH, so CI without claude does not check it. It ran here.
- Consistency: I1 is enforced by the plugin tests and I3 by tests/test_briefing.py::test_briefing_word_budget, which exists and asserts the budget. Both meet the manifesto-invariants rule. ADR 0003 and ADR 0004 match the change. `kmctl --help` shows no `plugin` command.

## Findings

- f1: the hint text in hooks.json names `kmctl plugin install`. That verb is not shipped (see `kmctl --help`), and the cli-version-floor rule forbids the hook naming verbs that are not shipped. It is non-blocking because the fix is to delete one clause, or to add it back in plugin-install-verb along with the verb.
- f2: the one-hook check looks only at hooks.json. It is non-blocking because asserting that plugin.json has no `hooks` key is a one-line addition.
- f3: there is no hook timeout. It is non-blocking hardening, because the default timeout still ends the hook.
