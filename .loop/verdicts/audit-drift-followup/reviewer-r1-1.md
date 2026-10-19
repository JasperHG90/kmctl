---
type: verdict
title: 'Verdict: audit-drift-followup reviewer round 1'
description: 'reviewer verdict for round 1 of audit-drift-followup: pass.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-10-19T01:35:50+00:00'
slug: audit-drift-followup
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

All eight mismatches the plan lists are still real against today's code, and each is fixed the way the eval row asks. Decision records get a dated Correction added at the end, and no earlier text is changed. The architecture page and the two how-tos are edited directly. HOOK_DESCRIPTION changes only after a check that nothing matches on its text. Every claim the change adds holds against the code. The extra fixes for pre-existing issues are accurate too. I found nothing that needs another round.

## Checked

- Gates: I ran `loopctl gate stamp` from the worktree. Lint, format, tests, integration, r2 and r3 all passed, with stamp green e6526ff3690b18667bd08fcb3a8c83f88443bd739a60e4240f18627aa8d95939. I also ran `prek run okf-validate --all-files` (okf validate --strict) and `prek run kmctl-check --all-files`, and both passed. `kmctl review due` does not list the summary. `kmctl briefing` reports "summary current".
- r1 (judgment), checked item by item against the code:
  - ADR 0014. `apm/apm.yml` depends on okf-skills, `./claude` and `./antigravity`. `apm/.apm/` holds only `agents/kmctl-auditor.md` and `skills/`. The rules sit in `apm/claude/.apm/instructions/`, and `apm/antigravity/.apm/instructions/` holds the copy that `scripts/sync_antigravity_rules.py` writes. pyproject's force-include matches the three folders the Correction names. `kmctl plugin --help` lists only `patch`. doctor's `_lock` builds the id `{harness}.lock`, so `claude.lock` exists, and it compares `resolved_ref` with `package_ref()`. The test claims also hold: `tests/test_plugin.py` tests the shipped hooks and the MCP launcher, `tests/test_plugin_patch.py` uses fake uvx and claude and asserts `fakes.calls("uvx") == []`, and both files carry `@pytest.mark.integration` tests against APM 0.33.0.
  - ADR 0012. `APM_FILES` is the four files the Correction names, `current` refuses when any one differs from `MANIFEST`, and `set` pins `APM_DOC` and moves the `kmctl_ref` default in `COPIER`.
  - ADR 0001. The `_agents` folder is used by `antigravity.agents_dir`, which `opencode.py` imports. The `_rules` folder is used only by `opencode.py`. Both match the Correction.
  - ADR 0011. The paths are right, and the 2026-10-17 correction it refers to exists.
  - Overview. The `okf.py` importer list matches what grep finds for `from kmctl.okf` in `src/kmctl/`: checks, concepts, docs_index, handoffs, review_due, scaffold, summary, supersede and verify, plus kinds (`ALLOWED_FIELDS`). The text on `action/agent.py` matches its docstring and ADR 0017. The mermaid edge now says release.py writes the four files.
  - How-tos. `.agents/plugins/kmctl/` is `antigravity.PLUGIN_PATH`. The three Antigravity hooks match `package_hooks("antigravity")`, which lists SessionStart, PostToolUse and Stop. Dropping "`main` until then" is right now that v0.9.0 exists.
  - HOOK_DESCRIPTION. Outside `.loop/spikes` output, only `doctor._claude_hook`, through `hook_entry()`, and `tests/test_plugin.py`, through the constant, use its text. The new wording matches what `kmctl briefing` prints: the routing, the skills, the state and one reading rule.
- The concern about doctor's `claude.hook`: doctor compares the whole entry, description included, so a settings.json written by an older package now fails `claude.hook`. In that case the CLI and the package versions differ, so `claude.lock` already fails with the same fix, an update. Under ADR 0026 the pinned CLI runs doctor, so the CLI and the package match in the normal case. `_is_kmctl_hook` finds kmctl's hook by its command, so `plugin patch` still finds and replaces an older entry. This is acceptable.
- ADR 0014's front-matter description still names `kmctl plugin install --harness`. The record keeps its original text, the Amended notes and the new Correction carry the change, and the line for 0014 in `.okf/decisions/index.md` already says "(amended by ADR 0020 and ADR 0021 ...)". Leaving the description as it is follows the never-rewrite rule, so this is acceptable.
- Beyond the plan: the release.py docstrings and help, the release.yml header and PR body (its `git add` line stages all four apm.yml files), and the how-to's three hooks are all accurate. The test_apm_package change keeps the three skeleton sections as a strict prefix and lets only `Correction, YYYY-MM-DD` headings follow. The test needed this change because ADR 0014 now has a Correction section.

## Findings

None.

## Notes

- The overview says `action/agent.py` "needs nothing from kmctl". That is true of the script, which imports nothing from kmctl. Audit mode still installs kmctl and sets KMCTL_PINNED so the agent's skills can run kmctl commands. The wording matches the script's own docstring, so this is not a finding.
- Merge: main's release-cache-off also appends to `.okf/log.md` and changes `checked` in `.okf/summary.md`. Expect conflicts there when merging. Keep both log lines, and re-acknowledge the summary.
- The commit message has no "left alone" items to name, because all eight were real and are fixed.
