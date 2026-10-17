---
type: verdict
title: 'Verdict: verify-verb reviewer round 3'
description: 'reviewer verdict for round 3 of verify-verb: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T21:56:51+00:00'
slug: verify-verb
pass: reviewer
round: 3
body_schema: verdict/1
---

## Summary

f2 and f5 are fixed. `_target` now refuses any id not spelled the one way kmctl review due prints it, and the handoff check runs on that canonical id, so `./handoffs/h` and `.//handoffs/h` no longer reach a handoff. Absolute ids get a one-line refusal instead of a traceback. Nothing the fix touched broke. One rare new edge remains (f6, hardening, not blocking): a docs/ folder that is a symlink out of the repository still crashes at the later `relative_to(root.resolve())`. With f4 deferred and f6 hardening, the label is pass.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests, integration and eval rows r1, r2, r3, r4, r4b, r5, r6, r7, r8 and r10 all pass. `stamp green: b7ba61bc430cd196ab502e4839261bb9c5c41b545c75c80dead9d8ba70b05d2a`.
- Read src/kmctl/verify.py in full (`_target` and its use in `verify`), and the refuses parametrisation in tests/test_verify.py. The new cases dot-slash-handoff, dot-double-slash-handoff, absolute and docs-absolute assert exit 1, empty stdout, one `kmctl verify: refused:` stderr line naming the fix, and no file changed. That covers r4's fails_when for these ids.
- Re-ran the round 2 probe: `./handoffs/h`, `handoffs/./h`, `.//handoffs/h` are refused as not canonical (naming `handoffs/h`). `/etc/passwd` and `docs//etc/passwd` are refused with a message and no traceback. `handoffs/h` is refused as a handoff.
- Ran a second probe: `decisions/a.md` is accepted and recorded as `decisions/a`. A symlink `decisions/b` pointing at `decisions/a` is refused and the message names `decisions/a`. `''`, `docs` and `docs/` are refused. A docs/ that is a symlink to a folder outside the repo crashes (f6).

## Findings

- f1 resolved in round 2. It still holds: the CRLF test passes under the stamp.
- f2 resolved: `_target` compares the id with its canonical form, built from the resolved path relative to the base (verify.py:58), and returns it. `verify` runs the handoff check on the returned id (verify.py:161). Any `.`, `//` or `..` spelling is refused before that check, so it cannot be bypassed.
- f3 resolved in round 2.
- f4 open, not blocking: deferred to verify-verb-reviewer-f4.
- f5 resolved: the is_relative_to and is_file check now comes before any `relative_to`, and the message is built from strings (verify.py:52). An absolute id gets a ConceptError.
- f6 open, hardening, not blocking: `_target` resolves the base, so when docs/ is a symlink to `../shared`, `path.relative_to(root.resolve())` at verify.py:166 raises `ValueError: ... is not in the subpath of ...`. kmctl review due's `_docs_pages` lists those pages, so a person following its output would hit a traceback. The layout is rare. The plain fix is to build `rel` from the canonical id (`docs/<name>.md` or `.okf/<name>.md`) rather than from the resolved path.

## Notes

The staged diff against main also deletes many .loop/ files (opencode-harness, verify-verb-reviewer-f4 and verify-verb event logs and verdicts). That is because main has moved on since the worktree branched. It is not part of this change's code, but whoever lands it should make sure the commit does not delete main's loop state.
