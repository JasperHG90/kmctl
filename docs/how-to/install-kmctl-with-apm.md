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
  needs a GitHub token with access to it. APM reads one from
  `GITHUB_APM_PAT`, `GITHUB_TOKEN` or `GH_TOKEN`, then from `gh auth token`,
  then from your git credential helper.

## Steps

### 1. Install the kmctl CLI

```
uv tool install git+https://github.com/JasperHG90/Knowledge-management@v0.3.0
```

### 2. Add the kmctl package

Add the package to `dependencies.apm` in the repository's `apm.yml`, with
`ref` set to the tag of the CLI, `v` and what `kmctl --version` prints:

```yaml
dependencies:
  apm:
    - git: https://github.com/JasperHG90/Knowledge-management.git
      path: apm
      ref: vX.Y.Z
```

and then, from the repository root, install it for your harnesses and patch:

```
apm install --target claude
kmctl plugin patch
```

Use `--target antigravity` for Antigravity, or
`--target claude,antigravity` for both. APM writes the SessionStart hook
into `.claude/settings.json` and okf's MCP server, `okf-bundle`, into
`.mcp.json`, along with the skills, agent and rules; for Antigravity it
writes the same into `.agents/`. `kmctl plugin patch` reads `apm.lock.yaml`
to see which harnesses APM installed kmctl for, and never runs APM itself.

For Claude Code at user scope, for every repository, put the entry in
`~/.apm/apm.yml` and run `apm install -g --target claude`, then
`kmctl plugin patch --scope user`. Antigravity installs per repository
only.

### 3. Start a new session

Start a new Claude Code session in the repository. Claude Code asks once
whether to use the `okf-bundle` server from `.mcp.json`. The SessionStart
hook prints the kmctl briefing at the start of each session.

For Antigravity, trust the repository root: open it in the IDE and accept
the trust prompt, or run `agy` there and choose "Yes, I trust this folder".
Antigravity loads `.agents/` only from a trusted folder.

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
found`, go back to step 1. `kmctl doctor` checks the hook (`claude.hook`)
and okf's MCP server (`claude.okf-mcp`) along with the rest; when one is
missing, check whether `apm approve --pending` lists kmctl's package.

To upgrade, install the CLI at the new tag with `uv tool install --force`,
set `ref` to the same tag, and run `apm install` and `kmctl plugin patch`
again. To remove the package, run `apm uninstall` on kmctl's entry, then
`kmctl plugin patch --undo`; the steps, with the name `apm uninstall` takes,
are in
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
