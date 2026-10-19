---
type: decision
title: "ADR 0018: kmctl runs okf's Stop check for Antigravity"
description: "kmctl's plugin folder runs okf's Stop check from the repository root and in Antigravity's format, and takes APM's broken copy out of .agents/hooks.json."
tags: [adr, decision, install, antigravity, hooks]
generated:
  by: process:kmctl/0.3.0
  at: 2026-10-17T07:02:34Z
status: stable
sources:
  - resource: "src/kmctl/antigravity.py"
  - resource: "src/kmctl/plugin.py"
  - resource: "src/kmctl/doctor.py"
---

# ADR 0018: kmctl runs okf's Stop check for Antigravity

## Context

okf-skills ships a Stop hook, `okf-stop-check.sh`, that keeps an agent from
stopping when tracked files changed and nothing under `.okf/` did. It does
nothing unless the bundle opts in with `upkeep: enforced` in
`.okf/index.md`. [ADR 0015](0015-antigravity-gets-skills-and-rules-from-apm-and-a-kmctl-plugin-folder.md)
left okf's hooks to APM. The first live agy session (agy 1.4.0,
2026-10-17) showed APM's copy never works in Antigravity:

- APM 0.33.0 merges it into `.agents/hooks.json` as
  `bash ".agents/hooks/okf-skills/hooks/okf-stop-check.sh"`, a path from
  the repository root, but agy runs a hook in the folder holding its
  hooks.json. The script is not found, and agy logs a failed hook (exit
  127) at the end of every turn in every repository.
- The script reads `.okf/` and runs git from its working folder, so it
  needs the repository root.
- It prints Claude Code's `{"decision": "block"}`. agy keeps the agent
  going only on `"decision": "continue"`; any other value lets it stop.
- agy's Stop input carries `executionNum`, which counts from 0 within each
  turn and starts again at 0 on the next turn of the same conversation
  (spike:antigravity-okf-stop-hook/1, /3). A plugin Stop handler that
  prints `continue` sends agy back into the loop with its reason
  (spike:antigravity-okf-stop-hook/2).

## Decision

The operator chose (2026-10-17) to relay okf's check in Antigravity rather
than leave it Claude-only, although it makes kmctl write a Stop hook there,
which [ADR 0004](0004-sessionstart-is-the-only-hook.md) and invariant I1 had ruled
out for kmctl's own nudges. The check stays okf's: opt-in per bundle, okf's
script and okf's reason. I1 now says kmctl's own hook is SessionStart and
that it relays this one check in Antigravity.

The plugin folder's `hooks.json` gets a second named hook,
`kmctl-okf-stop`, with one Stop handler. On the first stop of a turn
(`executionNum` 0, as okf's own `stop_hook_active` guard allows one
re-entry in Claude Code) it changes to the repository root, three levels
above the plugin folder, runs okf's script with `{}` on stdin, and prints
okf's reason with `"decision": "continue"` when okf blocks. In every other
case, a missing script or a failure included, it prints `{}` and exits 0,
so it never breaks a turn (ADR 0004).

After APM's install, kmctl takes every handler running `okf-stop-check.sh`
out of `.agents/hooks.json`, dropping a named hook left empty and keeping
the rest. `kmctl doctor` fails `antigravity.apm-hooks` while that file
still runs it, and `antigravity.hook` covers both of kmctl's hooks.

Rejected:

- Leaving APM's handler and only adding kmctl's. agy would still log the
  failed handler at every turn's end.
- Dropping okf's check for Antigravity. A bundle that opts in to
  `upkeep: enforced` would get it in Claude Code only.

## Consequences

- An Antigravity session in a repository with `upkeep: enforced` gets
  okf's reminder once per turn, as Claude Code does.
- The handler depends on okf's script path and its exact
  `"decision":"block"` output; a change to either in okf-skills makes the
  hook print `{}`, which is safe but silent.
- A bare `apm install` puts APM's handler back until the next
  `kmctl plugin install`, and doctor says so.

### Amended, 2026-10-17

[ADR 0020](0020-apm-installs-the-hooks-mcp-server-and-rules-kmctl-patches-the-rest.md):
kmctl's package now ships the SessionStart hooks, okf's MCP server and the
rules for each harness, and APM writes them; kmctl writes only the
Antigravity agents and removes APM's broken okf Stop handler.

## Correction, 2026-10-17

The Consequences say a bare `apm install` puts APM's broken handler back
until the next `kmctl plugin install`. That verb is gone ([ADR 0021](0021-apm-installs-kmctl-s-package-kmctl-plugin-patch-adds-the-rest.md)): the next
`kmctl plugin patch` takes the handler out again (`src/kmctl/plugin.py`),
and `kmctl doctor` still says when it is back.

## Consequence, 2026-10-19

While kmctl takes APM's okf Stop handler out of `.agents/hooks.json`,
`apm audit --ci` reports that file as drift for every Antigravity install
(spike:antigravity-apm-audit/3), and no APM option keeps the handler out at
install (spike:antigravity-apm-audit/4). CI for Antigravity runs
`apm audit --ci --no-drift`, and the drift check is a frozen install plus
`kmctl plugin patch` on a clean checkout that fails when `git status
--porcelain` prints anything: the starter's `just check-install`
(`docs/how-to/install-the-plugin-and-the-ci-action.md`, step 4).
