---
type: verdict
title: 'Verdict: plugin-patch reviewer round 1'
description: 'reviewer verdict for round 1 of plugin-patch: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T15:49:46+00:00'
slug: plugin-patch
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The change does what the plan asks. `kmctl plugin patch` reads the lock, refuses old entry forms before it refuses a missing package, patches only the harnesses the lock lists, never runs uvx, and the old verbs are gone. A fresh stamp is green on every gate and every row. I found no defect that needs a second look, but there are four plain fixes. One stale refusal message (f1) names the deleted `kmctl plugin install`. Tests for functions that are still live were deleted along with the verbs (f2). There is leftover dead code and stale comments (f3), and a rule heading and two test docstrings now say false things (f4).

## Checked

- Gates: I ran `loopctl gate stamp` in the worktree myself, with a fresh, empty scratch HOME. Result: `pass` for lint, format, tests and integration, and for eval rows r1 to r7. `stamp green: e73c649e1f35ca614d202f67dbe5034ad70d4f48d259f871e3e81c09a8cdedd9`. The state commit was deferred only because the scratch HOME has no git identity.
- Code read in full: plugin.py, the plugin_patch command in __init__.py, and the doctor.py, antigravity.py, briefing.py and scaffold.py diffs.
  - patch checks for an old entry form before it checks the lock, as the plan orders.
  - Harnesses come from the lock's deployed_files.
  - The claude cleanup runs only when the lock lists claude, and antigravity only at project scope.
  - `--undo` deletes only `.agents/plugins/kmctl/`.
  - The Next line, `--json`, and the exit code 1 on refusal match the plan.
  - Every doctor fix now names apm install, the apm.yml ref or kmctl plugin patch. The antigravity rpartition still splits APM_FIX correctly, because APM_FIX contains no '; '.
- Eval rows: I read every test the rows run.
  - r1: tests assert on the written folder against plugin_files, the Stop handler being gone, no uvx calls, hook and stale okf-bundle removal at both scopes with the 'apm install again' note, the old-plugin calls, byte-identical files on a second run, and the JSON keys and Next line.
  - r2: tests assert exit 1, the named apm install, the string-form and v0.3.0-layout uninstall names (with -g at user scope), and the new entry.
  - r3: tests assert that only the folder changed, and exit 0 when there is nothing to undo.
  - r4: tests assert exit 2 and 'No such command' for each old verb, that `plugin` lists only `patch`, a regex over every doctor fix across the BREAKS table, and init's Next line.
  - r5: tests assert the README's three harness sections and each step, the commands.md headings, and the ADR 0021/0019 links.
  - r6: runs real APM 0.33.0 from a served tree, then patch, init, doctor (exit 0), undo and uninstall, and checks that nothing is left.
  - All of these assert their fails_when.
- APM behaviour behind the docs: I checked `uvx --offline --from apm-cli==0.33.0 apm --help`, `update --help`, `uninstall --help` and `install --help`. `apm update` and `apm uninstall -g` exist, and `install` takes `--target` with commas. The okf-bundle re-install claim matches spike plugin-patch/1.
- Docs: I read the README install section, the commands.md patch section, both how-tos, ADR 0021, the ADR 0019/0014 corrections, the index, the log, the manifesto, the architecture overview, the tutorial and the explanations. They match the code: the refusal order, the user-scope note, `--undo` output, the anchors (#7-to-remove-kmctl, #before-you-start) and the Next line.
- I reproduced f1 with the worktree's kmctl in a scratch repo.

## Findings

- f1: `read_json`'s 'not valid JSON' message still says 'run kmctl plugin install again'. patch surfaces it as the fix in its refusal. Change it to a fix that exists, as the 'not a JSON object' branch already does ('run the command again').
- f2: Coverage for remove_old_plugin, drop_old_hook, drop_old_mcp and uninstall_name went with test_plugin.py and test_plugin_remove.py. These functions are still live, and patch's refusal relies on uninstall_name. Restore those cases against patch or the functions directly, and add a test for the invalid-JSON refusal.
- f3: Remove `_apm_run`, and fix the HARNESSES and DEFAULT_SOURCE comments that name the removed --harness and --source options.
- f4: Retitle the rule and rename its constraint to match its body. Update the two test module docstrings.

## Notes

- Possibly pre-existing, and not shown here: a later okf pin bump could leave a stale okf-bundle in `.agents/mcp_config.json` that APM skips. patch removes a stale okf-bundle only for claude, so doctor's antigravity.okf-mcp fix (apm install, then patch) would not clear it. Worth a spike when OKF_COMMIT next moves.
- `kmctl plugin patch --undo --scope user --json` reports `scope: project`. That is harmless, since undo only touches the repository, but slightly odd.
- When the old-layout lock has a git entry from a fork, `_old_entry` falls back to naming `JasperHG90/Knowledge-management/apm` for uninstall. This is an edge case that carried over from the old install code.
