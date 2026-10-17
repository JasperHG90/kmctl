---
type: decision
title: "ADR 0015: Antigravity gets skills and rules from APM and a kmctl plugin folder"
description: "kmctl plugin install --harness antigravity installs the skills and rules with APM and writes .agents/plugins/kmctl/ itself, holding the translated agents, the SessionStart hook and okf's MCP server."
tags: [adr, decision, install, antigravity]
generated:
  by: process:kmctl/0.3.0
  at: 2026-10-16T21:27:04Z
status: stable
sources:
  - resource: "src/kmctl/antigravity.py"
  - resource: "src/kmctl/plugin.py"
---

# ADR 0015: Antigravity gets skills and rules from APM and a kmctl plugin folder

## Context

[ADR 0016](0016-antigravity-rules-come-from-the-kmctl-plugin-folder.md)
moves the rules into kmctl's plugin folder: APM's copies in `.agents/rules/`
never reach an Antigravity session. [ADR 0018](0018-kmctl-runs-okf-s-stop-check-for-antigravity.md)
has kmctl run okf's Stop check, whose APM copy fails in Antigravity.

[ADR 0014](0014-apm-is-the-only-install-route.md) made APM (`apm-cli`
0.33.0) the one install route and served Claude Code only. The operator asked
(2026-10-16) for kmctl's skills, rules, agent and hook to reach Antigravity
(Google's agent IDE and CLI, `agy` 1.4.0) through the same route, with
`kmctl plugin install` a thin wrapper that takes the harness.

What APM and Antigravity do, from the ticket's spikes and APM's
`apm_cli/integration/targets.py`:

- With `--target antigravity` APM writes skills to `.agents/skills/` and the
  rules to `.agents/rules/`. It writes no agents and no MCP config Antigravity
  reads: Antigravity reads MCP servers only from
  `~/.gemini/config/mcp_config.json` or a plugin's `mcp_config.json`. At user
  scope APM writes no rules and no hooks for Antigravity.
- Antigravity loads a plugin from `plugins/NAME/` under a customization root
  such as the workspace `.agents/`, but only in a trusted workspace
  (`trustedWorkspaces`, matched exactly; spike:antigravity-harness/3). agy
  registered the hook of such a plugin (spike:antigravity-harness/4); whether
  the hook fires and the MCP server starts could not be seen on this account.
- An Antigravity hooks.json maps names to hooks; SessionStart holds a flat
  list of handlers. A hook gets a JSON object on stdin whose `workspacePaths`
  names the workspace, and its stdout must be JSON.
- Antigravity agents name Antigravity tools (`view_file`, `grep_search`,
  `find_by_name`, `list_dir`, `write_to_file`, `replace_file_content`,
  `run_command`) and take `mainAgent`, `subagent`, `model` and
  `commandExecutionPolicy`; Claude Code agents name Claude tools.
- `uv run` of okf's `okf_mcp.py` from its raw GitHub URL at the pinned commit
  starts okf's MCP server, given the `.okf` folder as its argument
  (spike:antigravity-harness/1).

## Decision

`kmctl plugin install --harness antigravity` runs the same APM install as for
Claude Code, `apm install --target antigravity` (both harnesses with
`--harness claude,antigravity`), then writes the folder
`.agents/plugins/kmctl/`, which kmctl alone owns and replaces whole on every
run:

- `plugin.json`, naming the plugin `kmctl`.
- `hooks.json` with one named hook, `kmctl-briefing`, holding one
  SessionStart handler. It runs `kmctl briefing --format antigravity`, which
  prints the briefing as `{"injectSteps": [{"systemMessage": {"systemMessage":
  TEXT}}]}` and reads the repository from `workspacePaths[0]` on stdin,
  falling back to `--path`. When kmctl is missing or fails, the handler prints
  `{}` and exits 0, so ADR 0004's one hook still never blocks.
- `agents/`: kmctl's auditor and okf's `bundle-weaver` and `event-analyzer`
  (read from `apm_modules/scaccogatto/okf-skills/agents/`), translated from
  Claude Code's format at install time. The tool map is: Read to `view_file`,
  Grep to `grep_search`, Glob to `find_by_name` and `list_dir`, Write to
  `write_to_file`, Edit to `replace_file_content`, Bash to `run_command`.
  Each agent gets `mainAgent: false`, `subagent: true`, `model: inherit`, and
  `commandExecutionPolicy: "off"` when it has no Bash; `color`, `effort` and
  a named model are dropped and the body is copied unchanged. A Claude tool
  missing from the map makes the install refuse and name it. The wheel now
  carries the agents folder as well as the skills.
- `mcp_config.json` declaring okf's MCP server as `bundle`, run with `uv run`
  from the pinned raw URL through ADR 0014's `sh` launcher, which walks up to
  the first `.okf/` from the repository above the plugin folder (when
  Antigravity sets `PLUGIN_ROOT`) and then from the working folder.

`kmctl plugin status --harness antigravity` compares every file in the folder
with what this kmctl writes and names each missing, extra or different one
with the fix. Antigravity is installed per repository only; `--scope user`
with it is refused, because APM writes no rules or hooks there.

Rejected:

- `agy plugin install` of okf-skills. It kept `${CLAUDE_PLUGIN_ROOT}`, the
  Claude-shaped hooks.json and Claude-format agents, and
  `agy plugin validate` counted 0 hooks and 0 agents.
- A user-level plugin under `~/.gemini/config/plugins/`. The workspace folder
  loads from a trusted repository (spike:antigravity-harness/3) and keeps the
  install to the repository, as APM's rules are.
- Shipping agents already in Antigravity's format. Two copies of each agent
  would drift; one Claude-format source and a translator keep one.

## Consequences

- Antigravity loads `.agents/` only once the repository folder is trusted;
  the install's last step and the install how-to say so, and `kmctl doctor`
  is to check it.
- okf's MCP server needs `uv` on PATH; when no `.okf/` is found it starts and
  reports no bundle, which costs okf's three read-only tools only.
- `.agents/plugins/kmctl/` is rebuilt from `apm_modules/`, which is
  git-ignored, so a fresh clone needs `kmctl plugin install --harness
  antigravity` before status reports the folder as current.
- Whether the hook fires and the MCP server starts in a live session is still
  unseen; the ticket antigravity-live-check is for checking it on an
  eligible account.
- The manifesto names Antigravity as a harness kmctl installs for.

## Correction, 2026-10-17

`kmctl plugin status --harness antigravity`, named in the Decision and the
Consequences, no longer exists; `kmctl doctor` took over its checks. Its
`antigravity.plugin` check compares the files in `.agents/plugins/kmctl/`
with what this kmctl writes, through `antigravity.plugin_problems`
(`src/kmctl/doctor.py`). The decision stands.
