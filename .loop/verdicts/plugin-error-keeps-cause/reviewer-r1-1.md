---
type: verdict
title: 'Verdict: plugin-error-keeps-cause reviewer round 1'
description: 'reviewer verdict for round 1 of plugin-error-keeps-cause: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-16T06:05:03+00:00'
slug: plugin-error-keeps-cause
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. `_cause` keeps git's `fatal:` and `error:` lines in order, adds claude's last line when it is not already the last kept line, joins them with "; " and caps the result at 400 characters. `_require` still names the command and ends with the fix line, and `_MISMATCH` still reads claude's full output. Each eval row's test fails when its behavior breaks; I checked this by changing the code in a scratch copy.

## Checked

- Gates: `loopctl gate stamp` from the worktree printed "stamp green: 3fe3de39db7fb93fdd4ad4c68f421943bebc28d4f0290e9521c083b094b16e4b". lint, format, tests, integration and rows r1 to r4 all passed.
- Code read: `_cause` and `_require` in src/kmctl/plugin.py and every caller (`_json`, `install`). The mismatch check at plugin.py:280 runs before `_require` and still reads `added.stdout + added.stderr`. The `kept[-1:]` test stops a last line that is itself `fatal:` from showing up twice. The cap gives at most 399 characters plus "…", which is 400. Empty or blank output still gives "no output", as before.
- r1 and r2, mutation: in a scratch copy I put back the old last-line-only behavior. test_cause_named_on_ssh_fallback, test_cause_keeps_error_lines, test_last_line_and_cap_long_stderr and test_ssh_fallback_retried failed. The single-line and no-output tests passed, as they should, since that behavior did not change. With the cap removed and nothing else changed, only test_last_line_and_cap_long_stderr failed. The single-line test compares the whole message against today's exact text, so it covers r2's "differs from today's" and the command and fix wording.
- r3: test_ssh_fallback_retried builds a real kmctl message from the SSH-fallback stub. It runs it through the repo's own conftest retry hook in an integration-marked pytester test that fails twice and then passes, and it asserts passed=1 and three runs. With the old message the hook did not retry and the test failed, so the row checks the real path.
- r4: the stamp's r4 run (`-m "not integration or integration"`) passed.
- Consistency: the conftest comment above NETWORK_ERRORS now matches what kmctl passes on. The `_cause` docstring matches the code. No page in docs/, README.md or .okf/ describes the error text.

## Findings

None.

## Notes

- `_cause` strips each line, so a last line with leading indentation loses that indentation where the old code kept it. This does not matter in practice.
- The diff against main also shows .loop/ files. That is only because main moved after the branch was cut. The worktree's own changes are plugin.py, conftest.py and tests/test_plugin_error.py.
