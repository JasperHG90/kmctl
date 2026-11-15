---
type: verdict
title: 'Verdict: ci-per-package reviewer round 1'
description: 'reviewer verdict for round 1 of ci-per-package: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-14T21:02:15+00:00'
slug: ci-per-package
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. ci.yml is named CI and runs prek, then knowledge, then kmctl, kmaudit, repo and starter side by side. A `tests` job needs the three test jobs, runs with `if: always()` and fails unless all three succeeded. prek, knowledge and tests have no `name:`, so main's required checks keep reporting. The tests pin each eval row, and a new partition test checks that the per-job collections split the gate's root collection exactly.

## Checked

- Read the full diff of .github/workflows/ci.yml, tests/test_ci.py and tests/scripts/test_workflows.py. Checked the workflow syntax by reading, since actionlint is not installed: `needs:` as a list, `if: always()`, `${{ needs.X.result }}` in env, and a run script whose last command is the `&&` chain, so under the runner's default `bash -e` it exits non-zero unless all three results are `success`.
- r1: the command selects four tests. They pin the name CI, the exact job order, `needs: knowledge` for each test job and starter, the exact pytest `with:` block for each job (directory plus `markers: not integration`), just installed before pytest in the kmctl job, and the starter job's exact run line. The command passes.
- r2: the aggregate tests pin needs, `always()` and no `name:` on the three required jobs. They also run the job's real run script under `bash -e`, once with every result success (exit 0) and then with failure, skipped or cancelled for each job (non-zero). That is nine cases, and an env check ties the script to `needs.*.result`. I tried two broken scripts by hand (`echo x`, and an `||` chain). Both exit 0, so the test would catch them. The command passes.
- r3: the partition test reads the gate command from .loop/config.toml and the `test` recipe from justfile, and asserts both are `uv run pytest`. It reads each job's directory from ci.yml, collects each one, and asserts that no job is empty, that the counts sum to the gate's count, that no id appears twice, that the union equals the gate's ids, and that both packages appear. The command passes. All three row commands together gave 15 passed.
- Checked that no tests under tests/ or packages/kmaudit/tests call just, so only the kmctl job needs it.
- Consistency: the ci.yml comments and the test docstrings match the new layout. docs/how-to cites ci.yml only by file name and its knowledge job. ADR 0044 says only that the starter job's path moved, which is still true.
- Gates: running `loopctl gate stamp` myself was denied by the session's permission classifier, so I could not re-stamp. The briefing reports the stamp green. I ran the three eval-row commands directly instead.

## Findings

None.

## Notes

The starter job is not under the required `tests` check, so a broken bootstrap does not block a merge. That matches the plan, which has `tests` need only kmctl, kmaudit and repo.
