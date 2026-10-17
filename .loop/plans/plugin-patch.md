---
type: plan
title: 'Plan: plugin-patch'
description: kmctl plugin patch, run after apm install, writes only what APM cannot; it replaces kmctl plugin install, update and remove, and the README explains installing per harness.
tags:
- plan
generated:
  by: process:loopctl/2.1.1.dev246+g2cd5b87ba.d20261017
  at: '2026-10-17T12:41:50+00:00'
slug: plugin-patch
epic: null
depends_on:
- apm-hands-back
priority: null
---

# plugin-patch

<!-- This template was registered in planning. To capture an idea as a stub
instead (intent for later, promoted by the operator), write the plan with
`status: draft` in its front matter before running loopctl ticket register.
A hand-written plan's front matter needs type: plan, title, description and
slug; loopctl ticket register fills in generated. Optional: epic, depends_on,
priority, status, strictness and blocking. -->

Relayed from: none

## Intent

After apm-hands-back, APM installs kmctl's package, hooks, rules and okf's
MCP server, and kmctl only adds what APM cannot yet do. The operator asked
(2026-10-17) for that to be a command of its own, `kmctl plugin patch`,
replacing `kmctl plugin install`, `update` and `remove`, with an `--undo`
for what patch wrote; installing, upgrading and removing the package
become APM's (`apm install`, `apm uninstall`).

`kmctl plugin patch [--scope project|user] [--json] [--undo]` never runs
APM and needs neither uv nor APM on PATH. It reads `apm.lock.yaml` to see
which harnesses APM installed kmctl's package for, and refuses, naming the
`apm install` to run, when the lock lists no kmctl package. Then:

- For antigravity: writes `.agents/plugins/kmctl/` (`plugin.json` and the
  agents translated from Claude Code's format, kmctl-auditor from the CLI
  and okf's two from `apm_modules/`), and takes APM's broken okf Stop
  handler out of .agents/hooks.json.
- For claude: removes what an older kmctl wrote that APM now writes (a
  kmctl SessionStart group APM does not record, an `okf-bundle` entry that
  differs from APM's) and the old claude plugin `kmctl@kmctl`, as install
  did, saying to run `apm install` again when it removed something APM
  should now write.
- Running it again changes nothing; it ends with `Next: kmctl doctor`.

`--undo` deletes `.agents/plugins/kmctl/` and nothing else. `install`,
`update`, `remove` and their harness question leave the CLI. doctor's fixes
name `apm install`, the `apm.yml` ref, or `kmctl plugin patch` instead.
`kmctl init`'s next step points at the README's install section.

The README gets the install instructions per harness: the `apm.yml` entry
(`{git: ..., path: apm, ref: vVERSION}` at the CLI's version), the
`apm install --target ...` line for Claude Code, Antigravity or both (APM
through `uvx --from apm-cli==0.33.0 apm` when it is not installed), then
`kmctl plugin patch`, trusting the folder in Antigravity, upgrading
(change the ref, `apm install`, `kmctl plugin patch`) and removing
(`apm uninstall`, `kmctl plugin patch --undo`). The how-tos, the commands
reference and the architecture page follow; a decision records that APM
installs and kmctl patches, superseding ADR 0019 and amending ADR 0014.

It worked when, in a scratch consumer, `apm install` from a local git
server then `kmctl plugin patch` makes doctor pass for claude and
antigravity; `kmctl plugin patch --undo` then `apm uninstall` leaves no
kmctl file; and `kmctl plugin install` no longer exists.

## Could invalidate this plan

- none
