---
type: plan
title: 'Plan: antigravity-harness'
description: kmctl plugin install --harness antigravity installs kmctl's and okf's skills and rules through APM and writes a kmctl-owned Antigravity plugin folder with the auditor agent, the SessionStart briefing hook and okf's MCP server.
tags:
- plan
generated:
  by: process:loopctl/2.1.1.dev72+ge53d4208b.d20261016
  at: '2026-10-16T19:44:52+00:00'
slug: antigravity-harness
epic: multi-harness
depends_on:
- apm-only-install
priority: 2
---

# antigravity-harness

Relayed from: none

## Intent

The operator asked (2026-10-16) that kmctl's skills, rules, agent and hook
reach Antigravity (Google's agent IDE and CLI, `agy` 1.4.0) as well as
Claude Code, through APM, with `kmctl plugin install` a thin wrapper that
takes the harness. Today only Claude Code gets kmctl and okf: the manifesto
lists Antigravity as out of scope (`.okf/manifesto.md`, ADR 0003
`.okf/decisions/0003-claude-code-plugin-first-depends-on-okf.md`).

This ticket builds on apm-only-install, which moves the plugin content into
the APM package under apm/.apm/ (skills, the auditor agent, rules as
instructions), makes `kmctl plugin install --harness claude` run
`uvx --from apm-cli==0.33.0 apm install JasperHG90/Knowledge-management/apm#v<version>`,
and has kmctl write the Claude SessionStart hook itself. Read that plan
before building; where it names a function, option or status shape, use
its name.

What APM does and does not do for Antigravity (APM 0.33.0,
apm_cli/integration/targets.py, antigravity profile): with
`--target antigravity` it writes skills to `.agents/skills/` and rules to
`.agents/rules/` (with `trigger: glob`), and hooks to .agents/hooks.json.
It writes no agents and no MCP config that Antigravity reads (Antigravity
reads MCP only from ~/.gemini/config/mcp_config.json or a plugin's
`mcp_config.json`). Installing okf-skills with `agy plugin install` was
tried and rejected: it kept `${CLAUDE_PLUGIN_ROOT}`, Claude-shaped
hooks.json and Claude-format agents, and `agy plugin validate` counted 0
hooks and 0 agents.

Measured on 2026-10-16: harnesses `kmctl plugin install` serves, 1 (Claude
Code). Agents Antigravity would get from an APM install of kmctl today, 0
of 1 kmctl agent and 0 of 2 okf agents; MCP servers, 0 of 1. A hand-built
plugin folder with the translated auditor and a SessionStart hook passed
`agy plugin validate --strict` with agents 1, hooks 1 and no findings.

What changes:

- **`kmctl plugin install --harness antigravity`.** Runs the same APM
  install as for claude with `--target antigravity`, then writes one folder
  that kmctl alone owns, `.agents/plugins/kmctl/` in the repository
  (Antigravity discovers plugins in `plugins/` under a customization root
  such as `.agents/`). kmctl rewrites the whole folder on every run, so a
  second run changes nothing and an upgrade replaces it. It holds:
  - `plugin.json`: `{"name": "kmctl"}`.
  - `hooks.json` in Antigravity's named-hook shape, one hook:
    `{"kmctl-briefing": {"SessionStart": [{"type": "command", "command": ..., "timeout": 10}]}}`.
    The command runs `kmctl briefing --format antigravity`, which reads
    the repository from the hook's stdin JSON (`workspacePaths[0]`, which
    Antigravity sends to every hook) instead of the working folder, so it
    does not depend on which folder Antigravity runs the hook from, and it
    also works from a user-level plugin. With no usable stdin it falls back
    to `--path` (default: the current folder). Antigravity fails a hook whose stdout
    is not JSON, so when kmctl is missing or fails the command prints `{}`
    and exits 0, which keeps invariant I1 (one hook, never blocks).
  - agents/kmctl-auditor.md, translated at install time from the one
    Claude-format source the package ships. A new translator maps the
    front matter: `tools: Read, Grep, Glob` becomes the YAML list
    `view_file, grep_search, find_by_name, list_dir`; it adds
    `subagent: true`, `mainAgent: false`, `model: inherit`, and
    `commandExecutionPolicy: "off"` when the agent has no Bash; it drops
    Claude-only keys (`color`, `effort`, a named `model`). The body is
    copied unchanged. A Claude tool with no entry in the map makes the
    install refuse and name the tool, so a new tool cannot slip through
    untranslated.
  - agents/bundle-weaver.md and agents/event-analyzer.md: okf's two
    agents, read from where APM put the okf-skills package
    (apm_modules/scaccogatto/okf-skills/agents/) and passed through the
    same translator, which also maps `Write` to `write_to_file`, `Edit` to
    `replace_file_content` and `Bash` to `run_command`. The okf skills that
    dispatch them (backfill) then work in Antigravity.
  - `mcp_config.json` declaring okf's MCP server under the name `bundle`
    as `uv run https://raw.githubusercontent.com/scaccogatto/okf-skills/<sha>/servers/okf_mcp.py`
    (a single-file PEP 723 script with no local imports), where `<sha>` is
    the okf-skills commit `apm/apm.yml` pins. The sha is a constant in the
    code, and a no-network test checks it equals the pin in `apm/apm.yml`,
    so the two cannot drift. The server needs the `.okf` folder itself as
    its first argument when its working folder is not the repository root
    (spike:antigravity-harness/1: with no argument from another folder it
    starts but every tool call fails). Antigravity documents neither the
    working folder nor the environment of a plugin's MCP server, so the
    entry uses the launcher apm-only-install writes for Claude: a short
    POSIX `sh -c` script that walks up to the first folder holding `.okf/`,
    starting from `$PLUGIN_ROOT/../../..` when that variable is set and
    then from the working folder. It does not depend on either being
    right: from the plugin folder or anywhere in the repository it finds
    the same `.okf/`. If neither leads to it, the server starts and reports
    "no OKF bundle", which costs only okf's three read-only MCP tools; the
    agent still reads `.okf/` with its file tools (okf's own decision
    record says the server duplicates them).
- **`kmctl briefing --format antigravity`.** Prints
  `{"injectSteps": [{"systemMessage": {"systemMessage": "<briefing text>"}}]}`,
  the shape Antigravity's SessionStart hook injects into context. It takes
  the repository from `workspacePaths[0]` in the stdin JSON when stdin is
  not a terminal and parses, else from `--path`. The
  briefing text is the same as `kmctl briefing` prints. `--format text`
  stays the default, so the Claude hook does not change; `--json` keeps its
  meaning (the briefing's parts, for scripts).
- **`kmctl plugin status --harness antigravity`.** Compares each file under
  `.agents/plugins/kmctl/` with what this CLI would write and reports each
  missing, extra or different file as a problem that names
  `kmctl plugin install --harness antigravity`, in the status shape
  apm-only-install defines.
- **Tests.** `new:tests/test_antigravity.py`, no network: the translator
  maps each known tool and refuses an unknown one; the translated auditor
  has no write tool and `commandExecutionPolicy: "off"`; hooks.json has one
  SessionStart hook; the hook command prints JSON and exits 0 with kmctl
  missing and with kmctl failing (I1); `kmctl briefing --format antigravity`
  prints JSON whose systemMessage equals the text briefing; the MCP sha
  equals the `apm/apm.yml` pin; install twice leaves the folder the same;
  status reports a hand-edited file. An `integration` test runs
  `agy plugin validate --strict --json .agents/plugins/kmctl` when `agy`
  is on PATH and skips otherwise.
- **Knowledge.** A new ADR (the builder takes the next free number after
  apm-only-install's) records the Antigravity route: APM for skills and
  rules, a kmctl-owned plugin folder for agents, hook and MCP, why
  `agy plugin install` of okf was rejected, and the tool-name map.
  `.okf/manifesto.md` names Antigravity in Parts and takes it out of "Out
  of scope for now"; ADR 0003's "other harnesses follow" gets a pointer to
  the new ADR. `docs/reference/commands.md` documents `--harness` and
  `--format`; the install how-to says how to install for Antigravity, that
  Antigravity loads the repository's `.agents/` only once the folder is
  trusted, and that okf's MCP server needs `uv` on PATH.

Done when: in a scratch repository with the kmctl CLI from this branch,
`kmctl plugin install --harness antigravity` leaves kmctl's and okf's
skills in `.agents/skills/`, the rules in `.agents/rules/`, and
`.agents/plugins/kmctl/` that
`agy plugin validate --strict --json .agents/plugins/kmctl` reports with
agents 3 (1 if okf's agents are cut), hooks 1, mcpServers 1 and no
findings; `echo '{"workspacePaths":["<repo>"]}' | kmctl briefing --format antigravity`
run from another folder prints valid JSON with `injectSteps` briefing on
`<repo>`; a second install changes no file; and the gates
pass.

## Could invalidate this plan

- Discovery: Antigravity might not load a plugin from the workspace
  `.agents/plugins/` folder, which would leave the agents, hook and MCP
  server unused and force a user-level plugin under `~/.gemini/`.
  Settled by spike:antigravity-harness/3: offline, with a scratch HOME,
  `agy agents` listed the agent inside a workspace `.agents/plugins/kmctl/`
  from the repository root and from a subfolder. It loads only when the
  working folder is trusted (`trustedWorkspaces`, matched exactly), so the
  install how-to tells users to trust the folder and `kmctl doctor` checks
  it. spike:antigravity-harness/4 then got as far as agy logging "loaded 1
  named hooks from 1 hooks.json file(s)" for a workspace plugin before the
  account check stopped the session, so the plugin's hook is registered.
  Whether it fires, and whether the plugin's MCP server starts, happens
  after that check and cannot be seen on this account. Neither throws the
  plan away: the briefing reads the repository from the hook's stdin and
  the MCP launcher does not depend on the working folder or `PLUGIN_ROOT`,
  so the only remaining unknown is whether Antigravity runs them at all,
  which its embedded docs say it does. The live check is the stub ticket
  antigravity-live-check, for the operator to run on an eligible account.
- MCP server: `uv run <raw GitHub URL>` might not start okf's server or
  answer an MCP initialize over stdio, which would change how the server
  is shipped (a local copy instead of a URL). Settled by
  spike:antigravity-harness/1: it started, answered initialize and listed
  get_neighbors, read_concept and search_concepts, given the `.okf` path
  as its argument.
