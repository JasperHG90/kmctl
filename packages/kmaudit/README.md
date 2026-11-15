# kmaudit

kmaudit audits what a folder of markdown docs claims about the repository
it sits in. A coding agent reads each section, lists the claims it makes,
and writes a check for each claim: steps kmaudit reruns with no model
whenever the files the check reads change. People review the claims and
checks on a local page.

kmaudit calls no model itself, except the optional `judge` tool. The agent
you already work with does the reading and writing through kmaudit's MCP
tools; you review the result, and rerun stale checks, on its local page.

kmaudit lives in the kmctl repository as a package of its own. It does not
need kmctl, though the two work well together: kmctl keeps an `.okf/`
knowledge bundle current, and kmaudit checks that bundle against the code.

## Install

```bash
uv tool install 'kmaudit @ git+https://github.com/JasperHG90/kmctl#subdirectory=packages/kmaudit'
```

Add the `tracing` extra (`kmaudit[tracing]`) to trace the `judge` tool's
calls to LangSmith.

## Commands

The CLI starts the MCP server and the review page, and reads a store.
Every command takes `--help`, and those that print take `--json` for
scripts. The full reference, MCP tools included, is
[`docs/commands.md`](docs/commands.md).

| Command | What it does |
|---|---|
| `kmaudit mcp` | kmaudit's verbs as tools of an MCP server over stdio, for any harness that speaks MCP |
| `kmaudit ui` | A local page to review claims and checks, give feedback and rerun stale checks |
| `kmaudit claims list` | The stored claims, per concept and kind or one by one |
| `kmaudit checks list` | Each claim's check status, strength and why |
| `kmaudit namespaces` | Each audited folder, with its counts |
| `kmaudit briefing` | Each namespace's state and the next step, for a session-start hook |

Extracting claims, writing and testing checks, rerunning them, coverage and
the decision model are MCP tools, not commands; the `/extract-claims` and
`/write-checks` skills drive them. A command that once did one of these
(`kmaudit checks run`, say) exits 2 and names its replacement.

Point kmaudit at any folder of markdown docs: `/extract-claims docs`,
`/extract-claims .okf`, or `folder` set to `docs` in an MCP tool call. Each folder is a namespace with its own store
under `.kmaudit/` in the repository, which ignores itself in git, so two
folders never clash; `kmaudit namespaces` lists them. An OKF bundle keeps
its own rules (its `index.md`, `log.md` and `prototypes/` are skipped);
any other folder audits every `.md` file in it.

## MCP server

`kmaudit mcp` serves the verbs as MCP tools over stdio, so any harness that
speaks MCP drives the audit through them, with no shell: `namespaces`, `claims_todo`,
`claims_submit`, `claims_list`, `checks_todo`, `checks_try`,
`checks_submit`, `checks_run`, `checks_list`, `coverage` and `judge`. The
tools are listed in [`docs/commands.md`](docs/commands.md#kmaudit-mcp).

Every tool takes `folder`, the folder to audit. A relative `folder` is read
from the directory the harness starts the server in, which is not always
the repository, so an absolute path is the safe choice. `checks_run` can
take minutes on a large folder, longer than some harnesses wait for a tool
by default; each section below says how to wait longer.

### Claude Code

```bash
claude mcp add kmaudit -- kmaudit mcp
```

Add `--scope project` to write it to `.mcp.json` and share it with the
repository. Claude Code starts the server in the directory you started
`claude` in, so a relative `folder` works from the repository root. To give
`checks_run` longer, set `MCP_TOOL_TIMEOUT` (milliseconds) before starting
Claude Code, as in `MCP_TOOL_TIMEOUT=600000 claude`.

### Codex

Add the server to `~/.codex/config.toml`:

```toml
[mcp_servers.kmaudit]
command = "kmaudit"
args = ["mcp"]
tool_timeout_sec = 600
```

`tool_timeout_sec` gives `checks_run` up to ten minutes; Codex waits 60
seconds by default. Pass an absolute `folder`, since the server may not
start in the repository.

### Antigravity

Open the agent panel's menu, choose Manage MCP Servers, then View raw
config, and add kmaudit to `mcp_config.json`:

```json
{
  "mcpServers": {
    "kmaudit": {"command": "kmaudit", "args": ["mcp"]}
  }
}
```

Antigravity may start the server outside your workspace, so pass an
absolute `folder`. If `checks_run` times out, narrow `folder` to part of
the docs, or press Rerun stale checks on `kmaudit ui`.

### LangGraph

Load the tools with
[`langchain-mcp-adapters`](https://github.com/langchain-ai/langchain-mcp-adapters)
and hand them to the agent:

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

client = MultiServerMCPClient(
    {
        "kmaudit": {
            "command": "kmaudit",
            "args": ["mcp"],
            "transport": "stdio",
            "cwd": "/path/to/repo",
        }
    }
)
tools = await client.get_tools()
agent = create_react_agent(model, tools)  # model: any LangChain chat model
```

`cwd` sets the directory a relative `folder` is read from; without it the
server starts in your Python process's directory. A tool call waits as long
as the MCP client session's read timeout; pass a longer one through the
connection's `session_kwargs` if `checks_run` gives up first.

## A briefing at session start

`kmaudit briefing` prints where the audit stands and what to do next, in a
few lines, without changing anything, and always exits 0. In Claude Code,
add it as a SessionStart hook in `.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {"hooks": [{"type": "command", "command": "kmaudit briefing"}]}
    ]
  }
}
```

## Agents and skills

kmaudit's [APM](https://github.com/microsoft/apm) package, in
`packages/kmaudit/apm`, brings the `/extract-claims` and `/write-checks`
skills and the kmaudit MCP server, from the same release, so you need not
install kmaudit first. For Claude Code it also brings two agents,
`kmaudit-claims-extractor` and `kmaudit-check-writer`, which the skills hand
each batch to; they call the MCP tools and have no shell. Antigravity and
OpenCode get no agents, so there the skills do each batch themselves with
the same tools.

Add the package to your repository's `apm.yml`, with `ref` set to the
kmaudit release you want:

```yaml
dependencies:
  apm:
    - git: https://github.com/JasperHG90/kmctl.git
      path: packages/kmaudit/apm
      ref: kmaudit-vX.Y.Z
```

then install it for your harnesses, for example
`apm install --target claude`. APM writes the server into `.mcp.json` for
Claude Code, `opencode.json` for OpenCode and `.agents/mcp_config.json` for
Antigravity, as `uvx` running `kmaudit mcp` from that tag.

Claude Code asks once for each kmaudit tool the first time the skill or an
agent calls it. APM writes no permission rules, so to skip the prompts,
allow every kmaudit tool in `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": ["mcp__kmaudit__*"]
  }
}
```

In `claude -p` (headless) runs, a project allow rule did not reach a
subagent's MCP calls when we tried it; name the tools with `--allowedTools`
as well, such as
`--allowedTools mcp__kmaudit__claims_todo,mcp__kmaudit__claims_submit`.
