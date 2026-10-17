---
type: verdict
title: 'Verdict: fix-audit-drift reviewer round 1'
description: 'reviewer verdict for round 1 of fix-audit-drift: fail.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-17T19:22:46+00:00'
slug: fix-audit-drift
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The doc and bundle fixes are correct, and every one I checked against the code holds. Decisions change only through appended Correction sections. The index notes and log lines are in place, and the gates are green. One thing blocks: row r2 is asserted by no test. The commands it runs pass with or without the help-string fix, so the contract the row describes is unguarded. The change also leaves the same stale "rules for writing" claim in the README, the briefing module's docstring and the Claude hook description. Rows r3 and r4 are pending: there is no commit message yet, and the audit rerun has no output.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests, integration, r1 (`uv run kmctl check`) and r2 all pass. Stamp green, 8572d82eff39615879b5c39c2facbb6dd64ddac1b6f419757447ab34657fb75f.
- Read the full `git diff HEAD` (19 files) and all 35 findings in spikes 2 to 4.
- Decisions: `git diff HEAD -- .okf/decisions/0*.md` has no removed lines, so every change is an appended `## Correction, 2026-10-17`. ADR 0012's description is untouched and its index line got a note. Its existing 2026-10-16 correction does name apm/apm.yml.
- Code behind the claims:
  - plugin.py `patch()` and `remove_old_plugin` / `drop_old_mcp` match the diagram edges: removes the old hook and a stale okf-bundle entry; plugin uninstall, prune and marketplace remove; mcp remove at user scope; never runs APM.
  - Init's Next line at `__init__.py:134` matches the ADR 0011 quote, and scaffold.py's BLOCK has five duties, the fourth naming description, stale_after and sources.
  - kinds.py has `_DOC_FIELDS` (description, stale_after, verified, sources) and `docs-folder-index`; concepts.py's result has `updated`.
  - `kmctl briefing` output lists the skills and gives one reading rule, `unverified-is-a-lead`, which matches the new row and docstring.
  - `kmctl review due --help` prints the new summary verbatim.
  - Only the antigravity hooks.json ships a Stop hook.
  - APM's authentication page says private GitHub packages need `gh auth login` or `GITHUB_APM_PAT`, with `gh auth token` asked after the env var. That matches the new how-to text.
- Explanation page: line 18's "the only hook in kmctl's package" is in the Claude Code context, where it is true. The new Antigravity paragraph and the intro's parenthesis cover finding 29.
- r3 (judgment, partial): the author's outcome list accounts for all 35 findings, and each fix I checked appears in the named file. The commit message does not exist yet, so the row cannot be judged done.
- r4 (judgment): pending. The rerun's `.out` files in the scratchpad's drift-rerun folder are empty and there is no `out-*/report.json`.

## Findings

- f1 (blocking, test-mismatch): grepping tests/ for "pages in docs/", "rule for reading" and "created_section" finds nothing. `test_reference_covers_commands` only checks that each command and option name appears in the reference. Reverting the `due` docstring would leave r2's command green. To fix, add a test that asserts review due's help names docs/, and that each summary row in docs/reference/commands.md equals the first line of that command's help. The briefing row and the `--json` key list would be good to cover too.
- f2 (non-blocking, docs): README.md:10 and :195 ("the rules for writing it"), the module docstring at src/kmctl/briefing.py:1 ("and the rules") and the Claude hook's `description` in apm/claude/.apm/hooks/hooks.json ("the rules") repeat the claim this ticket fixed for findings 7 and 31. These are outside the 35, so they are a short follow-up stub or a one-line fix each here.

## Notes

The how-to's "which APM asks after its environment variables" reads a little oddly ("tries after" would be plainer), but it is accurate.
