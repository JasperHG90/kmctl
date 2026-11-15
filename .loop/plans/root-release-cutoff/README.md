---
type: plan
title: 'Plan: root-release-cutoff'
description: v0.12.2 was built from the repository root, so the subdirectory cutoff moves from v0.12.1 to v0.12.2, and release.py set writes the fragment only for releases after it.
tags:
- plan
generated:
  by: process:loopctl/2.3.1.dev65+g93b143856
  at: '2026-11-15T04:45:45+00:00'
slug: root-release-cutoff
epic: monorepo-release
depends_on: []
priority: 1
schema_version: '2.0'
---

# root-release-cutoff

Relayed from: none

## Intent

kmctl-to-packages assumed v0.12.1 was the last release built from the
repository root, and wrote that as the cutoff in three places: `LAST_ROOT_RELEASE`
in `packages/kmctl/src/kmctl/pin.py` (the uvx hand-off), the `> [0, 12, 1]`
compare in `starter/justfile.jinja` (the generated project's `kmctl_src`),
and the docs and ADR 0044. main has since released v0.12.2 from the root
(the tag's tree has `src/kmctl`, no `packages/`). So a project pinned to
v0.12.2 gets `#subdirectory=packages/kmctl`, and both the starter's
`just kmctl` and the pin hand-off fail: uv says the source "has no
subdirectory `packages/kmctl`" (measured with a starter rendered at
`kmctl_ref=v0.12.2`).

A fifth site follows the same rule: `HOOK_INSTALL` in
`packages/kmctl/src/kmctl/plugin.py` always appends the fragment to
`@v{version('kmctl')}`, and `kmctl plugin patch` writes that hint into
users' `settings.json`, so a kmctl at 0.12.2 would hand out a hint that
cannot install. This ticket moves the cutoff to v0.12.2 and makes it one
constant, `LAST_ROOT_RELEASE` in plugin.py (pin.py imports from plugin.py,
so plugin.py cannot import from pin.py; pin.py re-uses plugin.py's), with
one helper deciding the fragment for a version, which `HOOK_INSTALL` and
the pin hand-off both call. The starter and the docs move to v0.12.2 too.
`scripts/release.py set` also learns the cutoff: it writes the fragment only
for a version after it, and strips it from a line it re-pins at or below it.
Then `set 0.12.2` on this branch writes install lines that build
(`@v0.12.2`, no fragment), the version files match main's v0.12.2 release,
and the "install lines on main name a tag that cannot build" caveat in ADR
0044 goes away. An integration test reads every `v*` tag in the clone and
fails when a tag whose tree has no `packages/kmctl/pyproject.toml` is newer
than the cutoff, or one that has it is not, so the next root release from
main cannot slip past again. The two cutoffs (plugin.py and release.py) are
compared by a test, since release.py is a script that does not import kmctl.

It worked when a starter rendered at v0.12.2 installs kmctl from the root,
one rendered at a later tag from `packages/kmctl`, the pin hand-off does the
same, the hook hint of a kmctl at 0.12.2 has no fragment and one at a later
version has it, and `release.py set 0.12.2` leaves no fragment on any
install line.

## Problems

- P1: Pins, the starter and install lines at v0.12.2 add a subdirectory that release does not have, so installing kmctl at v0.12.2 fails.

## Goals

- G1: Every kmctl release installs from the layout it was built with.

## Outcomes

### O1: The cutoff is v0.12.2 everywhere, release.py set follows it, and a test ties it to the tags
- kind: behaviour
- goal: G1
- fixes: P1
- needs: none
- touches: `packages/kmctl/src/kmctl/pin.py`, `packages/kmctl/src/kmctl/plugin.py`, `starter/justfile.jinja`, `scripts/release.py`, `packages/kmctl/tests/test_pin.py`, `packages/kmctl/tests/test_plugin.py`, `packages/kmctl/tests/test_starter.py`, `packages/kmctl/tests/test_docs.py`, `packages/kmctl/tests/conftest.py`, `tests/scripts/test_release.py`, `tests/scripts/test_release_notes.py`, `apm.yml`, `apm/apm.yml`, `apm/claude/apm.yml`, `apm/antigravity/apm.yml`, `apm/claude/.apm/hooks/hooks.json`, `copier.yml`, `README.md`, `docs/tutorials/get-started-with-kmctl.md`, `docs/how-to/install-kmctl-with-apm.md`, `docs/how-to/install-the-plugin-and-the-ci-action.md`, `.okf/decisions/0044-kmctl-and-kmaudit-are-both-workspace-packages.md`
- checked by: a test_plugin test that the hook hint carries the fragment for a version after v0.12.2 and not for v0.12.2, and that hooks.json still equals the hook command; test_pin and test_starter parametrised over v0.12.1, v0.12.2 (no fragment) and v0.12.3rc1, v0.13.0 (fragment); a test_release test that `set 0.12.2` writes no fragment and `set 0.13.0` writes it once, also when re-pinning a line that had it; a test that pin.py's and release.py's cutoffs agree; an integration test over the clone's `v*` tags; the starter bootstrap integration test still passes
- seen by: operator

## Could invalidate this plan

- none
