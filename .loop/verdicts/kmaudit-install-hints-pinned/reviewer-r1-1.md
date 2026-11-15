---
type: verdict
title: 'Verdict: kmaudit-install-hints-pinned reviewer round 1'
description: 'reviewer verdict for round 1 of kmaudit-install-hints-pinned: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-15T08:13:08+00:00'
slug: kmaudit-install-hints-pinned
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. kmaudit/install.py builds the hint from the running version: a release or a/b/rc pre-release gets its kmaudit-vX.Y.Z tag, and a dev, local or unreadable version gets no ref. steps.py and judge.py take INSTALL from it, and check_verbs.py and ui.py import those. The tracing refusal now asks for kmaudit[tracing]. set --package kmaudit pins the commands.md tracing line and refuses before writing anything, and the bump stages the file. One non-blocking docs finding: two descriptions of the kmaudit bump still name only the README.

## Checked

- I re-ran `loopctl gate stamp` in the worktree. lint, format, tests and integration all pass, and so do eval rows r1 and r2. The stamp is green: 2bd097ffdc6a89e2c4668d63b6f473eb5c8c565137b79f1956c0bfa86f819d59.
- r1: test_install_hint_names_the_release_it_ships_in compares exact strings for 0.2.0, 0.2.0rc1, 0.2.0.dev1, 0.2.0+g1a2b and the tracing extra. test_the_tracing_refusal_install_hint_asks_for_the_extra goes through the real run_judge, with langsmith hidden by patching find_spec, and asserts `kmaudit[tracing] @`. test_only_the_install_module_writes_the_install_source fails if any module still holds a hand-written git URL. Each part of fails_when is covered.
- r2: the kmaudit set test asserts the pinned tracing line and the exact changed-file set. The refusal test removes the tracing line and asserts exit 1, commands.md named in stderr, and no changes. The workflow tests check the bump's git add line and run the bump end to end, asserting the committed files.
- Tag existence: next_release_version.py accepts only canonical X.Y.Z or X.Y.Z{a,b,rc}N. hatch reads the version from apm.yml, and release.yml checks that the wheel carries $VERSION. So any version install.py's regex treats as a release has a kmaudit-vX.Y.Z tag. Post releases cannot be released, so the regex leaving them out is correct.
- kmaudit-skills-mcp: that plan has set --package kmaudit pin the server's ref in apm.yml. It fits the same pattern of pinning each file and refusing when a line is missing. This change does nothing to block it.
- Ordering in set_kmaudit_version: all three reads and checks run before any write, so a refusal writes nothing.

## Findings

- f1 (docs, non-blocking): release.yml:327's WHAT text says the kmaudit bump "pins the README's install line to $TAG", and that text goes into the version PR body. release.py:390's set help says the same. Both should also name the commands reference's tracing line now. The fix is a plain wording change.
