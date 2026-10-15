---
type: verdict
title: 'Verdict: new-concept-freshness reviewer round 1'
description: 'reviewer verdict for round 1 of new-concept-freshness: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-15T17:54:27+00:00'
slug: new-concept-freshness
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. `--stale-after` and `--source` write the
right fields in the shape the strict validator accepts. Every refusal happens
before anything is written. `review_due._resolve` behaves exactly as before.
There are two non-blocking findings: a crash on an absurdly long duration
(plus non-ASCII digits being accepted), and the commands for eval rows r4 and
r5 not running the tests they name.

## Checked

- `loopctl gate stamp` from the worktree: lint, format and tests pass; rows r1 to r6 pass; "stamp green: ece49c8e2de27fdca9301262e175b53502eaab1f9cf54cd6dfad1923e07f878f".
- Read the whole diff of src, tests and docs against main.
- Date edges, probed by calling `stale_after_time` directly:
  - `1m` from Jan 31 gives Feb 28, or Feb 29 in 2028. `11m` from Dec 31 gives Nov 30.
  - `12m` and `1y` from 2028-02-29 give 2029-02-28; `48m` and `4y` give 2032-02-29.
  - `2027-02-29` is refused; `2028-02-29` is accepted.
  - An offset timestamp is converted to UTC, and one without an offset is read as UTC. A `now` with an offset still gives UTC output.
  - `9999-12-31T23:59:59-01:00` is refused (no UTC value). `99999999d`, `8000y` and `99999999999999999999y` are refused as too far.
  - `30D`, `' 30d'`, `20270115` and `2027-W03` are refused, and the message names the value.
  - A bare date counts as its midnight UTC, so today's date is refused; tomorrow's date is accepted.
  - Only the 5000-digit count crashes (f1).
- Order of checks: `--key`, `--source` on a handoff, and `--stale-after` are all checked before the key lookup. `_check_sources` runs before the section is created, the folder is made, or the file and log are written. The refusal tests compare every .okf/*.md file, including log.md, before and after.
- review_due: I copied the old `_resolve` into a script and compared it with the new one on 78 cases against this repo's tracked files. The cases covered `/`, `..`, `.`, empty, a trailing slash, escaping the root, concept ids, `.md` added and folders. Old and new agree on every case. `kmctl review due --path /home/vscode/kmctl --json` gives byte-identical output with main's code and the worktree's code (13 due, all for "unverified").
- Sources shape: `- resource: "PATH"` passes `okf_validate --strict` with no warning in test_new_freshness_valid, and the fields are a subset of ALLOWED_FIELDS. JSON-quoted strings are valid YAML double-quoted scalars.
- Eval rows: r1, r2 and r3 each run tests that assert their fails_when, and r3 includes the git commit test that checks the "source changed" reason. For r4 and r5, see f2.
- Help and docs: the `kmctl new practice --help` text is plain and complete. The reference, tutorial, overview table and the ADR 0011 correction match the code. ADR 0008's "14 days out" still holds as the default.

## Findings

- f1: The fix is to use `[0-9]+` (or re.ASCII) and to cap the count's length or move `int()` inside the try, so a long count is refused as too far in the future. This is a plain fix, so it is non-blocking.
- f2: The fix belongs to the eval rows, not the code. The r4 command could be `uv run pytest "tests/test_new_concept.py::test_new_freshness_valid" tests/test_okf_fields.py -q`. The r5 command needs node ids or a single `-k "block_names_freshness or freshness_documented"`. This is non-blocking because r6 covers both tests.

## Notes

`_check_sources` accepts any path on disk, including gitignored files and empty folders. `review due` will then only report "source not resolved" for those. The plan accepts this for untracked files, so I did not raise it as a finding.
