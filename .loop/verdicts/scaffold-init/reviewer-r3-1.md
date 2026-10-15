---
type: verdict
title: 'Verdict: scaffold-init reviewer round 3'
description: 'reviewer verdict for round 3 of scaffold-init: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T08:40:33+00:00'
slug: scaffold-init
pass: reviewer
round: 3
body_schema: verdict/1
---

## Summary

Both findings sent back are fixed and rows r1 to r6 still hold. The f3 fix now reads the kept index and log, which makes one new edge reachable: a kept file that is not UTF-8 crashes init (f5). It is hardening and does not block, because OKF files are UTF-8 markdown, the files init writes are already correct when it crashes, and a second run succeeds. The label is pass.

## Checked

- `loopctl gate stamp` from the worktree: lint, format and tests pass, rows r1 to r6 pass. Stamp green 752deb6ac4459c61035e2dfae2d5ba3c244930f1d94eb7099db279fdd859e24f.
- Read src/kmctl/scaffold.py in full, the init command in src/kmctl/__init__.py, and the warning tests in tests/test_init.py.
- f3: the index warning now needs the kept index text to lack `manifesto.md`, and the log warning needs the kept log to lack `` `manifesto` ``. test_init_no_warning_when_kept_index_already_links_manifesto sets up a kept index and log that name the manifesto, with the manifesto missing, and asserts no warning on stderr. The two existing warning tests still assert both warnings in the negative case.
- f4: the --json help now says "created, skipped and warnings lists", and the scaffold() Returns section names the warnings. The ScaffoldResult docstring now matches the code, since the code checks what the kept file says.
- Probe for f5: a kept .okf/index.md holding the byte 0xe9 makes `kmctl init` end with a UnicodeDecodeError traceback.

## Findings

- f1: resolved in round 2, unchanged: --path has exists=True, file_okay=False.
- f2: resolved in round 2, unchanged: warnings go to stderr, and into the JSON object with --json.
- f3: resolved. src/kmctl/scaffold.py:85-97 reads the kept index and log before warning, and a new test covers the case where they already name the manifesto.
- f4: resolved. The --json help (src/kmctl/__init__.py) and the scaffold() docstring both mention warnings.
- f5: open, hardening, not blocking. read_text() on a kept non-UTF-8 file raises. A plain fix (read with errors="replace", or catch UnicodeDecodeError and warn) needs no second look, and the input is unlikely because OKF files are UTF-8.

## Notes

- None.
