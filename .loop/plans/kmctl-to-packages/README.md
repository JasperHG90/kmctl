---
type: plan
title: 'Plan: kmctl-to-packages'
description: Move kmctl into packages/kmctl and make the root a uv virtual workspace, with install lines, pins and the release build following it.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T17:22:48+00:00'
slug: kmctl-to-packages
epic: monorepo-release
depends_on: []
priority: null
schema_version: '2.0'
---

# kmctl-to-packages

Relayed from: none

## Intent

Decision D1 of the `monorepo-release` epic, with the operator's correction:
the repository takes the shape of the operator's uv-monorepo template. The
root `pyproject.toml` becomes a workspace root that installs nothing
(`[tool.uv] package = false`, `[tool.uv.workspace] members = ["packages/*"]`,
`[tool.uv.sources]` naming each member `{ workspace = true }`, both members
in the root `dev` dependency group, plus the shared ruff and pytest config).
kmctl moves to `packages/kmctl` with its own full `pyproject.toml`
(`[project]`, `[build-system]`, the hatch version regex on
"../../apm/apm.yml", and wheel force-includes of "../../apm/.apm/skills",
"../../apm/.apm/agents" and "../../apm/claude/.apm/instructions"). Its code
and its tests move with it. `packages/kmaudit/pyproject.toml` already has
that shape. One `uv.lock` stays at the root. The root keeps `action.yml`,
`action/`, `apm/`, `copier.yml`, `starter/`, `docs/`, `.okf/`, `scripts/`
and `.github/`. This partly reverses ADR 0043 ("kmctl stays at the root"),
so a new ADR records the move.

Tests: a test moves into `packages/kmctl/tests/` when its subject is the
kmctl package. It stays in the root `tests/` when it imports nothing from
`kmctl` or from kmctl's test helpers (`tests/conftest.py`, `tests/fixtures/`)
and its subject is a repo-level file. That leaves `tests/scripts/`,
`tests/test_agent.py`, `tests/test_audit.py`, `tests/test_ci.py`,
`tests/test_repo_apm.py`, `tests/test_rules.py`, `tests/test_skills.py` and
`tests/vendor/` at the root. `.pre-commit-config.yaml`'s okf-validate hook
and `tests/test_ci.py` keep the validator's path. Every other test file,
plus `tests/conftest.py` and `tests/fixtures/`, moves. The test files are
tied together by `from conftest import ...` and `from test_plugin_patch
import ...`, so splitting them further would mean rewriting helpers. The
root `tests/` gets its own small conftest only for the autouse fixtures its
tests still need (the uv cache, `KMCTL_PINNED`).

Install URLs for releases after this move become
`git+https://github.com/JasperHG90/kmctl@vX.Y.Z#subdirectory=packages/kmctl`.
Tags up to `v0.12.1` keep the root layout. So anything that builds kmctl
from a tag or commit chosen at run time adds the fragment only for refs
newer than v0.12.1: `src/kmctl/pin.py`'s uvx hand-off (ADR 0026) and the
starter's `kmctl_src` in `starter/justfile.jinja`. The rest are fixed lines
that `scripts/release.py set` rewrites and that always name the newest tag,
so they always carry the fragment: `README.md`, the three docs pages, the
hook hints in `apm/claude/.apm/hooks/hooks.json`, `HOOK_INSTALL` in
`src/kmctl/plugin.py`, and `.github/release-notes.md`. `action.yml`
installs `${{ github.action_path }}/packages/kmctl`, which matches the tag
the action runs at.

The release workflows keep working on the new path, so main can still
release between this ticket and `release-per-package`, which reworks them.
They need only the path changes: `uv build --package kmctl`, and
`scripts/check_wheel.py` reading `packages/kmctl/pyproject.toml`.

Measured on 2026-11-14 at 29502a0d: `uv run pytest --collect-only` at the
root selects 1407 of 1421 tests. `tests/` holds 1165: 277 stay at the root
(276 selected) and 888 move. `packages/kmaudit/tests` holds the other 256.
21 `.okf/` files cite `src/kmctl/`, `tests/` or `pyproject.toml` in
`sources[].resource`. The outcome that shows it worked: on the moved tree,
`uv sync` and then `uv run pytest` at the root still select the same 1407
tests and pass. `uv build --package kmctl` gives a wheel at `apm/apm.yml`'s
version that `scripts/check_wheel.py` and `scripts/smoke_wheel.py` accept.
`uv tool install` from the subdirectory prints that version.

## Problems

- P1: kmctl's package (`pyproject.toml`, `src/kmctl/`, its tests) sits at the repository root, so the root is both the workspace and a package, unlike `packages/kmaudit` and the operator's uv-monorepo layout
- P2: Every install line and install hint names the root as kmctl's source (docs, `README.md`, the hook hints, `HOOK_INSTALL`, the release notes template, the starter justfile, `action.yml`), so each breaks once the package moves
- P3: kmctl's code finds repository files by the root layout: the `parents[2]` fallbacks to `apm/` in `src/kmctl/plugin.py`, `src/kmctl/antigravity.py` and `src/kmctl/opencode.py`, and `src/kmctl/pin.py`'s uvx source with no subdirectory
- P4: The release tooling assumes a root project: both release workflows run a bare `uv build`, `scripts/check_wheel.py` defaults to the root `pyproject.toml`, and `scripts/release.py`'s install pattern would drop a `#subdirectory=` fragment
- P5: The knowledge bundle and the repo's own rules cite the old paths: `.okf/` `sources[].resource`, the summary, overview and manifesto, docs pages, and the `paths:` globs of local `.claude/rules/`

## Goals

- G1: The repository has the uv-monorepo shape (a workspace root that installs nothing, `packages/kmctl` and `packages/kmaudit` each a full package, one root `uv.lock`), and `uv run pytest` at the root still runs every test
- G2: Users install kmctl from post-move tags through `#subdirectory=packages/kmctl`, and projects pinned to v0.12.1 or older keep running their pin
- G3: The release workflows keep building, checking and publishing kmctl from its new folder until `release-per-package` reworks them
- G4: The knowledge bundle and rules describe the tree as it now is, and an ADR records the move

## Outcomes

### O1: The root is a workspace root that installs nothing, and kmctl builds from packages/kmctl
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `pyproject.toml`, `new:packages/kmctl/pyproject.toml`, `new:packages/kmctl/README.md`, `new:packages/kmctl/LICENSE`, `new:packages/kmctl/src/kmctl/__init__.py`, `new:packages/kmctl/src/kmctl/pin.py`, `new:packages/kmctl/hatch_build.py`, `scripts/check_wheel.py`, `src/kmctl/__init__.py`, `uv.lock`
- checked by: `uv sync` then `uv run kmctl --version` at the root prints `apm/apm.yml`'s version; `uv build --package kmctl` (wheel built from the sdist) and `uv build --wheel --package kmctl` both give a wheel at that version with `_skills`, `_agents` and `_rules` that `scripts/check_wheel.py` and `scripts/smoke_wheel.py` accept; `tests/scripts/test_release.py` and `tests/scripts/test_check_wheel.py` read `packages/kmctl/pyproject.toml`
- seen by: operator

### O2: kmctl's tests live in packages/kmctl/tests, and repo-level tests stay in tests/
- kind: support
- goal: G1
- fixes: P1
- needs: O1
- touches: `tests/conftest.py`, `tests/fixtures/fake_tools.py`, `tests/test_plugin.py`, `new:packages/kmctl/tests/conftest.py`, `new:packages/kmctl/tests/test_plugin.py`, `tests/test_ci.py`
- checked by: `uv run pytest --collect-only` at the root selects 1407 tests (888 under `packages/kmctl/tests`, 276 under `tests/`, the rest under `packages/kmaudit/tests`), and `uv run pytest` passes
- seen by: nobody

### O3: kmctl's source-tree fallbacks find apm/ at the repository root from the new folder
- kind: support
- goal: G1
- fixes: P3
- needs: O1
- touches: `src/kmctl/plugin.py`, `src/kmctl/antigravity.py`, `src/kmctl/opencode.py`
- checked by: the existing skills, agents and rules tests pass against the editable install, where `_skills`, `_agents` and `_rules` do not exist
- seen by: nobody

### O4: The pin hand-off adds the subdirectory only for refs newer than v0.12.1
- kind: behaviour
- goal: G2
- fixes: P3
- needs: O1
- touches: `src/kmctl/pin.py`, `tests/test_pin.py`
- checked by: tests that a pin at v0.12.1 hands off to `git+https://github.com/JasperHG90/kmctl@COMMIT` and a pin at a newer tag to `...@COMMIT#subdirectory=packages/kmctl`, for the command and the not-installed notice alike
- seen by: operator

### O5: Every install line, hint and the action install from packages/kmctl
- kind: behaviour
- goal: G2
- fixes: P2
- needs: O1
- touches: `action.yml`, `README.md`, `docs/tutorials/get-started-with-kmctl.md`, `docs/how-to/install-the-plugin-and-the-ci-action.md`, `docs/how-to/install-kmctl-with-apm.md`, `docs/reference/commands.md`, `apm/claude/.apm/hooks/hooks.json`, `src/kmctl/plugin.py`, `.github/release-notes.md`, `starter/justfile.jinja`, `scripts/release.py`, `tests/scripts/test_release.py`, `tests/test_docs.py`, `tests/test_repo_name.py`, `tests/test_starter.py`
- checked by: `scripts/release.py set` keeps the `#subdirectory=packages/kmctl` fragment on every line it pins; the starter renders `kmctl_src` with the fragment for a newer `kmctl_ref` and without it for v0.12.1; `tests/test_starter.py -m integration` bootstraps from a `file://` clone; the `knowledge` CI job (`uses: ./`) passes
- seen by: operator

### O6: The release workflows build and check kmctl from packages/kmctl, and CI's starter job follows the moved test
- kind: behaviour
- goal: G3
- fixes: P4
- needs: O1
- touches: `.github/workflows/release.yml`, `.github/workflows/release-tag.yml`, `.github/workflows/ci.yml`, `scripts/check_wheel.py`, `tests/scripts/test_workflows.py`, `tests/scripts/test_check_wheel.py`
- checked by: `tests/scripts/test_workflows.py` pins `uv build --package kmctl` and the check_wheel pyproject path in both workflows, and that ci.yml's starter job runs packages/kmctl/tests/test_starter.py (ci-per-package later splits the rest of ci.yml); a Release dry run on the branch passes the build and smoke-test job
- seen by: operator

### O7: The knowledge bundle, docs and local rules cite the moved paths, and a new ADR records the move
- kind: behaviour
- goal: G4
- fixes: P5
- needs: O1
- touches: `.okf/summary.md`, `.okf/architecture/overview.md`, `.okf/manifesto.md`, `.okf/decisions/0043-the-audit-is-its-own-library-kmaudit-served-over-mcp.md`, `.okf/decisions/0026-the-kmctl-on-path-runs-the-release-a-project-s-lock-pins.md`, `new:.okf/decisions/0044-kmctl-and-kmaudit-are-both-workspace-packages.md`, `.claude/rules/cli-interface.md`, `.claude/rules/cli-version-floor.md`, `.claude/rules/diagrams-stay-current.md`, `.claude/rules/adversarial-reviews.md`, `.claude/rules/manifesto-invariants.md`
- checked by: `kmctl review due` reports no "source not resolved" notice; `kmctl check` and the strict okf-validate hook pass; historical records (`.okf/log.md`, `.okf/prototypes/`, eval results) keep their text
- seen by: operator

## Could invalidate this plan

- Hatchling may not build kmctl from `packages/kmctl` when the version file and the force-included skills, agents and rules sit outside the package folder ("../../apm/..."). spike:kmctl-to-packages/1 measured it: `uv build --wheel`, the git-subdirectory install and the action's folder install all pass, but plain `uv build` (wheel from the sdist) fails with "Forced include not found". Settled by a hatch build hook, `new:packages/kmctl/hatch_build.py`: it force-includes from `../../apm` when that exists (a checkout) and from the sdist's own `apm/` otherwise, with an sdist force-include copying the three folders into the sdist; spike:kmctl-to-packages/3 confirmed it: all four builds pass at apm.yml's version with `_skills`, `_agents` and `_rules`, accepted by check_wheel and smoke_wheel; the sdist needs no copy of apm.yml because hatchling reads the version from PKG-INFO. A committed symlink also passed all four builds but was rejected because a Windows checkout without `core.symlinks` turns it into a text file. `scripts/check_wheel.py` reads the hook's table instead of `[tool.hatch.build.targets.wheel.force-include]`.
- A kmctl at v0.12.1 or older on a user's PATH hands off to a project pinned to a post-move release with `uvx --from git+...@COMMIT kmctl` and no subdirectory. That fails because the root no longer builds a package. Nothing in this repository can change copies already installed. Either the operator accepts that users upgrade the CLI before pinning a post-move release (the starter's `just kmctl` already installs one as new as the pin), or D1 is reopened for a root that still builds.
- The workspace root with `package = false` may not give the dev loop this plan assumes. spike:kmctl-to-packages/2 measured it: `uv sync` installs both members editable and `uv run kmctl --version` works, but the moved conftest's `pytest_plugins = ("pytester",)` errors outside the top-level conftest and drops collection to 531 of 1407. Settled by `-p pytester` in the root pytest addopts (dropping the conftest line), which brings back exactly 1407 selected (876 kmctl, 276 root, 255 kmaudit) with no clash between the two rootless conftests; spike:kmctl-to-packages/4 confirmed it for the plan as revised (1407 selected, no collection error). The spike also showed the path fixes O2 and O3 must make: the `parents[2]` fallbacks become `parents[4]`, the 24 moved tests that use `parents[1]` as the repo root become `parents[3]`, and hard-coded `ROOT / "tests"` and root `pyproject.toml` paths (test_network_retry, test_check_wheel, test_release) are rewritten.
