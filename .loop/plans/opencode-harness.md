---
type: plan
title: 'Plan: opencode-harness'
description: kmctl's APM package installs for OpenCode with apm install --target opencode, and kmctl plugin patch rewrites the agents into OpenCode's format, adds the rules to opencode.json's instructions and, if OpenCode allows it, the session briefing.
tags:
- plan
generated:
  by: process:loopctl/2.0.0a2.dev1117+g5fdc255a8.d20261014
  at: '2026-10-17T21:44:38+00:00'
slug: opencode-harness
epic: multi-harness
depends_on: []
priority: 2
---

# opencode-harness

<!-- This template was registered in planning. To capture an idea as a stub
instead (intent for later, promoted by the operator), write the plan with
`status: draft` in its front matter before running loopctl ticket register.
A hand-written plan's front matter needs type: plan, title, description and
slug; loopctl ticket register fills in generated. Optional: epic, depends_on,
priority, status, strictness and blocking. -->

Relayed from: none
<!-- When this ticket carries a finding raised while building another ticket,
replace "none" with that ticket's slug and the finding, in one line (ADR 0001). -->

## Intent

The operator asked (2026-10-17): "add opencode as an APM target. Run it
through the loop." and "Also update kmctl-starter". The operator chose to
split the starter into its own ticket, opencode-starter, which depends on
this one and on the release that ships it. Today kmctl's package
serves two harnesses, Claude Code and Antigravity (`HARNESSES` in
`src/kmctl/plugin.py`); `.okf/manifesto.md` lists opencode under "Out of
scope for now". This ticket makes OpenCode the third.

The route is the one ADR 0021
(`.okf/decisions/0021-apm-installs-kmctl-s-package-kmctl-plugin-patch-adds-the-rest.md`)
set: the user lists kmctl's package in apm.yml, runs
`apm install --target opencode`, then `kmctl plugin patch`, which adds only
what APM cannot install yet. `kmctl plugin install`, `update`, `remove`,
`status` and the harness question left the CLI with ADR 0021, so this plan
names `patch`, `patch --undo` and `kmctl doctor` where the antigravity-harness
plan (`.loop/plans/antigravity-harness.md`) named install, remove and status.

What APM 0.33.0 does for OpenCode (apm_cli/integration/targets.py:672, the
opencode profile): root folder `.opencode/`; agents copied verbatim to
`.opencode/agents/`; commands; skills to `.agents/skills/`, the same folder
as Antigravity's. No hooks and no per-file instructions (rules reach
OpenCode only through `apm compile` into AGENTS.md). Its
integration/opencode_frontmatter.py only warns about Claude-style front
matter, and OpenCode's agent loader silently drops an agent whose `tools`
is a string or list or whose colour is a named one outside its theme
(core/src/config/plugin/agent.ts:203, spike:opencode-harness/1).
apm/.apm/agents/kmctl-auditor.md has `tools: Read, Grep, Glob`, and okf's two
agents (bundle-weaver, event-analyzer) are Claude-format too. APM's
adapters/client/opencode.py writes MCP servers into the `mcp` key of
opencode.json at the repository root, and only when `.opencode/` exists.

What OpenCode reads (https://opencode.ai/docs/rules/, sst/opencode at
9d97a5b): no rules folder and no path-scoped rules. It loads AGENTS.md (the
nearest, walking up; CLAUDE.md only when there is no AGENTS.md) and the
`instructions` array of opencode.json: paths, globs or URLs, resolved from
the start folder and every parent up to the git root
(packages/core/src/config/plugin/instruction.ts:97, fs.globUp), reloaded
when a file changes. Shell hooks it has none; it has JS/TS plugins.

Measured on 2026-10-17, from apm/ and the APM source above: harnesses kmctl
serves, 2 of 3 asked for. What a plain `apm install --target opencode` of
kmctl's package gives OpenCode today: skills, all of kmctl's and okf's;
agents, 3 written and 0 that OpenCode can load (1 of kmctl's, 2 of okf's,
all with a Claude `tools:` string); rules, 0 of 4 (the four files in
`apm/claude/.apm/instructions/`); session briefing, 0; okf's MCP server, 1
only when `.opencode/` already exists.

What changes:

- **`kmctl plugin patch`, for OpenCode** (project scope only, like
  Antigravity; `--scope user` leaves OpenCode alone and says so). When the
  lock shows APM installed kmctl's package for OpenCode, patch, in a new
  `new:src/kmctl/opencode.py` that prints nothing (the shape of
  `src/kmctl/antigravity.py`):
  - Rewrites .opencode/agents/kmctl-auditor.md, bundle-weaver.md and
    event-analyzer.md in place into OpenCode's format. A translator like
    `translate_agent` in `src/kmctl/antigravity.py` keeps `description`,
    adds `mode: subagent`, and writes `permission` (not the deprecated
    `tools`) as `"*": deny` first, then `allow` for each mapped tool, since
    the last matching rule wins: Read to read, Grep to grep, Glob to glob,
    Write and Edit to edit (OpenCode's write and patch ask as edit), Bash to
    shell. It drops Claude-only keys (`name`, which OpenCode takes from the
    file name, `color`, `effort`, `model`); any other key would be sent to
    the model provider in the request body (core/src/v1/config/migrate.ts:45),
    spike:opencode-harness/1. The body is copied unchanged. A
    Claude tool with no entry refuses and names the tool, as the
    Antigravity translator does. kmctl's agent comes from the CLI's package
    data (`agents_dir()`), okf's from apm_modules/scaccogatto/okf-skills/agents/
    (`OKF_AGENTS`).
  - Writes kmctl's four rules to .opencode/rules/ (one file per rule in
    `apm/claude/.apm/instructions/`, the `applyTo` front matter dropped,
    since OpenCode loads every rule in every session, and a first-line
    notice naming the source and the new ADR). The rules ship in the wheel
    as package data next to `_agents`, through the force-include table in
    `pyproject.toml`. patch owns only those four files, not the folder.
  - Merges the one entry ".opencode/rules/*.md" into `instructions` in
    opencode.json, keeping every other key (the file is shared with the user
    and with APM's `mcp` key), and creates the file when it is missing. An
    opencode.json that does not parse as JSON refuses, naming the file.
  - Writes the session briefing plugin, .opencode/plugins/kmctl.js in the user's repository, for
    OpenCode's V2 plugin API (spike:opencode-harness/2): a plain default
    export `{ id: "kmctl", setup }` with no imports beyond
    `node:child_process`. `setup` runs `kmctl briefing` once, in
    `ctx.location.directory`, with a 10 s timeout, and registers
    `ctx.session.hook("context", ...)`, which pushes the text as a
    `{type: "text"}` part onto `event.system` before each model request.
    OpenCode catches no rejection from a plugin (plugin/src/promise/adapter.ts:594,620),
    so every step is wrapped: when `kmctl` is missing or fails the plugin
    adds nothing and raises nothing, which keeps invariant I1 (one hook,
    never breaks a session). OpenCode 1.x used a different plugin shape;
    the ADR and docs name the OpenCode version this targets.
  - Running patch again changes nothing. A plain `apm install` (also
    `--frozen` and `--force`) silently writes APM's Claude-format agents back
    over the translated ones, and `apm uninstall` stops halfway ("Retained
    user-edited file") on a translated one (spike:opencode-harness/4). So:
    patch is run after every `apm install`, as ADR 0021 already asks;
    `opencode.agents` in doctor catches a bare `apm install`; and `--undo`
    deletes the three translated agents, the four rules, the instructions
    entry (and opencode.json if patch created it and nothing else is left)
    and the plugin file, after which `apm uninstall` finishes cleanly
    (spike:opencode-harness/4). `--undo` and the docs say to run it before
    `apm uninstall`. `apm audit` reports the three agents as drift; the ADR
    and docs say why.
- **Which harnesses are here.** `_harnesses_of` in `src/kmctl/plugin.py`
  and `FOLDERS` / `_harness_of` / `harnesses_found` in
  `src/kmctl/doctor.py` tell harnesses apart by top folder, and
  `.agents/skills/` is now shared, so an OpenCode-only install would read as
  Antigravity and patch would write `.agents/plugins/kmctl/`. OpenCode is
  marked by `.opencode/` in the lock; Antigravity by `.agents/` paths
  outside `.agents/skills/` (its sub-package's rules and hooks).
  `HARNESSES` gains `opencode`.
- **`kmctl doctor`.** Per harness, `opencode.lock`, `opencode.files` (the
  lock's files under `.opencode/` and the shared skills, less the three
  agents patch rewrites) and `opencode.okf-skills`, as for the others; then
  `opencode.agents` (each agent file is what this kmctl's translation
  writes), `opencode.rules` (the four rule files and the instructions
  entry), `opencode.okf-mcp` (opencode.json's `mcp` holds okf-bundle as the
  package declares it) and `opencode.hook` (the plugin
  file is what this kmctl writes); and `dep.opencode` (opencode on PATH)
  when OpenCode is installed. Each fix names `apm install --target opencode`
  or `kmctl plugin patch`. The epilog in `src/kmctl/__init__.py` lists them.
- **No `apm/opencode/` sub-package.** APM writes neither rules nor hooks for
  OpenCode, so a sub-package would deploy nothing; the shared package in
  `apm/apm.yml` already brings the skills, the agent and okf's server.
- **Tests.** `new:tests/test_opencode.py`, no network: the translator maps
  each known tool, turns the rest off and refuses an unknown one; the
  translated auditor has no write, edit or bash; the merge keeps other
  opencode.json keys and adds the entry once; patch twice changes no file;
  `--undo` leaves no kmctl file; an OpenCode-only lock is not read as
  Antigravity; doctor reports a hand-edited agent and a missing entry; and
  the plugin adds nothing and throws nothing when kmctl is missing or
  fails (run under node with a stub `ctx`).
  An `integration` test checks a translated agent against OpenCode's schema
  (`opencode agent list` or an equivalent offline call) when `opencode` is
  on PATH, and skips otherwise. `tests/test_plugin_patch.py` and
  `tests/test_doctor.py` take the new harness.
- **Knowledge.** `new:.okf/decisions/0023-opencode-gets-the-package-from-apm-and-its-agents-rules-and-briefing-from-kmctl-plugin-patch.md`
  records the route, the tool map, why rules go through `instructions`, the
  briefing outcome, and an ADR 0020-style table of the gaps with "drop it
  when". `.okf/manifesto.md` names OpenCode in Parts and takes it out of
  "Out of scope for now". `docs/reference/commands.md` documents what patch
  and doctor do for OpenCode; `docs/how-to/install-kmctl-with-apm.md` and
  `README.md` give the OpenCode install (apm install --target opencode,
  then kmctl plugin patch), that every rule loads in every session, and
  that okf's server needs `uv`. Any `.okf/architecture/` diagram whose
  Depicts section names the harnesses or patch is updated.
- **kmctl-starter** is out of scope: the operator split it into
  opencode-starter (an OpenCode choice in copier.yml, its README and CI
  matrix, and a `kmctl_ref` default and validator at the first release with
  OpenCode), which depends on this ticket and that release.

Done when: in a scratch repository with the kmctl CLI from this branch,
`apm install --target opencode` of kmctl's package from this branch, then
`kmctl plugin patch`, leaves kmctl's and okf's skills in `.agents/skills/`,
kmctl's four rules in .opencode/rules/, three agents in `.opencode/agents/`
that OpenCode's agent schema accepts, and opencode.json with
".opencode/rules/*.md" in `instructions` and okf-bundle in `mcp`; nothing
under `.agents/plugins/`; a second `kmctl plugin patch`, and
`apm install` then `kmctl plugin patch` again, change no file;
`kmctl doctor` passes but for `dep.opencode` when opencode is not on PATH;
and the gates pass.

## Could invalidate this plan

- Briefing: an OpenCode plugin may have no hook that puts text into a
  session's context, or none that can run a shell command. Holds: a project
  plugin in .opencode/plugins/ with `ctx.session.hook("context", ...)`
  adds a system part before each request and can run `kmctl` through
  `node:child_process`, spike:opencode-harness/2 (source read of 9d97a5b;
  the integration test is the first live run).
- Agents: a translated agent may fail OpenCode's agent schema. Holds:
  `description`, `mode: subagent` and a `permission` mapping, with no
  `name`, load from .opencode/agents/; the tool names and the traps are
  in the translator bullet above, spike:opencode-harness/1.
- In-place rewrite: APM may fail on, or silently undo, agent files patch
  rewrote. It does both: install puts them back, uninstall stops on them.
  The plan changed to re-patch after every install, catch a bare install in
  doctor and delete the agents in `--undo` before `apm uninstall`, which
  then finishes. spike:opencode-harness/4 showed the risk; spike:opencode-harness/7
  showed the changed flow holds: re-patching after a plain or `--frozen`
  install gives the same bytes, and deleting the translated agents lets
  `apm uninstall` finish clean.
- MCP server: APM may not write okf's launcher as an OpenCode server that
  starts, or may drop `instructions`. Holds: a first install writes
  `{"type": "local", "enabled": true, "command": ["sh", "-c", ...]}`
  (the agents step creates `.opencode/` first), keeps other keys on
  reinstall, and the command answers MCP initialize,
  spike:opencode-harness/6. This depends on APM deploying an agent to
  `.opencode/agents/`, which kmctl's package does.
