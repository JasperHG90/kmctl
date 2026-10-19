---
description: "Add kmctl's APM package to apm.yml, what APM leaves to kmctl plugin patch, and moving off an older entry."
---

# Install kmctl with APM

This page adds kmctl's APM package to a repository's `apm.yml`, for a
repository that already manages its agent files with
[APM](https://microsoft.github.io/apm), the Agent Package Manager, or one
that will. The package holds kmctl's skills, its audit agent, its four
knowledge rules, the SessionStart hook that prints the kmctl briefing and
okf's MCP server, `okf-bundle`, and brings the okf skills they use. APM
installs, upgrades and removes it; `kmctl plugin patch` then adds what APM
cannot install yet.

[Install the plugin and the CI action](install-the-plugin-and-the-ci-action.md)
walks through the same install with sample output and the CI action. Keep
in mind:

- **The kmctl CLI.** Most of the skills and the hook run `kmctl` commands, so
  you install the CLI yourself, in step 1, at the same tag as the package.
- **Approval.** APM installs the hooks and MCP server unless your `apm.yml`
  limits which packages may run them (an `executables:` block, or the older
  `allowExecutables:`). If it does, `apm approve --pending` lists kmctl's
  package; approve it with `apm approve`.
- **Antigravity.** APM does not install the agents for Antigravity yet, and
  writes okf's Antigravity Stop hook with a path that fails.
  `kmctl plugin patch` adds the agents and removes that hook.
- **OpenCode.** APM copies the agents in Claude Code's format, which
  OpenCode skips, and writes no rules or hooks for it.
  `kmctl plugin patch` rewrites the agents, adds the rules and a plugin
  that adds the briefing to the system prompt. kmctl supports OpenCode 2.x
  only. OpenCode has no rules scoped to paths, so it
  loads all four rules in every session.

How the APM install below was run: with APM 0.33.0 in a scratch
repository, installing the package from a local git server that held this
repository's files, and with okf-skills from GitHub.
`tests/test_plugin_patch.py` runs the same install, then
`kmctl plugin patch`.

## Before you start

- [uv](https://docs.astral.sh/uv/) and `git` on your PATH.
- APM 0.33.0 or later. Without it on your PATH,
  `uvx --from apm-cli==0.33.0 apm` runs it through uv; write that wherever
  this page says `apm`. To put it on your PATH, run `uv tool install apm-cli`.
- A git repository to install into.
- GitHub access to the kmctl repository. It is private for now, so APM
  needs a GitHub token with access to it: set `GITHUB_APM_PAT`, or log in
  with `gh auth login`, which APM asks after its environment variables.
  [APM's authentication guide](https://microsoft.github.io/apm/consumer/authentication)
  lists every source it reads.

## Steps

### 1. Install the kmctl CLI

```
uv tool install git+https://github.com/JasperHG90/kmctl@v0.10.0
```

One kmctl on your PATH serves every repository. When a repository's
`apm.lock.yaml` pins another kmctl release, the kmctl on PATH runs that
pinned release through `uvx`, at the commit the lock records, so each
repository runs its own kmctl, hooks and skills included. uv keeps each
pinned release after its first run, so later runs are as fast and work
offline. Install a newer CLI when you want its own fixes, never once per
repository.

### 2. Add the kmctl package

Add the package to `dependencies.apm` in the repository's `apm.yml`, with
`ref` set to the tag of the CLI, `v` and what `kmctl --version` prints:

```yaml
dependencies:
  apm:
    - git: https://github.com/JasperHG90/kmctl.git
      path: apm
      ref: vX.Y.Z
```

and then, from the repository root, install it for your harnesses and patch:

```
apm install --target claude
kmctl plugin patch
```

Use `--target antigravity` for Antigravity, `apm install --target opencode`
for OpenCode, or a list such as `--target claude,antigravity,opencode` for
more than one. APM writes the SessionStart hook into `.claude/settings.json`
and okf's MCP server, `okf-bundle`, into `.mcp.json`, along with the skills,
agent and rules. For Antigravity it writes the skills, rules, hooks and
`okf-bundle` into `.agents/`, but not the agents: patch writes those into
`.agents/plugins/kmctl/`. For
OpenCode it writes the skills into `.agents/skills/`, the agents into
`.opencode/agents/` and `okf-bundle` into `opencode.json`; patch then
rewrites the agents, writes the rules to `.opencode/rules/`, adds them to
the `instructions` list in `opencode.json`, and writes the briefing plugin
`.opencode/plugins/kmctl.js`. `apm install` puts APM's agents back, so run
`kmctl plugin patch` after every `apm install`. `kmctl plugin patch` reads
`apm.lock.yaml` to see which harnesses APM installed kmctl for, and never
runs APM itself.

For Claude Code at user scope, for every repository, put the entry in
`~/.apm/apm.yml` and run `apm install -g --target claude`, then
`kmctl plugin patch --scope user`. Antigravity and OpenCode install per
repository only.

### 3. Start a new session

Start a new Claude Code session in the repository. Claude Code asks once
whether to use the `okf-bundle` server from `.mcp.json`. The SessionStart
hook prints the kmctl briefing at the start of each session.

For Antigravity, trust the repository root: open it in the IDE and accept
the trust prompt, or run `agy` there and choose "Yes, I trust this folder".
Antigravity loads `.agents/` only from a trusted folder.

For OpenCode, start a new session in the repository. The plugin adds the
briefing to the system prompt. okf's MCP server runs through `uv`, so `uv`
must be on the PATH OpenCode starts with.

## Check it worked

APM writes kmctl's seven skills to `.claude/skills/` (`architecture-review`,
`audit`, `continue`, `decision-log-review`, `handoff`, `practices-review`,
`write-docs`) next to okf's (`okf`, `validate`, `backfill`, `visualize`),
the agent to `.claude/agents/kmctl-auditor.md`, and the rules to
`.claude/rules/`. In the repository, run:

```
kmctl briefing
```

It prints the same briefing the hook prints. If it says `kmctl: command not
found`, go back to step 1.

When a newer release is out than the one `apm.lock.yaml` pins, the briefing
ends with a line saying so, such as "kmctl v0.8.0 is out; this project pins
v0.7.0", and the agent tells you. kmctl reads the newest release from
`kmctl/latest-release` in your cache folder (`$XDG_CACHE_HOME`, by default
`~/.cache`), which a background `git ls-remote` refreshes once a day, so no
session start waits on the network. Set `KMCTL_NO_UPDATE_CHECK=1` to turn
it off. If the briefing says the pinned kmctl is not installed yet, run
`apm install` and `kmctl plugin patch` again, or the `uvx` command it
names: a session hook never waits for uv to build a release. `kmctl doctor` checks the hook (`claude.hook`)
and okf's MCP server (`claude.okf-mcp`) along with the rest; when one is
missing, check whether `apm approve --pending` lists kmctl's package.

To upgrade a repository, set `ref` to the new tag and run `apm install`
and `kmctl plugin patch` again; the kmctl on PATH then runs the new pinned
release. To remove the package, run `kmctl plugin patch --undo`, then
`apm uninstall` on kmctl's entry. For OpenCode the order matters:
`apm uninstall` stops on the agents patch rewrote, and `--undo` deletes
them first. The steps, with the name `apm uninstall` takes, are in
[Install the plugin and the CI action](install-the-plugin-and-the-ci-action.md#7-to-remove-kmctl).
After `apm uninstall -g`, APM leaves `okf-bundle` in your user
`.claude.json`; remove it with:

```
claude mcp remove okf-bundle --scope user
```

## Older installs

kmctl 0.3.0 and older named the package with a string entry, such as:

```yaml
dependencies:
  apm:
    - JasperHG90/Knowledge-management/apm#v0.3.0
```

That package's SessionStart hook goes only with `apm uninstall`, so
`kmctl plugin patch` refuses while such an entry is there, or while
`apm.lock.yaml` shows kmctl installed in that old layout. The refusal names
the `apm uninstall` to run, the `git:` entry to add in its place and the
`apm install` to run after it; then run `kmctl plugin patch` again. The
version in the old entry does not matter.

A repository installed with `kmctl plugin install`, which kmctl 0.3.0 had,
needs no extra step: after `apm install`, `kmctl plugin patch` removes the
SessionStart hook and the `okf-bundle` server that older kmctl wrote itself,
and the old claude plugin `kmctl@kmctl`. When it removes `okf-bundle`, it
says to run `apm install` again, so APM writes the package's server.
