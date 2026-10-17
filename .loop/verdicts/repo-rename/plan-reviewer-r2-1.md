---
type: verdict
title: 'Verdict: repo-rename plan-reviewer round 2'
description: 'plan-reviewer verdict for round 2 of repo-rename: pass.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-10-17T18:52:45+00:00'
slug: repo-rename
pass: plan-reviewer
round: 2
body_schema: verdict/1
---

## Summary

Both round-1 findings are settled and I found no new risk that could break the plan. Dropping pin_apm_doc removes the release refusal and stops the Older installs example from being rewritten (p1). The plan and r1 now keep the old name where it describes a v0.3.0 install (p2). The spike still settles the one listed risk.

## Checked

- scripts/release.py: set_version runs pin_docs over APM_DOC before pin_apm_doc, so dropping pin_apm_doc and its count==0 refusal still pins the page's `uv tool install` line. DOC_LINES (6) does not change with the rename, since _INSTALL and _USES move to the new name together with the docs lines.
- `git grep -i jasperhg90/knowledge-management` outside .okf/decisions and .loop: every hit is either in the plan's rename list or in its keep list. In docs/how-to/install-kmctl-with-apm.md the hits are lines 53 and 64 (renamed) and 135 (kept). In docs/reference/commands.md, 337 is kept, and 341 (the entry patch suggests) and 453 (the uninstall name example) get renamed. Both of those describe the new install, so renaming them is correct and matches r1.
- The `apm uninstall github.com/JasperHG90/Knowledge-management/apm` lines in README.md:175 and install-the-plugin-and-the-ci-action.md:506 remove a current install. uninstall_name builds the name from the entry's own git URL, so after the rename the new name is right for a new install. The docs already say the name comes from the entry's `git:` URL.
- plugin.py: _old_layout, _names_old_package and OLD_PACKAGE match the old name in lowercase. _old_entry and the refusal at :736 use the entry's own name, so old installs are still refused correctly. The plan keeps these and adds the new name, and r3 tests both.
- Spike repo-rename/1: README outcome. APM 0.33.0 locks a new-URL install as kmctl at virtual_path apm, which is what kmctl_package matches.
- Other spellings: the only other `Knowledge-management` hits are the explanation page's title (not the repo) and tests/test_apm_package.py:442. No hits in pyproject.toml, action.yml or .github.
- /home/vscode/kmctl-starter: commit 8ec63a6 already names JasperHG90/kmctl, and no old-name hit remains there.

## Findings

- p1: resolved. pin_apm_doc, _APM_PIN and the "no pin; restore it" refusal go, and r4 pins the behaviour.
- p2: resolved. The keep list and r1's exceptions now cover the docs and tests that describe v0.3.0 installs.

## Notes

The build will have to rewrite tests/test_apm_package.py's test_docs_release_set_moves_the_page_pins (around :432), because it asserts every APM pin in the page moves to the new version. That is now the opposite of r4. The plan covers it under "the tests that name it", so it is not a finding. The kmctl-starter change is already committed (8ec63a6), so that part of the ticket only needs confirming.
