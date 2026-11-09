---
type: plan
title: 'Plan: antigravity-apm-audit'
description: 'Rename okf''s MCP server okf-bundle to bundle so apm audit --ci passes its lockfile check, and give a frozen-install gate for the drift Antigravity''s patch causes (issue #28).'
tags:
- plan
generated:
  by: process:loopctl/2.2.2.dev1+gd84319696
  at: '2026-10-19T14:29:44+00:00'
slug: antigravity-apm-audit
epic: null
depends_on: []
priority: null
---

# antigravity-apm-audit

<!-- This template was registered in planning. To capture an idea as a stub
instead (intent for later, promoted by the operator), write the plan with
`status: draft` in its front matter before running loopctl ticket register.
A hand-written plan's front matter needs type: plan, title, description and
slug; loopctl ticket register fills in generated. Optional: epic, depends_on,
priority, status, strictness and blocking. -->

Relayed from: none
<!-- When this ticket carries a finding raised while building another ticket,
replace "none" with that ticket's slug and the finding, in one line (ADR 0001). -->

## Intent

Issue #28 says `uvx --from apm-cli==0.33.0 apm audit --ci` fails after
`kmctl plugin patch` for Antigravity, so it cannot be a CI gate. The spikes
confirm it and find more (spike:antigravity-apm-audit/3):

- `config-consistency` fails for every target, Claude Code alone too:
  "bundle: in manifest but not in lockfile". okf-skills declares its own
  server `bundle`, APM skips a transitive server, and kmctl re-declares it
  under another name, `okf-bundle` (`apm/apm.yml`). `--no-drift` still
  exits 1 on it.
- `drift` fails for Antigravity only, on .agents/hooks.json, because
  `drop_apm_okf_stop` (`src/kmctl/antigravity.py`) takes okf's Stop handler
  out after install, as ADR 0018
  (`.okf/decisions/0018-kmctl-runs-okf-s-stop-check-for-antigravity.md`)
  decided. No APM option keeps that handler out at install
  (spike:antigravity-apm-audit/4), so this drift stays.

The change:

1. Rename kmctl's okf MCP server from `okf-bundle` to `bundle`. With one
   direct server `bundle`, holding kmctl's launcher, `config-consistency`
   passes and kmctl's launcher is the one APM writes to `.mcp.json` and
   .agents/mcp_config.json (spike:antigravity-apm-audit/4). Every place
   that names the server changes with it, and nothing keeps the old name,
   because kmctl has no users yet:
   - `apm/apm.yml` (the entry and its comment) and `MCP_NAME` in
     `src/kmctl/plugin.py`, which `src/kmctl/doctor.py`,
     `src/kmctl/antigravity.py` and `src/kmctl/opencode.py` import, plus the
     docstrings in `src/kmctl/plugin.py` and `src/kmctl/doctor.py` and the
     `plugin patch` help in `src/kmctl/__init__.py`.
   - `drop_old_mcp` in `src/kmctl/plugin.py` goes, with its notes in
     `patch` and the help text. It removes a server under kmctl's name
     that is not kmctl's launcher, which only an older kmctl wrote. Under
     the name `bundle` it would delete okf's own server, which okf writes
     under that name. With it go the tests that drive it in
     `tests/test_plugin_patch.py` and `tests/test_doctor.py`.
   - Doctor's okf-mcp checks (`src/kmctl/doctor.py`) pass a `bundle`
     server that runs okf's script, kmctl's launcher or not, as they already
     pass an okf server under another name (`other_okf_server`). Only a
     `bundle` that runs no okf script fails as "not the one kmctl's package
     declares".
   - Docs that name the server: `README.md`,
     `docs/how-to/install-kmctl-with-apm.md`,
     `docs/how-to/install-the-plugin-and-the-ci-action.md`, and
     `docs/reference/commands.md` (the patch steps, the doctor table, the
     `claude mcp remove` lines), plus the diagrams and table in
     `.okf/architecture/overview.md`.
   - Tests that pin the name: `tests/test_apm_package.py`,
     `tests/test_doctor.py`, `tests/test_opencode.py`,
     `tests/test_plugin_patch.py`.
   The knowledge rule called `okf-bundle` (`okf-bundle.md`, its
   `apm/antigravity/.apm/instructions/okf-bundle.instructions.md` copy, the
   `okf-bundle` key in `tests/test_apm_package.py`'s rule table) and the
   first decision's slug `0001-keep-project-knowledge-in-an-okf-bundle` keep
   their names: they are not the server. No skill or rule names a tool id
   such as `mcp__okf-bundle__*` (grep finds none).
2. A gate for drift. On a clean checkout, `apm install --frozen`, then
   `kmctl plugin patch`, then fail if `git status --porcelain` prints
   anything. ADR 0030
   (`.okf/decisions/0030-projects-commit-what-apm-deploys.md`) has projects
   commit what gets installed, so this catches a committed hand edit to an
   installed file for every harness (spike:antigravity-apm-audit/2). The
   starter justfile (`starter/justfile.jinja`) gets one recipe for it,
   beside `install-frozen` (name settled in the build, for example
   `check-install`), whose comment says it needs a clean checkout because an
   uncommitted edit is overwritten without a word. The starter CI workflow
   stays as it is: while kmctl's repository is private, a project's CI cannot
   fetch the package without a token.
3. Docs. Step 4 of `docs/how-to/install-the-plugin-and-the-ci-action.md`
   says what to run in CI: `apm audit --ci` for a Claude Code-only install;
   `apm audit --ci --no-drift` plus the gate for Antigravity, because
   `drift` reports .agents/hooks.json there by design (ADR 0018). The
   Antigravity part of step 2 points to it, and
   `docs/how-to/start-a-repository-with-kmctl-starter.md` lists the recipe in
   its justfile row. Whether `drift` also fires for OpenCode, whose agents
   patch rewrites, is checked in the build and the docs say what it finds.
4. Knowledge. Dated Corrections: ADR 0014
   (`.okf/decisions/0014-apm-is-the-only-install-route.md`), which named the
   server `okf-bundle`, and ADR 0020
   (`.okf/decisions/0020-apm-installs-the-hooks-mcp-server-and-rules-kmctl-patches-the-rest.md`),
   which declares it in `apm/apm.yml` and removes an older kmctl's entry,
   get the new name, the reason (issue #28, spike:antigravity-apm-audit/4)
   and the end of `drop_old_mcp`; ADR 0019
   (`.okf/decisions/0019-kmctl-plugin-remove-uninstalls-the-package-and-reinstalls-the-harnesses-kept.md`)
   gets its name updated. ADR 0018 gets a dated Consequence that
   `apm audit --ci` reports drift on .agents/hooks.json while kmctl removes
   the handler, and the gate is the drift check. `.okf/log.md` gets a line.
   No upstream APM issue is filed.

The outcome that shows it worked: `test_bootstrap_installs_this_checkout`
in `tests/test_starter.py`, which bootstraps a starter project for claude,
antigravity and opencode, goes on to run
`apm audit --ci --no-drift --no-policy` (no git remote there) and sees exit
0, then commits the project, clones it fresh and sees the gate recipe exit 0
with `git status --porcelain` empty; after a one-line edit to a skill under
.agents/skills/ is committed and cloned fresh, the gate exits nonzero. A
render test in `tests/test_starter.py` checks the recipe is in the
justfile. Unit tests in `tests/test_doctor.py` cover a `bundle` that runs
okf's script but not kmctl's launcher (pass) and one that runs neither
(fail).

## Could invalidate this plan

- The gate might fail on a clean project. Settled by
  spike:antigravity-apm-audit/2: on a fresh clone, `apm install --frozen`
  plus `kmctl plugin patch` leaves `git status --porcelain` empty, and a
  committed edit shows; an uncommitted edit is overwritten, so the test
  commits and clones first.
