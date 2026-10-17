---
type: verdict
title: 'Verdict: apm-hands-back reviewer round 2'
description: 'reviewer verdict for round 2 of apm-hands-back: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T15:13:09+00:00'
slug: apm-hands-back
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

All three findings sent back are fixed. f1 now holds against a real APM install: doctor folds the sub-packages' lock entries into kmctl's, and a deleted or edited rule fails both files checks. drop_old_hook now keeps a user's hook that shares a group with kmctl's old one. One small help-text slip is left (f6), which needs no second look.

## Checked

- Ran `loopctl gate stamp` from the worktree with a fresh empty scratch HOME. lint, format, tests and integration passed, and eval rows r1 to r8 passed. Result: "stamp green: ec4abe6c7293afec94fbd9884dec225fbd62d6f73a887dcae45c21ef4d5454e7". The state commit was skipped because git had no identity in the scratch HOME.
- f1, reproduced on a real consumer: ran test_doctor_after_a_real_install_exits_zero with --basetemp in scratch. The lock lists the rules under kmctl-claude (apm/claude) and kmctl-antigravity (apm/antigravity), both with repo_url o/kmctl. Doctor printed `ok claude.files: 33` and `ok antigravity.files: 32` (29 and 28 in round 1). After I deleted .claude/rules/docs-layout.md and .agents/rules/okf-bundle.md, both checks failed and named the file. After I edited .claude/rules/okf-bundle.md, claude.files reported "differs from apm.lock.yaml". Read kmctl_files and the new fake lock in tests/test_doctor.py, which now splits the rules into per-harness sub-entries like real APM.
- f2: called plugin.drop_old_hook directly on a mixed group (echo mine plus kmctl's hook), on separate groups, on a file with no kmctl hook, and on a recorded group next to an unrecorded one. Each time it kept the user's hook and other keys, dropped only the unrecorded kmctl hook, and returned False when nothing changed. Read test_migrate_keeps_other_hooks_in_a_shared_group, which asserts the exact remaining document.
- f3/f4: the uninstall test now checks that okf-bundle is gone from .mcp.json and .agents/mcp_config.json and that kmctl briefing and the Stop wrapper are gone from .agents/hooks.json. The split_package selector now includes the shared-package and Claude-rule test.
- f5: read the install epilog, the plugin.install docstring and the overview diff. Removing the old hook and MCP now comes before apm install, matching the code. The doctor details, docs/reference/commands.md and the how-to sample now say the package ships these. The remaining "this kmctl writes" lines are about .agents/plugins/kmctl/, which kmctl still writes, so they are correct.

## Findings

- f1 resolved: plugin.kmctl_files (src/kmctl/plugin.py:647) is used by doctor's files checks, verified on a real install as above.
- f2 resolved: drop_old_hook (src/kmctl/plugin.py:838) removes only kmctl's hooks from an unrecorded group.
- f3 resolved: stronger uninstall assertions in tests/test_doctor.py.
- f4 resolved: r1's selector now covers the shared-package and Claude-rule assertions.
- f5 resolved: order and wording fixed in src/kmctl/__init__.py, .okf/architecture/overview.md, doctor.py and the how-to.
- f6 (docs, non-blocking): the doctor epilog in src/kmctl/__init__.py (around line 988) still reads "antigravity.hook (its hooks.json)" right after ".agents/plugins/kmctl/", so it points at the plugin folder's hooks.json, which kmctl no longer writes. It also says okf-mcp checks the server "as this kmctl declares it". Make it say antigravity.hook checks .agents/hooks.json for kmctl's SessionStart hook and okf's Stop check, and that okf-mcp checks the server as kmctl's package declares it, to match docs/reference/commands.md.

## Notes

Running the integration test with a scratch HOME made uv recreate the worktree's .venv. It is git-ignored and the tree is otherwise unchanged.
