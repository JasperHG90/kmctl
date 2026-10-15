---
type: verdict
title: 'Verdict: scaffold-init reviewer round 2'
description: 'reviewer verdict for round 2 of scaffold-init: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T08:38:59+00:00'
slug: scaffold-init
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

Both findings sent back are fixed, and rows r1 to r6 still hold. The f2 fix adds a new small defect: the index warning is a guess presented as a fact (f3). There is also a stale help string and docstring (f4). f3 can wait without another review: the false warning only appears on stderr, init still writes the right files and never edits a kept one, and the fix is a one-line text check plus a test. f4 is a help string and a docstring. Neither needs a second look, so the label is fix.

## Checked

- `loopctl gate stamp` from the worktree: lint, format and tests pass, and rows r1 to r6 pass. Stamp green 9796cc6d06fcd4f17eb6f0a2db85c0f18d80d7f66e833148897cced302ee4742.
- Read src/kmctl/scaffold.py, src/kmctl/__init__.py and tests/test_init.py in full.
- f1: ran `kmctl init --path <missing>`. It exits 2 with click's "Directory ... does not exist" and creates nothing. test_init_refuses_missing_path asserts a nonzero exit and that nothing was created. test_init_refuses_file_path asserts a nonzero exit and no traceback.
- f2: warnings go to stderr in human mode and into the JSON object with --json. The tests check that the kept index is unchanged, that both warnings reach stderr, and that the JSON has two warnings. r6 still parses stdout as one JSON object, because warnings in --json mode are written only into that object.
- Probe for f3: a kept .okf/index.md that already contains `- [Manifesto](manifesto.md): x`, with the manifesto missing. init still prints "the kept .okf/index.md does not link the new manifesto".

## Findings

- f1: resolved. `exists=True, file_okay=False` on --path (src/kmctl/__init__.py:54), and two tests cover it.
- f2: resolved. ScaffoldResult.warnings, printed to stderr, and included in --json (src/kmctl/scaffold.py:85-95, src/kmctl/__init__.py:73).
- f3: the check looks only at which files were created or kept, and never reads index.md. A repo whose manifesto was deleted but whose index still links it gets a false warning telling the user to add a line that is already there. The ScaffoldResult docstring says a warning names a kept file "that does not point at" the new file, which the code does not check. Fix: only warn when the kept index text has no `manifesto.md`, and add a test for that case. The log warning has the same shape, but a missing log line is harder to detect, so rewording it is enough.
- f4: the `--json` help says "Print one JSON object with created and skipped paths", and scaffold()'s Returns section names only created and kept files. Both should mention warnings, since the help text is what an agent reads to learn the JSON shape.

## Notes

- None beyond the findings.
