---
type: decision
title: "ADR 0024: OpenCode gets the package from APM and its agents, rules and briefing from kmctl plugin patch"
description: "apm install --target opencode brings the skills and okf's MCP server; kmctl plugin patch rewrites the agents into OpenCode's format and writes the rules, their instructions entry and a briefing plugin."
tags: [adr, decision, install, apm, opencode]
generated:
  by: process:kmctl/0.4.1
  at: 2026-10-18T04:28:18Z
status: stable
sources:
  - resource: "src/kmctl/opencode.py"
  - resource: "src/kmctl/plugin.py"
  - resource: "src/kmctl/doctor.py"
---

# ADR 0024: OpenCode gets the package from APM and its agents, rules and briefing from kmctl plugin patch

## Context

The operator asked (2026-10-17) for OpenCode as a third harness, through APM
like the other two ([ADR 0021](0021-apm-installs-kmctl-s-package-kmctl-plugin-patch-adds-the-rest.md)).
APM 0.33.0 has an `opencode` target. It writes skills to `.agents/skills/`
(the folder Antigravity uses too), copies agents into `.opencode/agents/`
unchanged, and writes MCP servers into the `mcp` key of `opencode.json`. It
writes no rules and no hooks for OpenCode.

OpenCode itself (sst/opencode 9d97a5b, read for spike:opencode-harness/1
and /2):

- It skips, without a word, an agent whose `tools` is a string, which is
  what Claude Code's format and APM's copy give it. It sends any front matter
  key it does not know to the model provider.
- It has no rules folder and no rules scoped to paths. It loads `AGENTS.md`
  and every file the `instructions` list of `opencode.json` names, globbed
  from the start folder up to the git root, in every session.
- It has no shell hooks. A plugin in `.opencode/plugins/` (a default export
  `{id, setup}`) can add text to the system prompt through its `context`
  hook, which runs before each model request.

kmctl supports OpenCode 2.x only (2.0.32, the `@opencode/cli` package), as
the operator decided on 2026-10-18. OpenCode 1.x (1.19.3, the `opencode-ai`
package, released the same day) is still published, but it loads plugins
through a `server` export and calls the shell permission `bash`; kmctl
writes neither.

APM's MCP entry for okf's server is a valid OpenCode local server, and APM
keeps the other keys of `opencode.json` when it writes it
(spike:opencode-harness/6).

## Decision

The user lists kmctl's package in `apm.yml` and runs
`apm install --target opencode`, then `kmctl plugin patch`, as for the other
harnesses. For OpenCode, at project scope only, patch:

- rewrites the three agents APM copied into `.opencode/agents/` (kmctl's
  auditor, okf's bundle-weaver and event-analyzer) into OpenCode's format.
  It keeps `description` and the body, adds `mode: subagent`, and writes a
  `permission` map that denies everything (`"*": deny`) and then allows each
  tool the agent had. OpenCode applies the last rule that matches, so the
  deny comes first. It drops every other key: `name`, `color`, `effort`,
  `model`. The tool map is:

  | Claude Code tool | OpenCode permission |
  |---|---|
  | Read | read |
  | Grep | grep |
  | Glob | glob |
  | Write, Edit | edit (OpenCode's write and patch ask as edit) |
  | Bash | shell |

  A tool with no entry makes patch refuse and name it.
- writes kmctl's four rules to `.opencode/rules/`, without their `applyTo`
  front matter, and adds `.opencode/rules/*.md` to `instructions` in
  `opencode.json`, keeping every other key. OpenCode loads every rule in
  every session.
- writes `.opencode/plugins/kmctl.js`, which starts `kmctl briefing` once,
  without waiting for it, and adds its text to the system prompt through the
  `context` hook. It catches every error, since OpenCode catches none a
  plugin throws, so a missing or failing kmctl adds nothing and breaks
  nothing (invariant I1).

Checked live on 2026-10-18 with OpenCode 2.0.32 and a Gemini model, in a
repository holding what patch writes: `opencode debug agents` lists the
three agents as subagents with the permissions above (the auditor: read,
grep and glob only); with a stand-in `kmctl` on PATH the model quoted the
briefing line from its system prompt, and without the plugin it found none;
with no `kmctl` on PATH the session ran and the rules still reached the
prompt through `instructions`.

`apm install` puts APM's Claude-format agents back over the rewritten ones,
and `apm uninstall` stops halfway on an agent patch rewrote
(spike:opencode-harness/4). So patch runs after every `apm install`; doctor's
`opencode.agents` reports a bare install; and `kmctl plugin patch --undo`
deletes the rewritten agents, the rules, the `instructions` entry and the
plugin, after which `apm uninstall` finishes cleanly
(spike:opencode-harness/7). `apm audit` reports the three agents as drift,
which is expected.

APM's skills in `.agents/skills/` serve Antigravity and OpenCode alike, so a
skill there no longer marks Antigravity as installed. patch and doctor take
`.opencode/` for OpenCode and the rest of `.agents/` (Antigravity's rules
and hooks) for Antigravity.

What APM cannot do yet, and what kmctl does meanwhile:

| Gap | Stopgap | Drop it when |
|---|---|---|
| APM copies agents to OpenCode in Claude Code's format, which OpenCode skips (APM only warns). | patch rewrites them in place. | APM translates agent front matter for OpenCode. |
| APM writes no rules for OpenCode. | patch writes `.opencode/rules/` and the `instructions` entry. | APM deploys instructions for OpenCode. |
| APM writes no hooks for OpenCode. | patch writes the briefing plugin. | APM deploys an OpenCode plugin from a package. |

Rejected:

- An `apm/opencode/` sub-package. APM deploys neither rules nor hooks for
  OpenCode, so it would install nothing.
- `apm compile` into `AGENTS.md` for the rules. `kmctl init` already owns a
  block there, and compiling would put a second writer on the same file.
- Agents in the `agent` key of `opencode.json` instead of rewriting APM's
  files. APM's copies would still be there, skipped by OpenCode, and kmctl
  would share one more key with the user.

## Consequences

- The kmctl block in `AGENTS.md` and the four rules are always in context
  in OpenCode, which costs more of its context than the rules' path scoping
  does in Claude Code.
- OpenCode 1.x users get the rules and the skills but no briefing (1.x
  refuses the plugin, logging that it lacks `server()`), and okf's two
  agents lose their shell there, since 1.x does not know `shell`.
- An agent's `read: allow` comes after OpenCode's default rule that asks
  before reading `.env` files, so these three agents read them without
  asking.
- Removing kmctl from an OpenCode install takes `kmctl plugin patch --undo`
  before `apm uninstall`.
- The manifesto names OpenCode as a harness.
