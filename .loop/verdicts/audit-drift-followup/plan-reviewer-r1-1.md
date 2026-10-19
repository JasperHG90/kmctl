---
type: verdict
title: 'Verdict: audit-drift-followup plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of audit-drift-followup: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-19T01:07:21+00:00'
slug: audit-drift-followup
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

Every listed mismatch is still real on today's tree (5996eb00, after v0.9.0). A few have moved to new lines, listed below. The approach is right and matches fix-audit-drift and .claude/rules/okf-bundle.md: an appended `## Correction, YYYY-MM-DD` for a decision record, a direct edit with a log line for the architecture page, and a direct edit for docs pages. The eval rows cover the intent. No risk breaks the plan.

## Checked

Each item against the code, with where it sits now:

- ADR 0014, about lines 68-73: it describes the `apm/.apm/` layout with skills, agents and instructions. The rules now live in `apm/claude/.apm/instructions/` (pyproject force-include, ADR 0020). The ADR's "Amended, 2026-10-17" notes point to ADR 0020 and 0021 but do not correct the layout, so this is real.
- ADR 0014, about line 115: "The wheel carries only the skills folder" is false. pyproject.toml force-includes `_skills`, `_agents` and `_rules`. Real.
- ADR 0014, about line 117: `kmctl plugin status` is gone; the only `plugin` command left is `patch` (src/kmctl/__init__.py:1084). Real.
- ADR 0014, about lines 151-153: "tests/test_plugin.py checks the install with fake uvx and claude" is false. test_plugin.py now tests the hook and the MCP launcher, and test_apm_package.py no longer runs a kmctl install. Real.
- ADR 0012, the 2026-10-16 Correction (lines 85-93): it says `set` copies the version to the root `apm.yml`. scripts/release.py APM_FILES writes four files (apm.yml, apm/apm.yml, apm/claude/apm.yml, apm/antigravity/apm.yml). Real.
- ADR 0001 line 59: this text sits inside the 2026-10-16 Correction ("The wheel carries only the skills"). It is false for the same pyproject reason. Real; the fix is a new Correction.
- ADR 0011 line 151: this is inside the 2026-10-16 Correction and names `apm/.apm/instructions/`. The rules now live in `apm/claude/.apm/instructions/`. Real.
- architecture/overview.md lines 17-18: "they hold no logic of their own beyond relaying it" is false now that `action/agent.py` holds the whole audit agent. Real. Line 176 has moved to 213-216, which names four modules that read through okf.py. checks, kinds, summary, docs_index, scaffold, verify and `__init__` also import it. Real.
- docs/how-to/install-kmctl-with-apm.md: lines 80-81 no longer hold it. Line 105 does: "for Antigravity it writes the same into `.agents/`", where "the same" includes the agent. That contradicts the page's own line 31 and ADR 0020/0021: APM does not write the Antigravity agents, `kmctl plugin patch` does. Real, at the new line.
- docs/how-to/install-the-plugin-and-the-ci-action.md: moved from 206 to 211 ("and `main` until then"). kmctl has tags up to v0.9.0, and the page already shows `@v0.9.0`. Real.
- HOOK_DESCRIPTION (src/kmctl/plugin.py:69-72) and apm/claude/.apm/hooks/hooks.json:9 both say "the rules". The briefing gives one reading rule and points at `.claude/rules/` (briefing.py:1 and 52). Nothing in src/ or action/ matches on the description. tests/test_plugin.py:65 compares hooks.json with `plugin.HOOK_DESCRIPTION`, so the two must change together. Spike apm-hands-back/3 shows APM tracks the hooks it installs in `.claude/apm-hooks.json` with `_apm_source`, not by description, so new wording should not leave a second hook behind on upgrade.

Eval: r1 is a judgment row that matches the intent: fix the real items, leave false ones named in the commit, and correct rather than rewrite. r2's test ids exist: `test_this_repo_docs_are_migrated` and `test_this_repository_*` in test_summary.py, where `-k this_repo` matches both names. r3 is the full suite.

## Findings

None.

## Notes

- For the builder: three of the decision items (ADR 0001:59, ADR 0011:151 and ADR 0012's 2026-10-16 Correction) are wrong text inside an earlier Correction. The fix is a new dated Correction that names the earlier one, as ADR 0001 and ADR 0011 already do. The earlier text stays as it is.
- release-cache-off also adds a Correction to ADR 0012 and touches log.md and the summary, so the second ticket to land will need a small rebase.
