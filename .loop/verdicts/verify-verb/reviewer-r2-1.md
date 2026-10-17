---
type: verdict
title: 'Verdict: verify-verb reviewer round 2'
description: 'reviewer verdict for round 2 of verify-verb: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T21:47:17+00:00'
slug: verify-verb
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

The CRLF fix (f1) and the docs fix (f3) hold. The traversal fix (f2) closes '..' but not the handoff refusal: `./handoffs/h` and `.//handoffs/h` resolve to the handoff and write a verified entry to it. The same fix added a crash (f5): an absolute id such as `/etc/passwd` raises ValueError while building the refusal message, and the CLI prints a traceback.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests, integration and eval rows r1 to r8 and r10 all pass. Stamp green: 54a2cda2cc0e97300ce4a3648d524c64ed12208f446f0ca83d72768b79f9989f.
- Read src/kmctl/verify.py in full, the commands.md diff, and the new refusal cases and test_verify_keeps_crlf_line_endings in tests/test_verify.py.
- Probed verify() on a temporary repo with ids `./handoffs/h`, `.//handoffs/h` (both WROTE to .okf/handoffs/h.md), `handoffs/./h` and `handoffs/h` (refused), `/etc/passwd` and `docs//etc/passwd` (ValueError). Ran `kmctl verify /etc/passwd --by human:j` through the CLI: Rich traceback ending `ValueError: '/etc/passwd.md' is not in the subpath of '.'`, exit 1.

## Findings

- f1 resolved: verify.py reads bytes, picks the file's newline, normalises, and writes it back with that newline (src/kmctl/verify.py:171 and the write_bytes call). The CRLF test asserts no bare LF, the unchanged body and the CRLF header. Mixed-ending files become all CRLF; rare, not a finding.
- f2 open: the handoff check at verify.py:156 is `cid.startswith("handoffs/")` on the raw id, but `_target` builds the path from `Path(name)`, which drops `.` segments. So `./handoffs/h` passes both checks and the handoff gets a verified entry and a log line naming `./handoffs/h`. Fix: decide "is a handoff" from the resolved path (relative to .okf/ its first part is `handoffs`), or refuse any id whose parts differ from its string split on '/'; add `./handoffs/...` to the refuses cases.
- f3 resolved: commands.md now gives the output line with the stale_after and Next lines, and the exit-code list names every refusal, including '..' and the unextendable verified field.
- f4 open, not blocking: deferred to verify-verb-reviewer-f4; not part of this round.
- f5 open: in `_target`, when the name is absolute, `base / name` is the absolute path itself, so `.relative_to(root)` raises ValueError before the ConceptError is built. The absolute case the fix meant to refuse crashes instead. Fix: build the message from the id without relative_to (or check `..`/absolute before computing rel), and add an absolute id to the refuses cases, which assert one stderr line and exit 1.
