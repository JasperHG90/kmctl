---
type: verdict
title: 'Verdict: repo-rename reviewer round 1'
description: 'reviewer verdict for round 1 of repo-rename: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T19:02:28+00:00'
slug: repo-rename
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The rename is complete and correct. Everything kmctl points users at names JasperHG90/kmctl. Installs from the old name are still recognised in every case the plan names, and each refusal names the right `apm uninstall`. The release script no longer moves the v0.3.0 example. All gates and the four eval rows are green on a fresh stamp. Two non-blocking findings remain: one test should be stronger, and one doc sentence is incomplete.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests and integration pass; rows r1 to r4 pass; stamp green 4f03fd0a54a78e03de43e164c1047ae66d95f421dfd6459d54ba18f701471b1f.
- Read the whole diff and the changed functions in src/kmctl/plugin.py: `_repo_of`, `_old_layout`, `_names_old_package`, `_old_entry`, `patch` and `uninstall_name`.
- The refusal for each case:
  - String entry from either name: uninstall names the entry as written, minus `#ref`.
  - v0.3.0 lock with a dict entry: `uninstall_name` builds it from the entry's own URL, so `github.com/<name>/apm` with its case kept.
  - v0.3.0 lock with no entry: the canonically cased `<repo>/apm` of the repository the lock names.
  - A dict entry from the old URL with the new layout is not refused, and `kmctl_package` still finds it by name and path, as the plan intends.
  - `_repo_of` checks REPO first; the old name does not contain the new one, so the order is safe.
- Eval tests: r1 runs git ls-files and allows only plugin.py, tests and the two docs pages, with a negative lookahead for `/apm`. r3 is parametrised over both names for the string entry, the v0.3.0 lock with an entry, and the v0.3.0 lock alone, and asserts exit 1 plus the exact uninstall text. r4 runs set_version on a copy and checks the example survives. The `-k` filters select the intended tests.
- Grepped tracked files outside .okf/decisions and .loop for the old name. The only hits are plugin.py, tests, the how-to's Older installs example and commands.md's refusal description. The apm/antigravity hooks name no repository, which matches the re-signed r2.
- /home/vscode/kmctl-starter: commit 8ec63a6 renames the repository there, and its tracked files no longer name the old one.
- release.py: the `pin_apm_doc` removal is clean, and the module and `set_version` docstrings match the new behaviour.

## Findings

- f1 (test-strength, non-blocking, row r2): `assert install in plugin.HOOK_COMMAND` is satisfied by either of the two install lines in the hook. Add an assertion that HOOK_COMMAND does not contain OLD_REPO, or count two occurrences. The code itself is correct.
- f2 (docs, non-blocking): after this change, `_names_old_package` treats a string entry from either repository name as the old form. docs/reference/commands.md step 1 still names only `JasperHG90/Knowledge-management/apm#…`. Mention `JasperHG90/kmctl/apm#…` too, or say "the string form of either name".

## Notes

`_repo_of` matches by substring, so `jasperhg90/kmctl-starter` would count as kmctl in a dict entry's git URL or in a lock repo_url. That only matters when the lock has `virtual_path: plugin` for that repository, which kmctl-starter never has. The old check had the same substring behaviour. This is not a finding.
