---
type: plan
title: 'Plan: apm-hands-back'
description: kmctl's APM package delivers its hooks, okf's MCP server and per-harness rules itself, so kmctl stops writing them.
tags:
- plan
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T12:41:49+00:00'
slug: apm-hands-back
epic: null
depends_on: []
priority: null
---

# apm-hands-back

<!-- This template was registered in planning. To capture an idea as a stub
instead (intent for later, promoted by the operator), write the plan with
`status: draft` in its front matter before running loopctl ticket register.
A hand-written plan's front matter needs type: plan, title, description and
slug; loopctl ticket register fills in generated. Optional: epic, depends_on,
priority, status, strictness and blocking. -->

Relayed from: none

## Intent

The operator asked (2026-10-17) to hand back to APM everything APM can do.
A review of apm-cli 0.33.0's source and docs found that APM can deliver
three of the four things kmctl writes itself today
(src/kmctl/plugin.py, src/kmctl/antigravity.py): the SessionStart hook,
okf's MCP server and the Antigravity rules. It cannot write Antigravity
agents (APM issue #2990, accepted, unreleased) and it writes okf's
Antigravity Stop hook with a path agy cannot find.

The package becomes three APM packages in one folder:

- `apm/` (shared): the skills, kmctl-auditor (APM writes agents for Claude
  Code only), the okf-skills dependency, okf's MCP server under
  `dependencies.mcp` as `okf-bundle` with kmctl's `sh` launcher at the
  pinned okf commit, and the two sub-packages below as `./claude` and
  `./antigravity`.
- `apm/claude/` (`targets: [claude]`): the four rules with their normal
  `applyTo`, and the SessionStart hook running `kmctl briefing`.
- `apm/antigravity/` (`targets: [antigravity]`): the same four rules with
  `applyTo` written as escaped commas and `**/` globs, so APM gives agy one
  `globs` string it matches, generated from the Claude copies by a script
  whose output a test checks; the SessionStart hook running
  `kmctl briefing --format antigravity`; and okf's Stop check wrapper from
  ADR 0018, now running from `.agents/`.

`kmctl plugin install` stops writing the hook, the MCP server and the
Antigravity rules and hooks; its plugin folder keeps only `plugin.json` and
the translated agents. It still takes APM's broken okf Stop handler out of
.agents/hooks.json (only that exact command, so kmctl's wrapper stays). For
repositories kmctl installed before, it first removes what kmctl wrote that
APM now writes: a kmctl SessionStart group APM does not record in
`apm-hooks.json`, and an `okf-bundle` entry that differs from the server
the package declares. This holds at both scopes: at user scope the files
are settings.json and .claude.json in the Claude config folder,
and `apm install -g` writes the hook and okf-bundle there too. Each
sub-package keeps an `.apm/` folder, since APM resolves both whatever the
target. doctor checks the same files with the new
fixes. A new decision supersedes ADR 0016, amends ADR 0014, 0015 and 0018,
and lists what APM cannot do yet, each with its upstream issue (or a draft
of one, for the operator to file) and the condition for dropping kmctl's
stopgap, plus one APM gap that needs no stopgap: `apm uninstall -g` leaves
okf-bundle in the user `.claude.json` (the docs give the `claude mcp remove`
line).

It worked when a scratch consumer installed from a local git server with
`kmctl plugin install --harness claude,antigravity` gets every hook, rule
and MCP entry from APM (recorded in its sidecars and lock), kmctl writes
only the agents and the okf Stop fix, doctor passes, `apm uninstall` of the
entry leaves nothing but kmctl's plugin folder, and an install over a
consumer set up by today's kmctl leaves one SessionStart hook.

## Could invalidate this plan

- One consumer entry may not be able to pull per-harness sub-packages, so
  the rules could not be split by harness. It can (spike:apm-hands-back/1):
  `./claude` and `./antigravity` with their own `targets:` gave each
  harness only its own rule and hook, agy's rule as one `**/` glob string,
  okf-bundle in both MCP files, and a clean `apm uninstall`.
- agy may not load a SessionStart hook or an MCP server from the workspace
  files APM writes, rather than from a plugin folder. It does
  (spike:apm-hands-back/2): the hook named `apm` injected the briefing and
  okf-bundle answered `search_concepts`.
- Over an install kmctl wrote, APM may rewrite kmctl's commands, refuse, or
  leave duplicates. It keeps every command byte for byte
  (spike:apm-hands-back/3), but leaves two SessionStart groups and skips an
  existing okf-bundle, which is why install removes kmctl's old entries
  first.
- APM may not deliver the hook and server at user scope, where kmctl
  writes them today. It does (spike:apm-hands-back/5; spike:apm-hands-back/4
  failed on the spike's own invalid sub-package): `apm install -g --target
  claude` wrote the recorded hook and okf-bundle into the Claude config folder,
  with the same migration facts as at project scope; only `apm uninstall
  -g` leaves okf-bundle behind.
