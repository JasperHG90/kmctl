## What changed

- kmaudit checks what a folder of markdown docs claims about its repository against the code. An agent reads each section and stores its claims, writes a check for each claim, and kmaudit reruns the checks with no model, so a claim that drifts from the code shows up. (`kmaudit-package`)
- It audits any folder of markdown docs (`.okf/`, `docs/`, or another), each in its own store under `.kmaudit/`, listed by `kmaudit namespaces`. (`kmaudit-namespaces`)
- `kmaudit mcp` starts an MCP server over stdio whose tools do the work (`claims_todo`, `claims_submit`, `checks_todo`, `checks_try`, `checks_submit`, `checks_run`, `judge` and more), so any harness that speaks MCP can drive the audit: Claude Code, Codex, Antigravity or a LangGraph agent. (`kmaudit-mcp`)
- `kmaudit ui` serves a review page: each claim with its check, the code it reads, feedback, a second opinion, and a Rerun stale checks button. (`kmaudit-cli-slim`)
- `kmaudit briefing` prints each namespace's state in a few lines, for a session-start hook. (`kmaudit-briefing`)
- kmaudit's APM package (`path: packages/kmaudit/apm`) installs the extract-claims and write-checks skills for every harness, two Claude Code agents that use only the MCP tools, and the kmaudit MCP server at this release. (`kmaudit-skills-mcp`)
- The CLI stays small: `mcp`, `ui`, `namespaces`, `briefing`, `claims list` and `checks list`. (`kmaudit-cli-slim`)

## Other changes

None.

## Install

```sh
uv tool install 'kmaudit @ git+https://github.com/JasperHG90/kmctl@kmaudit-v0.1.0#subdirectory=packages/kmaudit'
```

For the skills, agents and MCP server, add kmaudit's APM package to `apm.yml`:

```yaml
- git: https://github.com/JasperHG90/kmctl.git
  path: packages/kmaudit/apm
  ref: kmaudit-v0.1.0
```

In Claude Code, allow `mcp__kmaudit__*` so the agents can call the tools; kmaudit's README says how.

First release.
