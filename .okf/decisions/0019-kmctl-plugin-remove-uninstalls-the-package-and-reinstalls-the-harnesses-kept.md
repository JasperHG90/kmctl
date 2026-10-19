---
type: decision
title: "ADR 0019: kmctl plugin remove uninstalls the package and reinstalls the harnesses kept"
description: "kmctl plugin remove runs apm uninstall on kmctl's entry, removes the hook, MCP entry and plugin folder kmctl wrote, and installs the kept harnesses again at their ref."
tags: [adr, decision, install, remove]
generated:
  by: process:kmctl/0.3.0
  at: 2026-10-17T08:00:22Z
status: deprecated
sources:
  - resource: "src/kmctl/plugin.py"
  - resource: "src/kmctl/doctor.py"
---

# ADR 0019: kmctl plugin remove uninstalls the package and reinstalls the harnesses kept

## Context

The operator asked (2026-10-17) for `kmctl plugin remove`: a way to take
kmctl out of a repository without APM on PATH. An install leaves files from
two owners. APM writes kmctl's and okf's skills, agent, rules and okf's
hooks, and records them in `apm.lock.yaml`
([ADR 0014](0014-apm-is-the-only-install-route.md)). kmctl writes the
SessionStart hook, the `bundle` MCP entry (then named `okf-bundle`) and,
for Antigravity, `.agents/plugins/kmctl/` ([ADR 0015](0015-antigravity-gets-skills-and-rules-from-apm-and-a-kmctl-plugin-folder.md)).

What APM 0.33.0 does, from the ticket's spikes:

- `apm uninstall` on kmctl's entry removes both packages, their deployed
  files and hooks for every target, and the lock; it leaves `{}` in
  `.agents/hooks.json` (spike:plugin-remove/3).
- It takes the entry as `HOST[:PORT]/OWNER/REPO/apm`, the case of the
  entry's own `git:` URL; the lock lowercases a GitHub repo_url, so the name
  is built from the entry (spike:plugin-remove/5).
- Dropping one target from `targets:` and installing again leaves okf's
  Antigravity hook script behind, recorded in the lock as a `legacy`
  target (spike:plugin-remove/2).
- `kmctl plugin install` only adds targets, so `apm.yml` cannot say whether
  a target was there before kmctl.

## Decision

`kmctl plugin remove --harness LIST` uninstalls kmctl's entry with APM, then
removes what kmctl wrote for each harness named: the SessionStart hook and
the `bundle` server for Claude Code (with `claude mcp remove` at user
scope), the plugin folder and an empty `.agents/hooks.json` for
Antigravity. When some installed harnesses are kept, it installs them again
with the normal install, from the removed entry's source at its `ref`, so
their version does not change. If that install fails it exits 1, says the
kept harnesses were uninstalled too, and names the install that puts them
back.

A removed harness leaves `targets:` only when no other dependency is left
in `apm.yml`; otherwise the target stays, with a note, so the repository's
own packages keep it. `kmctl doctor` counts `targets:` only when the lock
lists no kmctl package, so a kept target does not mark a removed harness as
installed. Without `--harness`, remove asks at a terminal, as install does
since the harness question, with the installed harnesses as the default.

Rejected:

- Rewriting `targets:` and running `apm install` for the rest. It leaves
  okf's Antigravity hook script behind (spike:plugin-remove/2).
- Deleting APM's files by hand from the lock's list. APM's own uninstall
  does it and keeps the lock consistent.
- Dropping a removed harness from `targets:` always. It would stop the
  repository's other packages deploying to that harness.

## Consequences

- Removing one of two harnesses reinstalls the other, so it needs the
  network and the source's tag, as an install does.
- After a partial remove, a bare `apm install` without `--target` can
  deploy kmctl to a harness whose target was kept; remove says so.
- `kmctl plugin remove` with nothing installed changes nothing and exits 0.

## Correction, 2026-10-17

Superseded by [ADR 0021](0021-apm-installs-kmctl-s-package-kmctl-plugin-patch-adds-the-rest.md).
