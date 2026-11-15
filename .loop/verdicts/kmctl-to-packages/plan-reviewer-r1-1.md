---
type: verdict
title: 'Verdict: kmctl-to-packages plan-reviewer round 1'
description: 'plan-reviewer verdict for round 1 of kmctl-to-packages: fail.'
tags:
- verdict
- plan
generated:
  by: claude-opus/5.5
  at: '2026-11-14T19:47:47+00:00'
slug: kmctl-to-packages
pass: plan-reviewer
round: 1
body_schema: verdict/1
---

## Summary

Fail. The listed risks are settled: spike 3 settles risk 1, the operator accepted risk 2, and spikes 2 and 4 settle risk 3. One risk is missing: the `kmctl-check` pre-commit hook other repos install from the root (p1). It needs a spike. p2 to p4 are Outcomes facts that disagree with the prose and would mislead plan.split. With one real risk there is no case for splitting the ticket.

## Checked

- Risk 1: spikes 1 and 3. All four build paths pass with the hatch hook, at apm.yml's version, and check_wheel and smoke_wheel accept the result. Spike 1 rejected the symlink for a sound reason.
- Risk 2: the operator's acceptance, per plan lint.
- Risk 3: spikes 2 and 4. `-p pytester` restores 1407 selected with no collection errors, and the two rootless conftests do not clash. Spike 4 checked collection only. Spike 2's 31 run failures come from hard-coded root paths, which is build work.
- Repo claims: kmctl does not depend on kmaudit, so the subdirectory install needs no sibling member. pin.py's `Pin` carries `ref`, so the v0.12.1 cutoff can be decided. copier.yml validates `kmctl_ref` as a release tag. The `parents[2]` fallbacks sit at plugin.py:160, antigravity.py:95 and opencode.py:120. `.pre-commit-hooks.yaml` exports a `language: python` hook, and tests/test_docs_frontmatter.py has an integration test that installs it from a snapshot of this checkout.

## Findings

- p1: the exported pre-commit hook installs from the repo root, and the root stops being installable. Spike question below.
- p2: O1 cannot ship without O2, O3 and O6's workflow path change. O2 and O3 are supports that nothing needs.
- p3: O6 waits on O2 (the starter test's new path), and O4 and O5 touch test files that O2 moves, but none of them lists O2 in `needs`.
- p4: release.py's fragment handling is in P4, but O5, the outcome that changes it, only fixes P2.

## Notes

- O2's checked-by says 888 selected under packages/kmctl/tests. The spikes measured 876 selected (888 held) and 255 for kmaudit.
- Eval r5 runs `pytest tests -k install_subdirectory`. The docs, repo-name and starter tests move, so that command would not reach them.
- Root tests that stay, such as test_repo_apm.py (reads root pyproject.toml) and test_rules.py (cites src/kmctl), also need edits that no outcome's touches list.
