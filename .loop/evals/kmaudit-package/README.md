---
type: eval
title: 'Eval: kmaudit-package'
description: 'Definition of done for kmaudit-package: 7 row(s).'
tags:
- eval
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-14T11:38:52+00:00'
slug: kmaudit-package
signoff:
  signer: delegated:jasperginn@gmail.com/claude-main
  hash: 94a41d0f7dfb74a64be9910a3bd164fece21de376c6a2a4dd52e5d7a5070f63c
  at: '2026-11-14T11:38:52+00:00'
verified: null
---

Rows: rows.json; the fields each row takes: loopctl schema eval-rows.

- r1: kmaudit, built as a wheel from packages/kmaudit and installed into a fresh virtual environment that does not have kmctl, runs `kmaudit claims todo --json` on a fixture OKF bundle in a git repository and prints its sections.
  Fails when: the wheel does not build, kmctl gets installed alongside it, the command exits nonzero, or it prints no section of the fixture bundle
- r2: No Python module under packages/kmaudit imports kmctl, and kmaudit's pyproject.toml does not depend on kmctl.
  Fails when: any module under packages/kmaudit/src or packages/kmaudit/tests has an import of kmctl, or kmaudit's dependencies name kmctl
- r3: One `uv run pytest` at the repository root collects and runs both kmctl's tests under tests/ and kmaudit's under packages/kmaudit/tests.
  Fails when: the root run collects no test from packages/kmaudit/tests or none from tests/, or collection errors
- r4: kmctl has no audit group and no audit extra: `kmctl audit --help` fails as an unknown command and kmctl's package metadata lists no audit extra; the shipped agents' guard hook calls `kmaudit guard --allow GROUP`, and the guard lets through only `kmaudit GROUP` commands.
  Fails when: `kmctl audit` still resolves to a command group, kmctl's metadata Provides-Extra includes audit, an agent's hook still calls kmctl audit guard, or the guard allows a `kmctl audit` command
- r5: Every audit behaviour tested before the move is still tested after it: the audit tests that lived under tests/ run under packages/kmaudit/tests against kmaudit and pass.
  Fails when: an audit test from tests/ was deleted rather than moved (other than the CLI name changing from kmctl audit to kmaudit), or the moved tests fail
- r6: Outside .loop/, .okf/log.md, .okf/prototypes/, .okf/decisions/ and the Action's own audit-mode refusal (action.yml and docs/how-to/install-the-plugin-and-the-ci-action.md), no tracked file says `kmctl audit` or `kmctl[audit]`; the root README names the two packages and links packages/kmaudit/README.md.
  Fails when: git grep finds `kmctl audit` or `kmctl[audit]` in a file outside those exclusions, or README.md does not link packages/kmaudit/README.md
- r7 (judgment): A new decision record says the audit left kmctl to become kmaudit, a separate package in this monorepo served over MCP, names the alternative it rejected (keeping kmctl audit, or moving kmctl into packages/ too), and marks the records it supersedes; the OKF bundle validates strictly.
  Fails when: no such record exists, it names no rejected alternative, or okf validate --strict fails
