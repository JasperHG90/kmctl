# Install kmctl with APM

This page adds kmctl's APM package to a repository's `apm.yml` by hand, for a
repository that already manages its agent files with
[APM](https://microsoft.github.io/apm), the Agent Package Manager. The
package holds kmctl's skills, its audit agent, its four knowledge rules, the
SessionStart hook that prints the kmctl briefing and okf's MCP server,
`okf-bundle`, and brings the okf skills they use.

`kmctl plugin install --harness claude` does all of this for you;
see [Install the plugin and the CI action](install-the-plugin-and-the-ci-action.md).
With a hand-added entry, keep in mind:

- **The kmctl CLI.** Most of the skills and the hook run `kmctl` commands, so
  you install the CLI yourself, in step 1, at the same tag as the package.
- **`allowExecutables`.** If your `apm.yml` has an `allowExecutables` block,
  allow kmctl's package there; otherwise APM installs no hook or MCP server
  from it.
- **Antigravity.** APM does not install the agents for Antigravity yet, and
  writes okf's Antigravity Stop hook with a path that fails.
  `kmctl plugin install --harness antigravity` adds the agents and removes
  that hook.

How the commands below were run: with APM 0.33.0 in a scratch repository,
installing the package from a local git server that held this repository's
files, and with okf-skills from GitHub. `tests/test_apm_package.py` runs the
same install through `kmctl plugin install`.

## Before you start

- [uv](https://docs.astral.sh/uv/) and `git` on your PATH.
- APM 0.33.0 or later on your PATH, for example from
  `uv tool install apm-cli`.
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

Add the package to the repository's `apm.yml`, at the same tag as the CLI:

```yaml
dependencies:
  apm:
    - JasperHG90/Knowledge-management/apm#v0.3.0
```

and then, from the repository root:

```
apm install --target claude
```

APM writes the SessionStart hook into `.claude/settings.json` and okf's MCP
server, `okf-bundle`, into `.mcp.json`, along with the skills, agent and
rules.

### 3. Optional: hand the entry to kmctl

Skip this step to keep your own entry. To let kmctl manage it instead, run:

```
kmctl plugin install --harness claude
```

This replaces your entry with the one kmctl writes,
`{git: ..., path: apm, ref: v0.3.0}`, after running `apm uninstall` on
yours, so the two never install the package twice.

### 4. Start a new session

Start a new Claude Code session in the repository. Claude Code asks once
whether to use the `okf-bundle` server from `.mcp.json`. The SessionStart
hook prints the kmctl briefing at the start of each session.

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
missing, check `allowExecutables` in `apm.yml`.

To upgrade, install the CLI at the new tag with `uv tool install --force`,
then run `kmctl plugin update`. It asks which harnesses to update, and Enter
takes the ones already installed; pass `--harness` in a script.

To remove the package, run `apm uninstall` on your entry; APM takes out the
hook and okf's MCP server with the rest. After `apm uninstall -g`, APM
leaves `okf-bundle` in your user `.claude.json`; remove it with:

```
claude mcp remove okf-bundle --scope user
```
