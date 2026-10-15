---
type: verdict
title: 'Verdict: plugin-error-keeps-cause plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of plugin-error-keeps-cause: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-15T19:25:07+00:00'
slug: plugin-error-keeps-cause
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

No open risk could break this plan. The SSH-fallback stderr shape it rests on is real and reproduces on claude 2.1.300. Under the plan's rule, the HTTPS `fatal: ... Could not resolve host` line lands in the message, so the network-tests-retry hook (which matches "Could not resolve host") fires on that path. Keeping `fatal:`/`error:` lines leaks no credentials, because git already strips them from the URL. No test or doc asserts today's one-line message.

## Checked

- Reproduced in scratch with an isolated HOME, CLAUDE_CONFIG_DIR and XDG_DATA_HOME, and GIT_CONFIG_GLOBAL mapping `https://github.com/` to `https://unresolvable.invalid/` and `git@github.com:` to `git@unresolvable.invalid:`. `claude plugin marketplace add scaccogatto/okf-skills --scope project` exits 1. Its stderr reads: "Fetching the marketplace from GitHub failed on both attempts. HTTPS (...)", then "Original error: Cloning into ...", then `fatal: unable to access 'https://unresolvable.invalid/...': Could not resolve host: unresolvable.invalid`, then an SSH block with `ssh: Could not resolve hostname ...`, `fatal: Could not read from remote repository.`, and "Please make sure you have the correct access rights / and the repository exists." The plan's rule keeps both fatal lines and the last line, in that order. Spike network-tests-retry/1 mapped both prefixes to HTTPS and got no SSH block, which is why it missed this path.
- Leaks: I set an insteadOf target of `https://x-access-token:SECRETTOKEN123@unresolvable.invalid/`. Git 2.51 printed the URL with the credentials stripped, and `git ls-remote` with user:pass in the URL did the same. The HTTPS-only path already surfaces this same line today, so the plan adds no new kind of exposure. The "Cloning into" line, which carries local paths, starts with neither prefix and is dropped.
- Exact-message assertions: I grepped tests, docs, .okf and src in main and in the network-tests-retry worktree for "failed:", "run it by hand", "access rights" and "last line". Only plugin.py builds the message. test_network_retry.py's NETWORK constant is a hand-written report string fed to a generated test, not kmctl's output. test_okf_source_unknown_kind asserts only that a path is in the message.
- r3's fit: test_network_retry.py's `run_generated` fixture already runs a generated integration-marked test under the real conftest through pytester, with `time.sleep` patched. An unmarked outer test in tests/test_plugin_error.py can do the same with a stub claude on PATH that fails twice with the SSH-fallback stderr. That keeps the outer test in the default run, so `uv run pytest tests/test_plugin_error.py -k ssh_fallback_retried` selects it. The new file does not affect test_network_retry's checks, which read only test_plugin_install.py.
- `_MISMATCH` reads `added.stdout + added.stderr` before `_require` runs, so it does not depend on the message (plugin.py:255-267).

## Findings

None.

## Notes

- The kept "SSH line" is the last line, "and the repository exists.", plus `fatal: Could not read from remote repository.`. The plan's wording fits, but r1's stub should use the real line order shown above.
- If the cap truncates, it should cut from the end so the leading HTTPS fatal line (the cause) survives.
- The comment above NETWORK_ERRORS in network-tests-retry's conftest ("as kmctl passes on claude's last stderr line") goes stale once this lands. That is worth a one-line touch in the build.
