---
type: verdict
title: 'Verdict: kmctl-to-packages reviewer round 1'
description: 'reviewer verdict for round 1 of kmctl-to-packages: fix.'
tags:
- verdict
- review
generated:
  by: claude-opus/5.5
  at: '2026-11-14T20:44:07+00:00'
slug: kmctl-to-packages
pass: reviewer
round: 1
body_schema: verdict/1
---

## Summary

The move does what the plan says. The root is a virtual uv workspace, kmctl builds, tests and releases from packages/kmctl, the pin hand-off and the starter add the subdirectory only after v0.12.1, every fixed install line carries the fragment, and the bundle and rules cite the new paths. I re-ran the gate stamp and it is green, integration tests included. One small gap is left: the plan's root conftest for the uv cache was never added. I trust a plain fix for it, so the verdict is fix.

## Checked

- `loopctl gate stamp` from the worktree: lint, format, tests and integration pass, and eval rows r1 to r6 pass. Stamp green, 1967960450a15cb2fd6c60f6a838ec971a7cb7ebd14044692dcce5ddcac57d15.
- Read the diff against agent-audit: the root and kmctl pyproject files, hatch_build.py, uv.lock, the pin.py, plugin.py, antigravity.py and opencode.py changes (the parents[4] fallbacks resolve to the repo root from packages/kmctl/src/kmctl), check_wheel.py, release.py's regexes and replacements, starter/justfile.jinja, action.yml, .pre-commit-hooks.yaml, both release workflows, ci.yml, the moved conftest (tree_repo's opt-in bump), ADR 0044 and the 0026 and 0043 amendments, the overview, manifesto, summary, docs and rule globs.
- Eval rows. r1: test_workspace_layout.py asserts package = false, no root src/, members packages/*, each member a workspace source in the dev group, and kmctl's version path. r2: the package_build test builds both ways, checks the wheel name against apm.yml's version and the three folders, and runs check_wheel and smoke_wheel. r3: the stamp ran the whole non-integration suite with no collection error (root tests/ 288 collected, packages/kmctl/tests 895). r4: test_pin's parametrised uvx_source test covers v0.12.1rc1, v0.12.1, v0.12.2, pre-releases and a branch, for both the command and the notice, plus real hand-off and briefing calls through the fake uvx. test_starter renders kmctl_src for refs on both sides of v0.12.1. r5: the tests compare action.yml's exact install line and HOOK_INSTALL, scan every AT_REF match in the README, docs, hooks.json and the release-notes template for the fragment, and check that release.py set adds it once over two runs. r6: kmctl check passes, `kmctl review due` prints no "source not resolved" notice, test_bundle_valid runs the strict validator, and ADR 0044 exists.
- Edge cases I checked by hand. The starter's version compare strips a/b/rc the same way pin.py orders them: v0.12.1rc1 gets no fragment and v0.12.2rc1 gets it. copier's validator keeps kmctl_ref a tag, so the int split cannot fail. The hook hint's trailing full stop has the same copy-paste hazard as before; this change does not make it new.

## Findings

- f1: the plan's Intent says the root tests/ gets a small conftest for the autouse fixtures (the uv cache, KMCTL_PINNED). There is none. No root test runs a real kmctl, so KMCTL_PINNED is not needed. But the root integration tests that call uv build, uv venv and uv pip install now use the user's shared cache when run alone, for example `uv run pytest tests -m integration`. Add tests/conftest.py with the session `_uv_cache` fixture (moving it to a shared place both conftests import would also do). Non-blocking: it is a plain copy, and nothing ships wrong.

## Notes

- As the plan and ADR 0044 accept, until the next release the README and docs on main show `@v0.12.1#subdirectory=packages/kmctl`, which that tag cannot build. install-kmctl-with-apm.md says to leave the fragment out for v0.12.1, right under a v0.12.1 line that carries it. The version pull request clears this, so it is not a finding.
- The hermes triage area `src` became `packages`, which is outside the plan's touches but needed now that src/ is gone. Old `area/src` labels stay on existing issues.
- I did not verify the Release dry run or the knowledge CI job, which need GitHub.
