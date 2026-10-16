---
type: verdict
title: 'Verdict: kmctl-doctor reviewer round 1'
description: 'reviewer verdict for round 1 of kmctl-doctor: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-16T22:10:01+00:00'
slug: kmctl-doctor
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The doctor verb is well built. It is read only and makes one offline call. Harness detection does not depend on any single piece, plugin status is fully removed, and every eval row has a test that checks what the row says must not happen. All gates pass, and so does the real APM integration run. One finding blocks: the fix line for claude.old-plugin, when the plugin is okf@scaccogatto, points at a command that cannot remove it, so doctor can fail for good with advice that does nothing. One design finding does not block: a new runtime HTTP dependency that only --online uses.

## Checked

- Ran `loopctl gate stamp` in the worktree: lint, format, tests and integration all pass, and so do rows r1 through r8. Result: `stamp green: ddb5540e2a8eed89a872e760eae4e1832299122e12570dc1ab2c2fb4311e6f97`. Re-ran r7 with `-rs` to confirm it runs rather than skips: 1 passed.
- Read all of src/kmctl/doctor.py, the diffs to plugin.py, antigravity.py and __init__.py, tests/test_doctor.py, the test diffs, and the doc and .okf diffs.
- r1: test_all_ok_* checks the exact ordered id list, that every line is ok, exit code 0 and empty stderr.
- r2: the BREAKS cases cover every piece the row lists: a skill, a sha256 change, the hook, a plugin file that is missing, extra or edited, the plugin folder, apm_modules, okf-bundle, the lock, the ref, .okf and docs. Each asserts exit 1, the piece named in the fail line, and the line ending in the fix.
- r3 and r3b: tools are taken off a PATH that holds only fakes. Tests cover the harness that is not installed and the user-scope pass, break and seen-from-project cases.
- r4: tests check the exact key set, ids against ALL_IDS, and that JSON and text agree on exit code and fix.
- r5: a snapshot of bytes and mtime for the repository and HOME, socket.connect patched to fail, exactly one external call checked, and an AST check that doctor.py does not print, exit or write.
- r6 and r6b: help, the reference and the how-to are checked. `plugin status` gives a usage error. The old-plugin test covers both settings files and both plugin names, and checks that claude is never called. Trust is checked when settings are missing or name another folder.
- The builder's choices, judged: the extra ids (kmctl.harness, antigravity.hook, antigravity.okf-mcp, antigravity.okf-mcp-url) fit the plan and are documented. harness and fix are null where they do not apply. The new install --json shape is documented in commands.md. Reading settings.local.json is right, because local-scope plugins live there. Leaving out init and antigravity checks for --scope user is reasonable and documented. Putting fake claude and agy first on PATH in r7 is fine, because doctor only looks them up.
- Decision log: ADRs 0001, 0013 and 0015 still mention `kmctl plugin status`. They are records of past decisions, and ADR 0014's Consequences already says status folds into doctor, so I do not count this as a contradiction. The manifesto, architecture overview and log are current.

## Findings

- f1 (bug, blocking): doctor.py:419-431 uses `_install_fix("claude", scope)` for every old plugin. That fix works for kmctl@kmctl, which install uninstalls. It does not work for okf@scaccogatto, which `claude plugin prune` removes only when it was installed as kmctl's dependency and only after kmctl@kmctl is uninstalled. For okf@scaccogatto, name the claude command instead, using the scope of the file it was found in: `claude plugin uninstall okf@scaccogatto --scope project`, `--scope local` for settings.local.json, or `--scope user`. Add a test case that asserts this fix.
- f2 (design, not blocking): replace httpx with a urllib.request HEAD request, then drop httpx from dependencies and respx from dev dependencies, or give a reason to keep them.

## Notes

The ADR correction sections were reverted because existing tests pin those records' sections. I agree with leaving the ADRs as historical records.
