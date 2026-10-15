---
type: verdict
title: 'Verdict: scaffold-init reviewer round 1'
description: 'reviewer verdict for round 1 of scaffold-init: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T08:35:11+00:00'
slug: scaffold-init
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. `kmctl init` writes the four files, never overwrites one, creates no section folders, and its bundle passes the pinned validator in strict mode. The tests check every row's fails_when. One non-blocking finding: `--path` does not check that the target is an existing directory, so a typo creates a stray tree and a file path ends in a traceback. The fix is a plain option setting plus a test.

## Checked

- `loopctl gate stamp` from the worktree: lint, format and tests pass, and rows r1 to r6 pass. Stamp green 8b72a1c85436e57147f1d1e2243b476e28887431e5c78e2a2752316b6879f00c.
- Read the staged diff against main and every changed file in full: src/kmctl/__init__.py, src/kmctl/scaffold.py, tests/test_init.py, tests/conftest.py, pyproject.toml, tests/vendor/okf/README.md and NOTICE.
- Vendored validator: diffed okf_validate.py, LICENSE and NOTICE against the installed okf plugin cache at 0.10.1. All three are byte-identical, so the README's "copied unchanged" claim holds.
- r1: asserts each file exists and each path appears on stdout. r2: snapshots content and st_mtime_ns, compares after the second run, and asserts "created" is absent from stdout. r3: pre-seeds docs/README.md and .okf/manifesto.md and checks their content after the run. r4: runs the vendored validator with --strict and asserts exit 0. I checked the validator would catch a broken bundle: removing `type` from the generated manifesto makes it exit 1. r5: rglobs both trees for directories and asserts none. r6: parses stdout as JSON on two runs and checks the created and skipped lists. None of the tests is skipped or mocked, and each would fail if its behavior broke.
- Consistency: the root index uses a list-item relative link, which is the entry format in .loop/plans/knowledge-check.md. It writes no counts, as that plan says. The manifesto stub has type, title, description, tags and generated, as the okf-bundle rule requires. ADR 0003's test-only boundary is stated in the vendor README. Help renders at 80 columns with an example in metavar and an epilog.
- Edge probes by hand: `--path` pointing at a missing nested directory, and `--path` pointing at a file (see f1).

## Findings

- f1: `--path` does not check that the target is an existing directory. A missing path gets created and reported as success. A file path ends in a Python traceback instead of an error that names the path and what to pass. Either way the human or agent gets no useful refusal. The fix is the typer option flags plus a test, so it does not need another review.

## Notes

- If .okf/index.md already exists but manifesto.md does not, init writes a manifesto that the existing index does not link and that log.md does not mention. This follows from "never overwrite" in the plan, and `kmctl check` will report it, so it is not a finding.
- The vendored NOTICE mentions a SPEC.md path in the upstream repo. That is correct for a verbatim notice copy.
