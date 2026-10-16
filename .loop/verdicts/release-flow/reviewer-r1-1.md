---
type: verdict
title: 'Verdict: release-flow reviewer round 1'
description: 'reviewer verdict for round 1 of release-flow: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-16T10:21:56+00:00'
slug: release-flow
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change is a close port of loop-harness's release flow, minus the floor and ST-11 parts, and it should run on GitHub. I simulated the first 0.2.0 run's shell steps locally and every one worked. Nothing blocks. Two small fixes: one test assertion got weaker, and one sentence in the ADR is slightly wrong.

## Checked

- Gates: `loopctl gate stamp` from the worktree reported lint, format, tests and integration all pass, eval rows r1 to r7 all pass, and "stamp green: 59ad6b558cf5a316e354a4307cedef7a5de4fb88318c6e346ac3756df8828cc8". I also ran `uv run pytest -q` (445 passed, 11 deselected), `uv run ruff check` and `uv run ruff format --check` myself. All are clean, and no test takes over 1s by `--durations`, so no `slow` marker was needed.
- CI conditions: I ran the full suite with `GIT_CONFIG_GLOBAL=/dev/null` and a fresh HOME, with only `uv` and `/usr/bin:/bin` on PATH (no claude, no just). 445 passed. The release.yml test job will not trip on a missing git identity or tool on ubuntu-latest.
- First-release simulation, in a scratch copy of the tree:
  - `next_release_version.py PATCH --version 0.2.0` printed 0.2.0. Without `--version` it refused.
  - `release.py set 0.2.0` wrote the manifest, README.md, the tutorial and the how-to, and changed no other file. That matches the bump job's `git add` line, so its `git diff --exit-code` check passes.
  - `uv build` gave kmctl-0.2.0 wheel and sdist. `uvx twine check`, `check_wheel.py` and `smoke_wheel.py --version 0.2.0` all passed, and so did the SHA256SUMS step.
  - The release-tag compare path (`git worktree add` of the previous commit, `release.py --repo ... current`, then `compare`) gave 0.1.0 to 0.2.0, verdict raised. `is-prerelease 0.2.0` exited 1.
  - The `PREVIOUS` pipeline gives an empty string with no prior tag (it falls through `|| true` under pipefail), so `--notes-start-tag` is left out.
- Workflows against the reference: the pinned SHAs match loop-harness's exactly. release-tag.yml differs from the reference only in the dropped floor/ST-11 step, the build without SETUPTOOLS_SCM_PRETEND_VERSION, twine check moved into the build step, and the tag message. Permissions: read-only at the top level, `contents: write` plus `pull-requests: write` on bump, and `contents: write` on tag. A merge by a human starts release-tag, and this ticket's own landing does not touch plugin.json, so it starts no release.
- Eval rows: I read each test against its fails_when.
  - r1 checks pyproject's dynamic version, the regex source path and a real `uv build` at both 0.1.0 and a changed 9.8.7.
  - r2 covers current, set (manifest plus all 5 refs, moving off an older tag), refusal with nothing written, the four compare verdicts, is-prerelease, and no commit or tag.
  - r3 uses real tmp_path repos for each increment and for the no-tag refusal.
  - r4 uses offline fake wheels for each failure mode.
  - r5 checks trigger and inputs, step order, that the staged set includes the manifest and all docs, no PyPI, 40-char SHAs, and writer-only permissions.
  - r6 checks the ADR's schema, the names it must contain, the overview, the upgrade step and `kmctl check`.
  - None of these tests asserts a constant or mocks away the thing under test.
- Docs: the how-to's upgrade step uses commands that exist (`kmctl plugin update` and `status` are real verbs). Its `uv tool install --force ...@vX.Y.Z` placeholder does not match `_INSTALL`, so `set` still finds exactly 5 lines. The "ref" prose in step 3 holds both before and after the first version PR.

## Findings

- f1 (test-strength, non-blocking): `>= 11` lets the new ADR vanish unnoticed. `== 12` keeps the check exact.
- f2 (docs, non-blocking): the three `uv tool install git+...` lines have no `@ref`, so they follow the default branch. They do not name `main`. Reword the sentence to say the install lines follow `main` (the `uses:` lines pin `@main`).

## Notes

- `sort -V` puts `v0.3.0` before `v0.3.0rc1`, so the notes for a final release start from the previous final release, not its rc. The reference behaves the same way, and this is arguably what you want.
- My CI-like pytest run recreated the worktree's ignored `.venv` with a downloaded CPython 3.12. Tracked files were not touched.
