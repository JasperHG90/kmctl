---
type: plan
title: 'Plan: kmaudit-package'
description: Move the audit out of kmctl into its own package, kmaudit, that runs without kmctl.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T11:31:31+00:00'
slug: kmaudit-package
epic: kmaudit
depends_on: []
priority: 1
schema_version: '2.0'
---

# kmaudit-package

Relayed from: none

## Intent

The operator decided the audit is not part of kmctl: kmctl is an optional
helper for organising knowledge with coding agents, and the audit becomes its
own library, kmaudit, and the repository becomes a monorepo of two distinct
packages. kmctl stays at the root, so its install URLs, the GitHub Action and
the release flow keep working; kmaudit is a uv workspace member beside it.
This ticket is the move, nothing more. Measured today: of the 16 audit
modules, 2 import `src/kmctl/okf.py` (the front matter reader) and 1 imports
`src/kmctl/tracing.py`; nothing else in kmctl imports the audit except the
CLI group. The audit code
(`src/kmctl/claims/`, `src/kmctl/judge.py`, `src/kmctl/audit_settings.py`,
`src/kmctl/tracing.py` and the `audit` group in `src/kmctl/__init__.py`) moves
to a uv workspace member, `new:packages/kmaudit/pyproject.toml`, with the code
under `new:packages/kmaudit/src/kmaudit/__init__.py` and its tests under
`new:packages/kmaudit/tests/conftest.py`. kmaudit carries its own copy of the
two front matter helpers it reads from `src/kmctl/okf.py`, so it imports
nothing from kmctl. Its CLI keeps today's verbs under a `kmaudit` command
(`kmaudit claims todo`, `kmaudit checks try`, ...), and kmctl loses its
`audit` group and its `audit` extra. The store stays where it is
(.kmctl/audit.sqlite); the next tickets in the epic move it, add
namespaces, the MCP server and the slim CLI.

The agents' guard hook, the skills and agents that call `kmctl audit`, and
the test pinning the hook change together with the removal, so no state has
an agent hook calling a missing command. The docs, README and a decision
record follow. Accepted decision records keep their history notes ("found by
the first `kmctl audit checks` run" stays true), and the Action's own
audit-mode refusal ("kmctl audit: refused for event ...") is a different
audit and keeps its text. After this ticket kmaudit has no install route for
users yet; the epic adds one before it leaves the integration branch.

It worked when kmaudit's tests pass in a fresh environment that has kmaudit
installed and kmctl not, and `kmctl audit` no longer exists.

## Problems

- P1: The audit lives inside kmctl, so nobody can audit a folder of docs without installing kmctl and following its layout.
- P2: kmctl carries the audit's CLI group, extra and dependencies though the operator now wants kmctl optional.
- P3: The skills, agents, docs, README and decision records describe the audit as `kmctl audit` and the repository as one package.

## Goals

- G1: kmaudit is a library of its own that installs and runs without kmctl.
- G2: kmctl no longer holds or advertises the audit.

## Outcomes

### O1: kmaudit installs and runs with kmctl absent
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `new:packages/kmaudit/pyproject.toml`, `new:packages/kmaudit/src/kmaudit/__init__.py`, `new:packages/kmaudit/src/kmaudit/store.py`, `new:packages/kmaudit/src/kmaudit/ui.html`, `new:packages/kmaudit/tests/__init__.py`, `new:packages/kmaudit/tests/conftest.py`, `new:packages/kmaudit/tests/test_store.py`, `new:packages/kmaudit/tests/fixtures/__init__.py`, `new:packages/kmaudit/tests/fixtures/audit_repo.py`, `src/kmctl/claims/*.py`, `src/kmctl/claims/ui.html`, `src/kmctl/judge.py`, `src/kmctl/audit_settings.py`, `src/kmctl/tracing.py`, `pyproject.toml`
- checked by: a test that builds the kmaudit wheel, installs it into a new venv without kmctl and runs `kmaudit claims todo` on a fixture bundle; and a test that no module under packages/kmaudit imports kmctl
- seen by: operator

### O2: The root gates run kmaudit's tests next to kmctl's
- kind: support
- goal: G1
- fixes: P1
- needs: O1
- touches: `pyproject.toml`, `uv.lock`
- checked by: kmaudit is a workspace source in the root dev group, so a plain `uv sync` installs it; `uv run pytest` at the root collects the tests under packages/kmaudit/tests and tests/ in one run
- seen by: nobody

### O3: kmctl has no audit group or extra, and the agents' guard hook calls kmaudit
- kind: support
- goal: G2
- fixes: P2
- needs: O1
- touches: `src/kmctl/__init__.py`, `src/kmctl/claims/guard.py`, `pyproject.toml`, `tests/test_apm_package.py`, `apm/.apm/agents/kmctl-check-writer.md`, `apm/.apm/agents/kmctl-claims-extractor.md`, `apm/.apm/skills/extract-claims/SKILL.md`, `apm/.apm/skills/write-checks/SKILL.md`, `apm/.apm/skills/extract-claims/evals/evals.json`, `apm/.apm/skills/write-checks/evals/evals.json`
- checked by: a test that `kmctl audit --help` exits 2 as an unknown command and that kmctl's metadata names no audit extra; `tests/test_apm_package.py` pins the agents' hook command as `kmaudit guard --allow GROUP`, and the guard lets through `kmaudit GROUP` commands only
- seen by: operator

### O4: Docs, the README and a decision record name kmaudit
- kind: support
- goal: G2
- fixes: P3
- needs: O3
- touches: `README.md`, `new:packages/kmaudit/README.md`, `AGENTS.md`, `docs/reference/commands.md`, `.okf/manifesto.md`, `.okf/architecture/audit-pipeline.md`, `.okf/architecture/overview.md`, `.okf/architecture/index.md`, `apm/.apm/skills/extract-claims/evals/results.md`, `apm/.apm/skills/write-checks/evals/results.md`, `new:.okf/decisions/0043-the-audit-is-its-own-library-kmaudit-served-over-mcp.md`
- checked by: `git grep "kmctl audit"` finds nothing outside .loop/, .okf/log.md, .okf/prototypes/, .okf/decisions/ (accepted records keep their history notes; superseded ones keep their text), and the Action's own audit-mode refusal in `action.yml` and `docs/how-to/install-the-plugin-and-the-ci-action.md`; okf validate --strict passes; the root README names both packages and links kmaudit's own README
- seen by: operator

## Could invalidate this plan

- Running both test trees from the root in one pytest run may clash: both
  have a `conftest.py` and kmctl's tests import `fixtures.audit_repo` as a
  top-level package, so a second `tests/` tree with its own `fixtures` could
  fail collection or shadow the other, forcing a different layout (a separate
  gate per package, or importlib import mode across 1400 tests).
  spike:kmaudit-package/1 settles it: with `__init__.py` in
  packages/kmaudit/tests/ and its fixtures/, and relative fixture imports
  there, one root run collects both trees with duplicate names; kmctl's
  tests stay as they are. Without the `__init__.py`, kmaudit's tests silently
  load kmctl's fixtures, so building must add both files.
