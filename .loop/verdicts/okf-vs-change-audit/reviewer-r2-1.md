---
type: verdict
title: 'Verdict: okf-vs-change-audit reviewer round 2'
description: 'reviewer verdict for round 2 of okf-vs-change-audit: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-26T21:52:53+00:00'
slug: okf-vs-change-audit
pass: reviewer
round: 2
body_schema: verdict/1
---

## Summary

f2 is fixed. f1 is fixed for a symlink on the instruction path itself, but not for a symlink on one of its parent folders. A pull request that replaces the tracked folder `.github` with a tracked symlink to a folder it controls inside the repository (`.github -> evil`, with `evil/audit.md`) still swaps `--prompt-file .github/audit.md`, and the same goes for `--context`, `--skills` and `--system-prompt-file` under such a folder. The key does not leak through this path, since an untracked path that leaves the repository is now refused, but the pull request can still quietly rewrite the audit's instructions. That is the second claim f1 named (ADR 0017's Correction, "a pull request cannot quietly edit the prompt", and the how-to's "the pull request cannot quietly loosen the audit"). The verdict is fail.

## Checked

- Gates: I ran `loopctl gate stamp` from the worktree. Result: "stamp green: 84821977caf20eaa1f9a6640f18fe40329d389008a20977333efe65d2d9df111", with lint, format, tests, integration and every eval row r1 to r28 passing.
- f1, direct symlink: `tracked()` now asks `git ls-files -- <raw>` without resolving, so a tracked symlink counts as tracked and resolves under the base checkout, and `instruction_path` refuses a tracked path that resolves outside the base and an untracked path that resolves outside the repository. The new tests (tests/test_agent.py:1442 and :1485) assert the base task and base context folder are used, that the secret text never reaches the prompt, and exit 2 for an untracked symlink out of the repo. They would fail against the round 1 code.
- f1, parent-folder variant: in a scratch repository I committed `.github/audit.md` and `.okf/decisions/x.md`, made a base worktree, then committed a pull request that deletes both folders and adds `evil/audit.md`, `evil/decisions/` and the tracked symlinks `.github -> evil` and `.okf -> evil`. `git ls-files -- .github/audit.md` and `git ls-files -- .okf/decisions` both print nothing with exit 0. `agent.instruction_path(".github/audit.md", base, repo, "--prompt-file")` returned `repo/evil/audit.md` and read "EVIL PROMPT"; `--context .okf/decisions` returned `repo/evil/decisions`. Both stayed in the pull request's tree instead of the base. Pointing the parent symlink out of the repository (`ci -> /some/folder`) is refused, so this does not reach the key.
- Symlink inside a tracked context folder: the context folder resolves under the base checkout, so the pull request's symlinks inside it are never read. Skills folder symlinked directly: tracked, resolves under the base. Both fine.
- f2: both `uv run` calls in action.yml carry `--no-config`, and test_action_runs_the_agent_script_without_uv_config asserts it for the agent and publish steps and that no bare `uv run --script` is left. I also tried a `.python-version` in the working folder pointing at a tracked executable, with a fresh UV_CACHE_DIR: uv 0.13.7 ignores it for `uv run --script`, with and without `--no-config`. uv config through environment variables would need the workflow or an earlier workflow step to set them, which the pull request does not control under ADR 0057's threat model.
- The base checkout now goes to `mktemp -d "$RUNNER_TEMP/kmctl-base.XXXXXX"`, which removes the round 1 note about running two audits in one job.
- f4: the `instructed` fixture names each tree's skill after the tree (`{word}-skill`, tests/test_agent.py:1209), so r7 now tells base skills from head skills.

## Findings

- f1 (bug, blocking, open): the parent-folder symlink above. One fix: treat a raw path as tracked when git tracks any of its leading parts as a symlink (for example `git ls-files -s` on each parent, looking for mode 120000), or refuse an untracked path whose resolved location differs from `repo / raw` with no symlinks followed. Add a test where a tracked parent folder becomes a symlink to a folder inside the repository, for --prompt-file and --context, and assert the base's text and folder are used or the run is refused. Blocking, because another partial fix would leave the same hole.
- f2 (resolved): `uv run --no-config --script` in both steps, action.yml, with a test in packages/kmctl/tests/test_action.py:721.
- f3 (hardening, not blocking, open): not sent back this round; it moved to the stub ticket okf-vs-change-audit-reviewer-f3, so it stays open there.
- f4 (resolved): skill names differ per tree in the `instructed` fixture.

## Notes

A pull request that deletes a tracked prompt file without replacing it makes `instruction_path` treat the path as untracked, and `read_text()` then raises FileNotFoundError rather than a UsageError naming the flag. The run still fails closed, so this is a remark, not a finding.
