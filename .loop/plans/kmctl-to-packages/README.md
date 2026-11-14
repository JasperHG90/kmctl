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

The `kmctl-check` hook in `.pre-commit-hooks.yaml` keeps working for repositories that point `rev:` at a post-move tag: the hook gains `additional_dependencies: ["./packages/kmctl"]`, and the root pyproject gains a hatchling `[build-system]` that builds an empty wheel (`bypass-selection = true`), because pre-commit and prek pip-install the hook repository's root before the extra dependency. uv never builds it: `[tool.uv] package = false` stays.

## Problems

- P1: kmctl's package (`pyproject.toml`, `src/kmctl/`, its tests) sits at the repository root, so the root is both the workspace and a package, unlike `packages/kmaudit` and the operator's uv-monorepo layout; and the pieces that would have to move with it assume the root: the `parents[2]` fallbacks to `apm/` in `src/kmctl/plugin.py`, `src/kmctl/antigravity.py` and `src/kmctl/opencode.py`, both release workflows' bare `uv build`, `scripts/check_wheel.py`'s default root `pyproject.toml`, and the `kmctl-check` hook that installs the root
- P2: Every install line and install hint names the root as kmctl's source (docs, `README.md`, the hook hints, `HOOK_INSTALL`, the release notes template, the starter justfile, `action.yml`), and `scripts/release.py`'s install pattern would drop a `#subdirectory=` fragment, so each breaks once the package moves
- P3: `src/kmctl/pin.py` hands off to a uvx source with no subdirectory, which cannot install a post-move release
- P4: The knowledge bundle and the repo's own rules cite the old paths: `.okf/` `sources[].resource`, the summary, overview and manifesto, docs pages, and the `paths:` globs of local `.claude/rules/`

## Goals

- G1: The repository has the uv-monorepo shape (a workspace root that installs nothing, `packages/kmctl` and `packages/kmaudit` each a full package, one root `uv.lock`), `uv run pytest` at the root still runs every test, and the release workflows keep building, checking and publishing kmctl from its new folder until `release-per-package` reworks them
- G2: Users install kmctl from post-move tags through `#subdirectory=packages/kmctl`, and projects pinned to v0.12.1 or older keep running their pin
- G3: The knowledge bundle and rules describe the tree as it now is, and an ADR records the move

## Outcomes

### O1: The root is a workspace root that installs nothing, kmctl builds, tests and releases from packages/kmctl
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `pyproject.toml`, `new:packages/kmctl/pyproject.toml`, `new:packages/kmctl/README.md`, `new:packages/kmctl/LICENSE`, `new:packages/kmctl/src/kmctl/__init__.py`, `new:packages/kmctl/hatch_build.py`, `src/kmctl/__init__.py`, `src/kmctl/plugin.py`, `src/kmctl/antigravity.py`, `src/kmctl/opencode.py`, `uv.lock`, `tests/conftest.py`, `tests/fixtures/fake_tools.py`, `tests/test_plugin.py`, `tests/test_repo_apm.py`, `tests/test_ci.py`, `new:packages/kmctl/tests/conftest.py`, `new:packages/kmctl/tests/test_plugin.py`, `scripts/check_wheel.py`, `.github/workflows/release.yml`, `.github/workflows/release-tag.yml`, `.github/workflows/ci.yml`, `tests/scripts/test_workflows.py`, `tests/scripts/test_check_wheel.py`, `tests/scripts/test_release.py`, `.pre-commit-hooks.yaml`
- checked by: `uv sync` then `uv run kmctl --version` at the root prints `apm/apm.yml`'s version; `uv build --package kmctl` (wheel built from the sdist) and `uv build --wheel --package kmctl` both give a wheel at that version with `_skills`, `_agents` and `_rules` that `scripts/check_wheel.py` and `scripts/smoke_wheel.py` accept; the skills, agents and rules tests pass against the editable install, where `_skills`, `_agents` and `_rules` do not exist (the source-tree fallbacks find `apm/` at the root); `uv run pytest --collect-only` at the root selects 1407 tests (876 under `packages/kmctl/tests`, 276 under `tests/`, 255 under `packages/kmaudit/tests`) and `uv run pytest` passes; `tests/scripts/test_workflows.py` pins `uv build --package kmctl` and the check_wheel pyproject path in both release workflows, and ci.yml's starter job runs `new:packages/kmctl/tests/test_starter.py` (ci-per-package later splits the rest of ci.yml); the `kmctl-check` hook installs and runs from a post-move commit in another repository (the hook test in the docs front matter tests); a Release dry run on the branch passes the build and smoke-test job
- seen by: operator

### O2: The pin hand-off adds the subdirectory only for refs newer than v0.12.1
- kind: behaviour
- goal: G2
- fixes: P3
- needs: O1
- touches: `src/kmctl/pin.py`, `new:packages/kmctl/src/kmctl/pin.py`, `tests/test_pin.py`
- checked by: tests that a pin at v0.12.1 hands off to `git+https://github.com/JasperHG90/kmctl@COMMIT` and a pin at a newer tag to `...@COMMIT#subdirectory=packages/kmctl`, for the command and the not-installed notice alike
- seen by: operator

### O3: Every install line, hint, the release tooling and the action install from packages/kmctl
- kind: behaviour
- goal: G2
- fixes: P2
- needs: O1
- touches: `action.yml`, `README.md`, `docs/tutorials/get-started-with-kmctl.md`, `docs/how-to/install-the-plugin-and-the-ci-action.md`, `docs/how-to/install-kmctl-with-apm.md`, `docs/reference/commands.md`, `apm/claude/.apm/hooks/hooks.json`, `src/kmctl/plugin.py`, `.github/release-notes.md`, `starter/justfile.jinja`, `scripts/release.py`, `tests/scripts/test_release.py`, `tests/test_docs.py`, `tests/test_repo_name.py`, `tests/test_starter.py`
- checked by: `scripts/release.py set` keeps the `#subdirectory=packages/kmctl` fragment on every line it pins; the starter renders `kmctl_src` with the fragment for a newer `kmctl_ref` and without it for v0.12.1; `new:packages/kmctl/tests/test_starter.py -m integration` bootstraps from a `file://` clone; the `knowledge` CI job (`uses: ./`) passes
- seen by: operator

### O4: The knowledge bundle, docs and local rules cite the moved paths, and a new ADR records the move
- kind: behaviour
- goal: G3
- fixes: P4
- needs: O1
- touches: `.okf/summary.md`, `.okf/architecture/overview.md`, `.okf/manifesto.md`, `.okf/decisions/0043-the-audit-is-its-own-library-kmaudit-served-over-mcp.md`, `.okf/decisions/0026-the-kmctl-on-path-runs-the-release-a-project-s-lock-pins.md`, `new:.okf/decisions/0044-kmctl-and-kmaudit-are-both-workspace-packages.md`, `.claude/rules/cli-interface.md`, `.claude/rules/cli-version-floor.md`, `.claude/rules/diagrams-stay-current.md`, `.claude/rules/adversarial-reviews.md`, `.claude/rules/manifesto-invariants.md`
- checked by: `kmctl review due` reports no "source not resolved" notice; `kmctl check` and the strict okf-validate hook pass; historical records (`.okf/log.md`, `.okf/prototypes/`, eval results) keep their text
- seen by: operator

## Could invalidate this plan

- Hatchling may not build kmctl from `packages/kmctl` when the version file and the force-included skills, agents and rules sit outside the package folder ("../../apm/..."). spike:kmctl-to-packages/1 measured it: `uv build --wheel`, the git-subdirectory install and the action's folder install all pass, but plain `uv build` (wheel from the sdist) fails with "Forced include not found". Settled by a hatch build hook, `new:packages/kmctl/hatch_build.py`: it force-includes from `../../apm` when that exists (a checkout) and from the sdist's own `apm/` otherwise, with an sdist force-include copying the three folders into the sdist; spike:kmctl-to-packages/3 confirmed it: all four builds pass at apm.yml's version with `_skills`, `_agents` and `_rules`, accepted by check_wheel and smoke_wheel; the sdist needs no copy of apm.yml because hatchling reads the version from PKG-INFO. A committed symlink also passed all four builds but was rejected because a Windows checkout without `core.symlinks` turns it into a text file. `scripts/check_wheel.py` reads the hook's table instead of `[tool.hatch.build.targets.wheel.force-include]`.
- A kmctl at v0.12.1 or older on a user's PATH hands off to a project pinned to a post-move release with `uvx --from git+...@COMMIT kmctl` and no subdirectory. That fails because the root no longer builds a package. Nothing in this repository can change copies already installed. Either the operator accepts that users upgrade the CLI before pinning a post-move release (the starter's `just kmctl` already installs one as new as the pin), or D1 is reopened for a root that still builds.
- The workspace root with `package = false` may not give the dev loop this plan assumes. spike:kmctl-to-packages/2 measured it: `uv sync` installs both members editable and `uv run kmctl --version` works, but the moved conftest's `pytest_plugins = ("pytester",)` errors outside the top-level conftest and drops collection to 531 of 1407. Settled by `-p pytester` in the root pytest addopts (dropping the conftest line), which brings back exactly 1407 selected (876 kmctl, 276 root, 255 kmaudit) with no clash between the two rootless conftests; spike:kmctl-to-packages/4 confirmed it for the plan as revised (1407 selected, no collection error). The spike also showed the path fixes O1 must make: the `parents[2]` fallbacks become `parents[4]`, the 24 moved tests that use `parents[1]` as the repo root become `parents[3]`, and hard-coded `ROOT / "tests"` and root `pyproject.toml` paths (test_network_retry, test_check_wheel, test_release) are rewritten.
- The `kmctl-check` hook other repositories use (`.pre-commit-hooks.yaml`, `language: python`) may not install from a post-move tag, because pre-commit and prek pip-install the hook repository's root and the root no longer holds a package. spike:kmctl-to-packages/5 measured it with prek 0.5.5 and pre-commit 4.7.0 on the moved tree: `additional_dependencies: ["./packages/kmctl"]` alone fails in both (the root, with no `[build-system]`, falls back to setuptools' flat-layout discovery and stops), and works in both once the root pyproject also has a hatchling `[build-system]` with `[tool.hatch.build.targets.wheel] bypass-selection = true`, so pip builds an empty wheel for the root and kmctl comes from `./packages/kmctl`. `[tool.uv] package = false` still holds: `uv sync --locked` passes and installs no root package. O1 makes both changes; the operator may prefer to drop the hook for post-move tags instead.
