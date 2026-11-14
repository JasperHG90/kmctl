---
type: verdict
title: 'Verdict: kmaudit-namespaces reviewer round 2'
description: 'reviewer verdict for round 2 of kmaudit-namespaces: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-14T13:56:03+00:00'
slug: kmaudit-namespaces
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

Both blocking findings are fixed, and I found nothing the fixes broke. The
repository root without .okf/ is now refused with a message that names a
folder to give. The legacy store copy now goes to a unique temp file and is
linked into place with os.link, which fails rather than overwrites when the
store already exists. f3 and f4 are fixed too. Pass.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests and integration
  pass, and rows r1 to r9 pass. "stamp green:
  14a08a0fbcfd62ea2e4642626743c2ded8c8f63133ee350ef4b64e9789bd1baf".
- f1: read resolve_target and namespaces.repository_root. In a scratch git
  repo with docs/, handbook/ and README.md and no .okf/, `kmaudit claims todo`
  exits 1 with "is the repository root, which holds no .okf/; give the folder
  ... such as docs", and creates no .kmaudit/. After that, `claims todo docs`
  gives namespace docs, and running `claims todo` with no argument from inside
  docs/ also gives docs. Outside git, a folder gets its own namespace, with
  the folder's parent as the root. The root can only equal the path inside a
  git repo, so the refusal cannot trigger by mistake outside one. Nothing
  references _git_root any more. The new test asserts exit 1, the hint, empty
  stdout, no '..sqlite' store, and that a later `todo docs` succeeds.
- f2: read store._copy and its caller in Store.__init__. A unique mkstemp
  file sits in the same folder, so os.link stays on one filesystem.
  FileExistsError means another process won, and the temp file is always
  unlinked. I ran 8 parallel `kmaudit claims list .okf` processes over a copy
  of the operator's real legacy store, 5 times. Every process exited 0 every
  time, no .partial file was left, integrity_check gave ok, the claims count
  was 1281, and the legacy file's md5 did not change. The new test starts 6
  processes and asserts they all succeed, no .partial file is left, and the
  claims are kept.
- f3: `-k maps` now also collects
  test_a_folder_holding_a_namespace_maps_to_a_refusal_naming_it.
- f4: r1's test compares the full set of section ids, with a count guard of 5.

## Findings

- f1 resolved: sections.py:142-148 refuses the root when it holds no .okf/.
  namespaces.repository_root is the one root rule.
- f2 resolved: store.py:158-184 writes to a unique temp file and publishes
  with os.link, which never overwrites.
- f3 resolved: r2b's selection now includes the refusal test.
- f4 resolved: test_namespaces.py:109 asserts every section id.

## Notes

The concurrency test calls wait() before it reads the pipes. If a process's
stdout ever grew past the pipe buffer (64 KB), the test could deadlock.
Today's output is small. communicate() would remove the risk.
