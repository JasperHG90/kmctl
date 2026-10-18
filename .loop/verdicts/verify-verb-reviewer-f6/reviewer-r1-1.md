---
type: verdict
title: 'Verdict: verify-verb-reviewer-f6 reviewer round 1'
description: 'reviewer verdict for round 1 of verify-verb-reviewer-f6: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-18T22:42:27+00:00'
slug: verify-verb-reviewer-f6
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

`verify` now builds the reported path from the id `_target` returned (`docs/...md` or `.okf/...md`) instead of `path.relative_to(root.resolve())`. That call raised ValueError when docs/ or .okf/ was a symlink to a folder outside the repository. The page is written through the symlink and named by its path inside the repository, as `kmctl review due` names it. The plan's intent is met.

## Checked

- Ran `loopctl gate stamp` in the worktree: lint, format, tests, integration, r1 and r2 all pass, stamp green e3b3f7391c3ef095aa894ea502bcc736bd7b9d7d2dd8bb2aa0641cb3f8a6f375.
- r1: `test_verify_through_a_symlinked_folder_outside_the_repo`, run for both docs and .okf, moves the folder outside the repo and symlinks it back. It first checks that review due lists the page, then runs verify with `--json`. It checks that the exit code is 0, that `path` is the in-repo `folder/rel`, that the entry was written to the real file outside, and for .okf that log.md got the line. The old code raised at the relative_to call, so this test fails without the fix. It covers fails_when.
- The id is safe to build a path from: `_target` returns its canonical spelling only after checking that the resolved file is under the resolved base and is spelled as review due prints it. `rel` then always matches `_target`'s own `shown` path, and `Verified.path`'s docstring ("the repository-relative path") is now true in the symlink case too.

## Findings

None.

## Notes

verify-verb-reviewer-f4 also edits src/kmctl/verify.py, in `_with_entry` and the regexes near the top. This ticket edits only the `rel` line in `verify`. `git merge-file` merges verify.py cleanly. tests/test_verify.py conflicts, because both tickets add their test after `test_verify_keeps_every_other_line`. Keep both blocks.
